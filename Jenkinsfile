pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-${BUILD_ID}"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
        LOCAL_DATA_PATH = "/Users/asmatayechi/Desktop/Finn"
        PDF_LOANS_DIR = "PDF Loans"
    }

    stages {
        stage('Checkout & Prepare') {
            steps {
                git branch: 'main', url: 'https://github.com/elyestayechi/Finnn.git'

                sh '''
                echo "=== Preparing workspace ==="
                mkdir -p Back/test-results Back/coverage

                # Copy data files into the Back directory structure
                echo "=== Copying data files ==="
                
                # Copy PDF files
                if [ -d "${LOCAL_DATA_PATH}/Back/${PDF_LOANS_DIR}" ]; then
                    cp -r "${LOCAL_DATA_PATH}/Back/${PDF_LOANS_DIR}/" "Back/${PDF_LOANS_DIR}/"
                    echo "✅ PDF Loans directory copied"
                    echo "PDF files count: $(find \"Back/${PDF_LOANS_DIR}/\" -name \"*.pdf\" | wc -l)"
                else
                    echo "⚠️ No PDF Loans directory found"
                fi

                # Copy Data directory
                if [ -d "${LOCAL_DATA_PATH}/Back/Data" ]; then
                    cp -r "${LOCAL_DATA_PATH}/Back/Data/" "Back/Data/"
                    echo "✅ Data directory copied"
                else
                    echo "⚠️ No Data directory found"
                fi

                # Copy database file if it exists
                if [ -f "${LOCAL_DATA_PATH}/Back/loan_analysis.db" ]; then
                    cp "${LOCAL_DATA_PATH}/Back/loan_analysis.db" "Back/"
                    echo "✅ Database file copied"
                else
                    echo "⚠️ No database file found - will be created during migration"
                fi
                '''
            }
        }

        stage('Build Backend with Data') {
            steps {
                dir('Back') {
                    sh '''
                    echo "=== Building backend image with embedded data ==="
                    
                    # Build the image (data will be copied into the image during build)
                    docker build -t finn-backend:${BUILD_ID} -f Dockerfile .
                    
                    # Run migration INSIDE the built image
                    echo "=== Running data migration in the built image ==="
                    docker run --rm \
                        -e OLLAMA_HOST=http://dummy:11434 \
                        finn-backend:${BUILD_ID} \
                        python migrate_data.py
                    
                    echo "✅ Data migration completed inside image"
                    '''
                }
            }
        }

        stage('Build Frontend') {
            steps {
                dir('Front') {
                    sh 'docker build -t finn-frontend:${BUILD_ID} -f Dockerfile .'
                }
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                echo "=== Deploying application ==="
                
                # Create simple docker-compose file
                cat > docker-compose.app.yml << EOF
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
    environment:
      - PYTHONPATH=/app
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
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
      - VITE_API_BASE_URL=http://localhost:8000
    restart: unless-stopped

volumes:
  ollama_data:
EOF

                docker compose -p ${COMPOSE_PROJECT_NAME} -f docker-compose.app.yml up -d
                echo "✅ Application deployed"
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                echo "=== Health Check ==="
                sleep 20
                
                # Check backend health
                if curl -f http://localhost:8000/health; then
                    echo "✅ Backend is healthy"
                    
                    # Test data endpoints to verify migration worked
                    echo "=== Testing data endpoints ==="
                    echo "PDF reports count:"
                    curl -s http://localhost:8000/api/pdfs | jq '. | length' || echo "N/A"
                    echo "Loans count:"
                    curl -s http://localhost:8000/api/loans | jq '. | length' || echo "N/A"
                else
                    echo "❌ Backend health check failed"
                fi
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
            echo "-- DEPLOYMENT SUCCESSFUL! --"
            echo ""
            echo "Access your services at:"
            echo "Frontend: http://localhost:3000"
            echo "Backend: http://localhost:8000"
            echo "Ollama: http://localhost:11435"
            '''
        }
        failure {
            sh '''
            echo "=== Cleaning up ==="
            docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
            '''
        }
    }
}