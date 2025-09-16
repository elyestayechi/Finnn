pipeline {
    agent any
    environment {
        DOCKER_HOST = 'unix:///var/run/docker.sock'
        COMPOSE_PROJECT_NAME = "finn-${BUILD_ID}"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
        LOCAL_DATA_PATH = "/Users/asmatayechi/Desktop/Finn"
        PDF_LOANS_DIR = "PDF Loans"
        MONITORING_DIR = "monitoring"
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

                # Verify monitoring directory structure exists
                echo "=== Checking monitoring structure ==="
                if [ -d "${MONITORING_DIR}" ]; then
                    echo "✅ Monitoring directory exists"
                    find "${MONITORING_DIR}" -type f | head -10
                else
                    echo "❌ Monitoring directory not found - creating basic structure"
                    mkdir -p "${MONITORING_DIR}/prometheus"
                    mkdir -p "${MONITORING_DIR}/alertmanager" 
                    mkdir -p "${MONITORING_DIR}/grafana/provisioning/datasources"
                    mkdir -p "${MONITORING_DIR}/grafana/provisioning/dashboards"
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

        stage('Deploy Full Stack') {
            steps {
                sh '''
                echo "=== Deploying complete application + monitoring stack ==="
                
                # Create comprehensive docker-compose file
                cat > docker-compose.full.yml << EOF
services:
  # Application Services
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11435:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434"]
      interval: 30s
      timeout: 30s
      retries: 10
      start_period: 120s

  backend:
    image: finn-backend:${BUILD_ID}
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - OLLAMA_HOST=http://ollama:11434
      - PROMETHEUS_MULTIPROC_DIR=/tmp
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

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    depends_on:
      - backend

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/config.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped
    depends_on:
      - prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning/datasources:/etc/grafana/provisioning/datasources
      - ./monitoring/grafana/provisioning/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_PATHS_PROVISIONING=/etc/grafana/provisioning
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  ollama_data:
  prometheus_data:
  grafana_data:
EOF

                docker compose -p ${COMPOSE_PROJECT_NAME} -f docker-compose.full.yml up -d
                echo "✅ Full stack deployed (application + monitoring)"
                '''
            }
        }

        stage('Health Check & Verification') {
            steps {
                sh '''
                echo "=== Health Check ==="
                sleep 30  # Give services more time to start
                
                # Check application health
                echo "=== Application Services ==="
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

                # Check monitoring services
                echo "=== Monitoring Services ==="
                if curl -f http://localhost:9090/-/healthy; then
                    echo "✅ Prometheus is healthy"
                else
                    echo "⚠️ Prometheus health check failed"
                fi

                if curl -f http://localhost:3001/api/health; then
                    echo "✅ Grafana is healthy"
                else
                    echo "⚠️ Grafana health check failed"
                fi

                # Check if monitoring targets are being scraped
                echo "=== Prometheus Targets ==="
                curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[].labels.job' | grep -E "(backend|prometheus)" || echo "Could not fetch targets"
                '''
            }
        }

        stage('Configure Monitoring') {
            steps {
                sh '''
                echo "=== Finalizing monitoring setup ==="
                
                # Wait for Grafana to be fully ready
                sleep 15
                
                # Check if datasource was provisioned correctly
                echo "=== Checking Grafana datasource ==="
                curl -u admin:admin http://localhost:3001/api/datasources 2>/dev/null | jq '.[].name' || echo "Could not fetch datasources"
                
                # Check if dashboards were provisioned
                echo "=== Checking Grafana dashboards ==="
                curl -u admin:admin http://localhost:3001/api/search 2>/dev/null | jq '.[].title' || echo "Could not fetch dashboards"
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
            echo "🎉 FULL STACK DEPLOYMENT SUCCESSFUL! 🎉"
            echo ""
            echo "=== APPLICATION SERVICES ==="
            echo "Frontend:     http://localhost:3000"
            echo "Backend API:  http://localhost:8000"
            echo "API Docs:     http://localhost:8000/docs"
            echo "Ollama:       http://localhost:11435"
            echo ""
            echo "=== MONITORING SERVICES ==="
            echo "Grafana:      http://localhost:3001 (admin/admin)"
            echo "Prometheus:   http://localhost:9090"
            echo "Alertmanager: http://localhost:9093"
            echo ""
            echo "=== NEXT STEPS ==="
            echo "1. Open Grafana and explore the pre-built dashboards"
            echo "2. Check that Prometheus is scraping backend metrics"
            echo "3. Verify your data is loaded by checking the API endpoints"
            echo ""
            echo "Data migration has been completed automatically!"
            '''
        }
        failure {
            sh '''
            echo "=== Cleaning up due to failure ==="
            docker compose -p ${COMPOSE_PROJECT_NAME} down 2>/dev/null || true
            '''
        }
    }
}