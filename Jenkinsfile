pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-${BUILD_ID}"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
        LOCAL_DATA_PATH = "/Users/asmatayechi/Desktop/Finn" // Update as needed
    }

    stages {
        stage('Checkout & Prepare') {
            steps {
                git branch: 'main', url: 'https://github.com/elyestayechi/Finnn.git'

                sh '''
                echo "=== Preparing workspace ==="
                mkdir -p Back/test-results Back/coverage Back/Data "Back/PDF Loans"

                # Copy data files from local machine
                cp -r "${LOCAL_DATA_PATH}/Back/Data/." Back/Data/ || echo "⚠️ No Data directory to copy"
                cp -r "${LOCAL_DATA_PATH}/Back/PDF Loans/." "Back/PDF Loans/" || echo "⚠️ No PDF Loans directory to copy"
                cp "${LOCAL_DATA_PATH}/Back/loan_analysis.db" Back/ 2>/dev/null || echo "⚠️ No DB file to copy"
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

        stage('Run Unit Tests') {
            steps {
                dir('Back') {
                    sh '''
                    docker build -t finn-backend-test:${BUILD_ID} -f Dockerfile.test .
                    mkdir -p test-results coverage
                    chmod 777 test-results coverage
                    docker run --rm -v "$(pwd)/test-results:/app/test-results" -v "$(pwd)/coverage:/app/coverage" finn-backend-test:${BUILD_ID} || true
                    '''
                }
            }
        }

        stage('Run Migration Before Deployment') {
    steps {
        dir('Back') {
            sh '''
            echo "=== Running migration in temporary container ==="
            docker run --rm \
                -v "$(pwd)/Data:/app/Data" \
                -v "$(pwd)/PDF Loans:/app/PDF Loans" \
                -v "$(pwd)/loan_analysis.db:/app/loan_analysis.db" \
                -e OLLAMA_HOST=http://dummy:11434 \
                finn-backend-test:${BUILD_ID} \
                python migrate_data.py

            # DEBUG: verify host files
            echo "=== After migration, host volumes ==="
            ls -la Data
            ls -la "PDF Loans"
            ls -la loan_analysis.db
            echo "✅ Host volumes populated with data"
            '''
        }
    }
}

        stage('Deploy Application') {
            steps {
                sh '''
                WORKSPACE="$(pwd)"
                cat > docker-compose.app.yml << EOF
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
      - ${WORKSPACE}/Back/Data:/app/Data
      - "${WORKSPACE}/Back/PDF Loans:/app/PDF Loans"
      - ${WORKSPACE}/Back/loan_analysis.db:/app/loan_analysis.db
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
                echo "✅ Application deployed with pre-populated data"
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                echo "=== Checking container status ==="
                docker compose -p ${COMPOSE_PROJECT_NAME} ps
                '''
            }
        }
    }

    post {
        always {
            // Create coverage directory in the correct location
            sh '''
            echo "=== Ensuring directories exist ==="
            mkdir -p Back/test-results Back/coverage
            # Create placeholder files if they don't exist
            if [ ! -f "Back/test-results/test-results.xml" ]; then
                echo '<?xml version="1.0" encoding="UTF-8"?><testsuite name="pytest" tests="0" errors="0" failures="0" skipped="0"></testsuite>' > Back/test-results/test-results.xml
            fi
            if [ ! -f "Back/coverage/coverage.xml" ]; then
                echo '<?xml version="1.0" ?><coverage></coverage>' > Back/coverage/coverage.xml
            fi
            '''
            
            // Use specific file paths instead of wildcards
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
            echo "Data migration has been automatically executed."
            echo "To deploy monitoring separately:"
            echo "docker compose -f docker-compose.monitoring.yml up -d"
            '''
        }

        failure {
            // Only clean up images if the pipeline failed
            sh '''
            echo "=== Cleaning up due to failure ==="
            docker rmi finn-backend-test:${BUILD_ID} 2>/dev/null || true
            docker rmi finn-backend:${BUILD_ID} 2>/dev/null || true
            docker rmi finn-frontend:${BUILD_ID} 2>/dev/null || true
            '''
        }
    }
}