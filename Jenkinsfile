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

                # Verify monitoring directory structure exists and has required files
                echo "=== Checking monitoring structure ==="
                if [ -d "${MONITORING_DIR}" ]; then
                    echo "✅ Monitoring directory exists"
                    
                    # Check for required files and create defaults if missing
                    if [ ! -f "${MONITORING_DIR}/prometheus/prometheus.yml" ]; then
                        echo "⚠️ prometheus.yml not found - creating default"
                        mkdir -p "${MONITORING_DIR}/prometheus"
                        cat > "${MONITORING_DIR}/prometheus/prometheus.yml" << 'PROMETHEUS_CONFIG'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s

  - job_name: 'backend'
    metrics_path: /metrics
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 10s
    scrape_timeout: 5s
PROMETHEUS_CONFIG
                    fi

                    if [ ! -f "${MONITORING_DIR}/prometheus/alerts.yml" ]; then
                        echo "⚠️ alerts.yml not found - creating default"
                        cat > "${MONITORING_DIR}/prometheus/alerts.yml" << 'ALERTS_CONFIG'
groups:
  - name: finn-alerts
    rules:
      - alert: BackendDown
        expr: up{job="backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend service is down"
          description: "The Finn backend service has been down for more than 1 minute"
ALERTS_CONFIG
                    fi

                    if [ ! -f "${MONITORING_DIR}/alertmanager/config.yml" ]; then
                        echo "⚠️ alertmanager config.yml not found - creating default"
                        mkdir -p "${MONITORING_DIR}/alertmanager"
                        cat > "${MONITORING_DIR}/alertmanager/config.yml" << 'ALERTMANAGER_CONFIG'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default-receiver'

receivers:
  - name: 'default-receiver'
ALERTMANAGER_CONFIG
                    fi

                    # Create Grafana provisioning directories if they don't exist
                    mkdir -p "${MONITORING_DIR}/grafana/provisioning/datasources"
                    mkdir -p "${MONITORING_DIR}/grafana/provisioning/dashboards"

                    if [ ! -f "${MONITORING_DIR}/grafana/provisioning/datasources/datasource.yml" ]; then
                        echo "⚠️ Grafana datasource.yml not found - creating default"
                        cat > "${MONITORING_DIR}/grafana/provisioning/datasources/datasource.yml" << 'GRAFANA_DATASOURCE'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    version: 1
    editable: false
GRAFANA_DATASOURCE
                    fi

                    if [ ! -f "${MONITORING_DIR}/grafana/provisioning/dashboards/dashboards.yml" ]; then
                        echo "⚠️ Grafana dashboards.yml not found - creating default"
                        cat > "${MONITORING_DIR}/grafana/provisioning/dashboards/dashboards.yml" << 'GRAFANA_DASHBOARDS'
apiVersion: 1

providers:
  - name: 'Finn Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
GRAFANA_DASHBOARDS
                    fi

                    echo "=== Monitoring files ==="
                    find "${MONITORING_DIR}" -type f
                else
                    echo "❌ Monitoring directory not found - creating basic structure with default configs"
                    mkdir -p "${MONITORING_DIR}/prometheus"
                    mkdir -p "${MONITORING_DIR}/alertmanager" 
                    mkdir -p "${MONITORING_DIR}/grafana/provisioning/datasources"
                    mkdir -p "${MONITORING_DIR}/grafana/provisioning/dashboards"
                    
                    # Create default config files
                    cat > "${MONITORING_DIR}/prometheus/prometheus.yml" << 'PROMETHEUS_CONFIG'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s

  - job_name: 'backend'
    metrics_path: /metrics
    static_configs:
      - targets: ['backend:8000']
    scrape_interval: 10s
    scrape_timeout: 5s
PROMETHEUS_CONFIG

                    cat > "${MONITORING_DIR}/prometheus/alerts.yml" << 'ALERTS_CONFIG'
groups:
  - name: finn-alerts
    rules:
      - alert: BackendDown
        expr: up{job="backend"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend service is down"
          description: "The Finn backend service has been down for more than 1 minute"
ALERTS_CONFIG

                    cat > "${MONITORING_DIR}/alertmanager/config.yml" << 'ALERTMANAGER_CONFIG'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default-receiver'

receivers:
  - name: 'default-receiver'
ALERTMANAGER_CONFIG

                    cat > "${MONITORING_DIR}/grafana/provisioning/datasources/datasource.yml" << 'GRAFANA_DATASOURCE'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    version: 1
    editable: false
GRAFANA_DATASOURCE

                    cat > "${MONITORING_DIR}/grafana/provisioning/dashboards/dashboards.yml" << 'GRAFANA_DASHBOARDS'
apiVersion: 1

providers:
  - name: 'Finn Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /etc/grafana/provisioning/dashboards
GRAFANA_DASHBOARDS
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

                # Check if monitoring config files are working
                echo "=== Checking monitoring configuration ==="
                echo "Prometheus config:"
                docker compose -p ${COMPOSE_PROJECT_NAME} exec prometheus ls -la /etc/prometheus/ || echo "Cannot check Prometheus config"
                
                echo "Alertmanager config:"
                docker compose -p ${COMPOSE_PROJECT_NAME} exec alertmanager ls -la /etc/alertmanager/ || echo "Cannot check Alertmanager config"
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