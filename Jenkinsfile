pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-${BUILD_ID}"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
    }
    
    stages {
        stage('Checkout & Prepare') {
            steps {
                git branch: 'main', url: 'https://github.com/elyestayechi/Finnn.git'
                
                sh '''
                echo "=== Preparing workspace ==="
                mkdir -p Back/test-results Back/coverage
                chmod 755 Back/test-results Back/coverage
                echo "Workspace prepared"
                '''
            }
        }
        
        stage('Build Images') {
            steps {
                parallel(
                    'Build Backend': {
                        dir('Back') {
                            sh '''
                            echo "Building backend image..."
                            docker build -t finn-backend:${BUILD_ID} -f Dockerfile .
                            '''
                        }
                    },
                    'Build Frontend': {
                        dir('Front') {
                            sh '''
                            echo "Building frontend image..."
                            docker build -t finn-frontend:${BUILD_ID} -f Dockerfile .
                            '''
                        }
                    }
                )
            }
        }
        
        stage('Run Tests') {
            steps {
                dir('Back') {
                    sh '''
                    echo "=== Running unit tests ==="
                    docker build -t finn-backend-test:${BUILD_ID} -f Dockerfile.test .
                    
                    docker run --rm \
                        -v "$(pwd)/test-results:/app/test-results" \
                        -v "$(pwd)/coverage:/app/coverage" \
                        -e OLLAMA_HOST=http://dummy:11434 \
                        finn-backend-test:${BUILD_ID} || true
                    '''
                }
            }
        }
        
        stage('Clean Previous Deployment') {
            steps {
                sh '''
                echo "=== Force cleaning previous deployment ==="
                
                # Remove any existing containers using our ports
                for port in 8000 3000 11435 9090 9093 3001; do
                    echo "Freeing port $port..."
                    docker ps -q --filter "publish=$port" | xargs -r docker rm -f 2>/dev/null || true
                done
                
                # Clean up any project containers
                docker compose -p ${COMPOSE_PROJECT_NAME} down -v --remove-orphans 2>/dev/null || true
                
                sleep 2
                echo "Cleanup completed"
                '''
            }
        }
        
        stage('Deploy Application Only') {
            steps {
                sh '''
                echo "=== Deploying application services only ==="
                
                # Create a custom compose file without Jenkins
                cat > docker-compose.app.yml << 'EOF'
version: '3.8'
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11435:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    restart: unless-stopped

  backend:
    image: finn-backend:${BUILD_ID}
    ports:
      - "8000:8000"
    volumes:
      - ./Back/Data:/app/Data
      - ./Back/PDF Loans:/app/PDF Loans
      - ./Back/loans_vector.db:/app/loans_vector.db
      - ./Back/loan_analysis.db:/app/loan_analysis.db
    environment:
      - PYTHONPATH=/app
      - OLLAMA_HOST=http://ollama:11434
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 30s
      retries: 5
      start_period: 60s

  frontend:
    image: finn-frontend:${BUILD_ID}
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_BASE_URL=http://backend:8000
    restart: unless-stopped

volumes:
  ollama_data:
EOF
                
                # Deploy only application services
                docker compose -p ${COMPOSE_PROJECT_NAME} -f docker-compose.app.yml up -d
                
                echo "=== Waiting for services to start ==="
                sleep 30
                '''
            }
        }
        
        stage('Health Check') {
    steps {
        script {
            // Get the host IP address
            def hostIp = sh(script: "ip route | grep default | awk '{print \\$3}'", returnStdout: true).trim()
            
            // Backend health check
            def backendHealthy = false
            for (int i = 1; i <= 10; i++) {
                try {
                    sh "curl -f http://${hostIp}:8000/health"  // Use host IP instead of localhost
                    echo "✅ Backend is healthy"
                    backendHealthy = true
                    break
                } catch (Exception e) {
                    echo "⚠️ Backend health check attempt ${i}/10 failed, retrying..."
                    if (i == 10) {
                        error "❌ Backend health check failed after 10 attempts"
                    }
                    sleep(10)
                }
            }
            
            // Frontend health check
            def frontendHealthy = false
            for (int i = 1; i <= 10; i++) {
                try {
                    sh "curl -f http://${hostIp}:3000"  // Use host IP instead of localhost
                    echo "✅ Frontend is accessible"
                    frontendHealthy = true
                    break
                } catch (Exception e) {
                    echo "⚠️ Frontend check attempt ${i}/10 failed, retrying..."
                    if (i == 10) {
                        error "❌ Frontend check failed after 10 attempts"
                    }
                    sleep(10)
                }
            }
        }
    }
}
    }
    
    post {
        always {
            // Fix JUnit path - look in the correct location
            junit 'Back/test-results/*.xml'
            archiveArtifacts artifacts: 'Back/coverage/*.xml', fingerprint: true
            
            // Clean up
            sh '''
            echo "=== Cleaning up ==="
            docker compose -p ${COMPOSE_PROJECT_NAME} down -v 2>/dev/null || true
            '''
        }
        
        success {
            sh '''
            echo "🎉 APPLICATION DEPLOYMENT SUCCESSFUL! 🎉"
            echo ""
            echo "Access your services at:"
            echo "Frontend: http://localhost:3000"
            echo "Backend: http://localhost:8000"
            echo "Ollama: http://localhost:11435"
            echo ""
            echo "To deploy monitoring separately:"
            echo "docker compose -f docker-compose.monitoring.yml up -d"
            '''
        }
        
        cleanup {
            sh '''
            # Clean up images
            docker rmi finn-backend-test:${BUILD_ID} 2>/dev/null || true
            docker rmi finn-backend:${BUILD_ID} 2>/dev/null || true
            docker rmi finn-frontend:${BUILD_ID} 2>/dev/null || true
            '''
        }
    }
}