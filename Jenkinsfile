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

                # Ensure Grafana dashboard files exist
                echo "=== Ensuring Grafana dashboards exist ==="
                if [ ! -f "monitoring/grafana/provisioning/dashboards/finn-compact-dashboard.json" ]; then
                    echo "⚠️ finn-compact-dashboard.json not found - creating placeholder"
                    mkdir -p "monitoring/grafana/provisioning/dashboards"
                    cat > "monitoring/grafana/provisioning/dashboards/finn-compact-dashboard.json" << 'DASHBOARD_JSON'
{
  "dashboard": {
    "id": null,
    "title": "Finn Compact Dashboard",
    "tags": ["finn", "loan-analysis"],
    "timezone": "browser",
    "panels": [],
    "version": 1
  },
  "message": "Dashboard created via provisioning"
}
DASHBOARD_JSON
                fi

                if [ ! -f "monitoring/grafana/provisioning/dashboards/finn-executive-dashboard.json" ]; then
                    echo "⚠️ finn-executive-dashboard.json not found - creating placeholder"
                    cat > "monitoring/grafana/provisioning/dashboards/finn-executive-dashboard.json" << 'DASHBOARD_JSON'
{
  "dashboard": {
    "id": null,
    "title": "Finn Executive Dashboard",
    "tags": ["finn", "executive"],
    "timezone": "browser",
    "panels": [],
    "version": 1
  },
  "message": "Dashboard created via provisioning"
}
DASHBOARD_JSON
                fi

                echo "=== Grafana dashboard files ==="
                ls -la "monitoring/grafana/provisioning/dashboards/" || echo "Could not list dashboards"
                '''
            }
        }

        stage('Debug Workspace') {
            steps {
                sh 'pwd'
                sh 'ls -l'
                sh 'ls -l monitoring || true'
            }
        }

        stage('Build Backend') {
            steps {
                dir('Back') {
                    sh '''
                    echo "=== Building backend image ==="
                    docker build -t finn-backend:${BUILD_ID} -f Dockerfile .
                    echo "✅ Backend image built"
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

        stage('Build Monitoring Images') {
    steps {
        sh '''
        echo "=== Building monitoring images ==="
        docker build -t finn-prometheus:${BUILD_ID} ./monitoring/prometheus
        docker build -t finn-alertmanager:${BUILD_ID} ./monitoring/alertmanager
        docker build -t finn-grafana:${BUILD_ID} ./monitoring/grafana
        echo "✅ Monitoring images built"
        '''
    }
}

        stage('Cleanup Previous Containers') {
            steps {
                sh '''
                echo "=== Cleaning up old containers (except Jenkins) ==="
                
                # Stop and remove all containers except Jenkins
                RUNNING_CONTAINERS=$(docker ps -q --filter "name=jenkins" --format "{{.ID}}")
                if [ -n "$RUNNING_CONTAINERS" ]; then
                    echo "Keeping Jenkins container(s):"
                    docker ps --filter "name=jenkins"
                fi

                # Stop and remove all other containers
                docker ps -q | grep -v "$(docker ps -q --filter 'name=jenkins')" | xargs -r docker stop
                docker ps -a -q | grep -v "$(docker ps -q --filter 'name=jenkins')" | xargs -r docker rm -f

                # Clean up networks (but keep volumes for data persistence)
                docker network prune -f

                echo "✅ Old containers cleaned up (Jenkins untouched)"
                '''
            }
        }

        stage('Deploy Application with Monitoring') {
            steps {
                sh '''
                echo "=== Deploying stack without Jenkins ==="

                # Deploy the stack using docker-compose
                docker compose -p ${COMPOSE_PROJECT_NAME} -f docker-compose.yml up -d \
                  ollama backend frontend \
                  prometheus alertmanager grafana

                echo "✅ App + Monitoring deployed (Jenkins excluded)"
                '''
            }
        }

        stage('Health Check') {
    steps {
        sh '''
        echo "=== Health Check with retries ==="
        
        # Wait longer for backend to be ready (migration + server startup)
        echo "Waiting for backend to be ready..."
        MAX_RETRIES=15
        RETRY_DELAY=10
        
        for i in $(seq 1 $MAX_RETRIES); do
            # Check if backend container is running and healthy
            if docker compose -p ${COMPOSE_PROJECT_NAME} ps backend | grep -q "(healthy)"; then
                echo "✅ Backend is healthy (Docker healthcheck passed)"
                
            else
                echo "⏳ Backend not ready yet (attempt $i/$MAX_RETRIES)"
                if [ $i -eq $MAX_RETRIES ]; then
                    echo "❌ Backend health check failed after $MAX_RETRIES attempts"
                    # Show backend logs for debugging
                    echo "=== Backend logs ==="
                    docker compose -p ${COMPOSE_PROJECT_NAME} logs backend | tail -20
                    # Show container status
                    echo "=== Container status ==="
                    docker compose -p ${COMPOSE_PROJECT_NAME} ps
                fi
                sleep $RETRY_DELAY
            fi
        done

        # Check monitoring services using Docker health checks
        echo "=== Checking monitoring services ==="
        
        if docker compose -p ${COMPOSE_PROJECT_NAME} ps prometheus | grep -q "Up"; then
            echo "✅ Prometheus container is running"
        else
            echo "⚠️ Prometheus container not running"
        fi

        if docker compose -p ${COMPOSE_PROJECT_NAME} ps alertmanager | grep -q "Up"; then
            echo "✅ Alertmanager container is running"
        else
            echo "⚠️ Alertmanager container not running"
        fi

        if docker compose -p ${COMPOSE_PROJECT_NAME} ps grafana | grep -q "Up"; then
            echo "✅ Grafana container is running"
            
            # Wait a bit more for Grafana to fully initialize
            sleep 15
            
            # Check if Grafana is responding internally
            if docker compose -p ${COMPOSE_PROJECT_NAME} exec -T grafana curl -f http://localhost:3000/api/health; then
                echo "✅ Grafana health endpoint is responding"
            else
                echo "⚠️ Grafana container running but health endpoint not responding"
            fi
        else
            echo "⚠️ Grafana container not running"
        fi
        '''
    }
}

        stage('Verify Grafana Provisioning') {
    steps {
        sh '''
        echo "=== Verifying Grafana provisioning ==="
        sleep 20
        
        # Check if datasource was created (from within Grafana container)
        echo "Grafana datasources:"
        docker compose -p ${COMPOSE_PROJECT_NAME} exec -T grafana curl -s http://localhost:3000/api/datasources -u admin:admin | jq '.[].name' || echo "Could not fetch datasources"
        
        # Check if dashboards were created
        echo "Grafana dashboards:"
        docker compose -p ${COMPOSE_PROJECT_NAME} exec -T grafana curl -s http://localhost:3000/api/search -u admin:admin | jq '.[].title' || echo "Could not fetch dashboards"
        
        # Check Grafana provisioning directory
        echo "=== Grafana container file structure ==="
        docker compose -p ${COMPOSE_PROJECT_NAME} exec grafana ls -la /etc/grafana/provisioning/ || echo "Cannot check Grafana files"
        docker compose -p ${COMPOSE_PROJECT_NAME} exec grafana ls -la /etc/grafana/provisioning/dashboards/ || echo "Cannot check dashboard files"
        
        # Also check the actual exposed ports on host (for user information)
        echo "=== Host port check (for user reference) ==="
        echo "Backend should be available at: http://localhost:8000"
        echo "Grafana should be available at: http://localhost:3001"
        echo "Prometheus should be available at: http://localhost:9090"
        '''
    }
}
    }

    post {
        success {
            sh '''
            echo "🎉 DEPLOYMENT SUCCESSFUL! 🎉"
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
            echo "=== GRAFANA DASHBOARDS ==="
            echo "1. Open Grafana: http://localhost:3001"
            echo "2. Login with admin/admin"
            echo "3. Go to Dashboards → Browse"
            echo "4. Look for 'Finn Compact Dashboard' and 'Finn Executive Dashboard'"
            echo ""
            echo "If dashboards don't appear immediately, wait 1-2 minutes for provisioning"
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