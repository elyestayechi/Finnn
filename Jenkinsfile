pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-${BUILD_ID}"
    }
    
    stages {
        stage('Checkout & Prepare') {
            steps {
                git branch: 'main', url: 'https://github.com/elyestayechi/Finn.git'
                
                sh '''
                echo "=== Preparing workspace ==="
                # Create test directories
                mkdir -p Back/test-results Back/coverage
                chmod 777 Back/test-results Back/coverage
                '''
            }
        }
        
        stage('Build Images') {
            steps {
                parallel(
                    'Build Backend': {
                        dir('Back') {
                            sh 'docker build -t finn-backend:${BUILD_ID} -f Dockerfile .'
                        }
                    },
                    'Build Frontend': {
                        dir('Front') {
                            sh 'docker build -t finn-frontend:${BUILD_ID} -f Dockerfile .'
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
                        finn-backend-test:${BUILD_ID}
                    '''
                }
            }
        }
        
        stage('Deploy Application') {
            steps {
                sh '''
                echo "=== Cleaning up previous deployment ==="
                # Clean up any existing containers with our project name
                docker compose -p ${COMPOSE_PROJECT_NAME} down -v --remove-orphans 2>/dev/null || true
                
                # Free up ports
                for port in 8000 3000; do
                    docker ps -q --filter "publish=$port" | xargs -r docker rm -f 2>/dev/null || true
                done
                
                sleep 2
                
                echo "=== Deploying application stack ==="
                # Create a simplified docker-compose for just app services
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
                
                docker compose -p ${COMPOSE_PROJECT_NAME} -f docker-compose.app.yml up -d
                
                echo "=== Waiting for services to start ==="
                sleep 30
                '''
            }
        }
        
        stage('Health Check') {
            steps {
                sh '''
                echo "=== Health Check ==="
                
                # Check backend with retries
                for i in {1..5}; do
                    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
                        echo "✅ Backend is healthy"
                        break
                    else
                        echo "⚠️ Backend health check attempt $i/5 failed, retrying..."
                        if [ $i -eq 5 ]; then
                            echo "❌ Backend health check failed after 5 attempts"
                            docker compose -p ${COMPOSE_PROJECT_NAME} logs backend
                            exit 1
                        fi
                        sleep 10
                    fi
                done
                
                # Check frontend with retries
                for i in {1..5}; do
                    if curl -f http://localhost:3000 >/dev/null 2>&1; then
                        echo "✅ Frontend is accessible"
                        break
                    else
                        echo "⚠️ Frontend check attempt $i/5 failed, retrying..."
                        if [ $i -eq 5 ]; then
                            echo "❌ Frontend check failed after 5 attempts"
                            docker compose -p ${COMPOSE_PROJECT_NAME} logs frontend
                            exit 1
                        fi
                        sleep 10
                    fi
                done
                
                echo "✅ All application services are running"
                '''
            }
        }
    }
    
    post {
        always {
            junit 'Back/test-results/test-results.xml'
            archiveArtifacts artifacts: 'Back/coverage/coverage.xml', fingerprint: true
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
            echo "To deploy monitoring (optional):"
            echo "docker compose -f docker-compose.monitoring.yml up -d"
            echo ""
            echo "Monitoring services will be available at:"
            echo "Prometheus: http://localhost:9090"
            echo "Grafana: http://localhost:3001"
            echo "Alertmanager: http://localhost:9093"
            '''
        }
        
        cleanup {
            sh '''
            # Clean up test images to save space
            docker rmi finn-backend-test:${BUILD_ID} 2>/dev/null || true
            '''
        }
    }
}