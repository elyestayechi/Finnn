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

        stage('Deploy Application with Monitoring') {
    steps {
        sh '''
        echo "=== Deploying stack without Jenkins ==="

        # Step 1: Build Prometheus and Alertmanager images with embedded configs
        docker build -t finn-prometheus:${BUILD_ID} ./monitoring/prometheus
        docker build -t finn-alertmanager:${BUILD_ID} ./monitoring/alertmanager

        # Step 2: Deploy the stack using docker-compose
        # Use the corrected docker-compose.yml (no host file mounts for Prometheus/Alertmanager)
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