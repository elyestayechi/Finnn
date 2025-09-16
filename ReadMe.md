# Finn AI Loan Analysis System - User Guide

## Overview

Finn is an AI-powered loan analysis system that automates risk assessment using machine learning and natural language processing. The system consists of:

- **Backend API (FastAPI)**: Processes loan applications, performs risk analysis, and generates reports
- **Frontend UI (React + TypeScript)**: Web interface for analysts to review loans and provide feedback
- **Ollama Integration**: Local LLM for advanced text analysis and reasoning
- **Monitoring Stack**: Prometheus, Grafana, and Alertmanager for observability
- **Jenkins CI/CD**: Automated build, test, and deployment pipeline

## Prerequisites

Before you begin, ensure you have:

- Docker and Docker Compose installed
- At least 8GB RAM available (for Ollama LLM)
- Git for cloning the repository
- (Optional) Jenkins for CI/CD automation

## Quick Start

### Option 1: Full Deployment with Docker Compose (Recommended)

# Clone the repository
git clone https://github.com/elyestayechi/Finnn.git
cd Finnn

# Start all services (application + monitoring + Jenkins)
docker compose -f docker-compose.local.yml up -d

# For a lighter deployment without Jenkins:
docker compose -f docker-compose.local.yml up -d ollama backend frontend prometheus grafana alertmanager

### Option 2: Development Mode (Automatic Data Migration)

# Use the development compose file with automatic migration
docker compose -f docker-compose.local.yml up -d --build
# The backend will automatically run data migration on startup

### Option 3: Jenkins CI/CD Pipeline

# First, start Jenkins and the application
docker compose -f docker-compose.local.yml up -d
# Access Jenkins: http://localhost:9190
# Create a new pipeline job pointing to your Git repository
# Run the build - Jenkins will automatically:
# - Build Docker images with unique version tags
# - Run tests
# - Deploy the application
# - Perform health checks

#### Important First-Time Setup
# Database Migration

The system now includes automatic data migration! When using docker-compose.local.yml, the backend will automatically:
-Migrate existing PDF reports to the database
-Import feedback data from JSON files
-Create analysis records from existing PDF content
-Set up the complete database schema

# Manual migration (if needed):
docker exec -it finn-backend-1 python migrate_data.py

### Access Points
# After successful deployment:

Frontend	http://localhost:3000	Main web interface
Backend API	http://localhost:8000	REST API & Documentation
API Docs	http://localhost:8000/docs	Interactive API documentation
Ollama	http://localhost:11435	LLM service
Grafana	http://localhost:3001	Monitoring dashboards
Prometheus	http://localhost:9090	Metrics database
Alertmanager	http://localhost:9093	Alert management
Jenkins	http://localhost:9190	CI/CD pipeline

# Default credentials:
Grafana: admin/admin
Jenkins: No authentication required (setup wizard disabled)

# Directory Structure
Finn/
├── Back/                 # Python FastAPI backend
│   ├── Data/            # Data files and databases
│   ├── PDF Loans/       # Generated PDF reports
│   ├── src/            # Source code
│   └── migrate_data.py  # Data migration script
├── Front/              # React frontend
├── monitoring/         # Monitoring configuration
│   ├── prometheus/     # Prometheus config
│   ├── alertmanager/   # Alertmanager config
│   └── grafana/        # Grafana dashboards & provisioning
├── jenkins/           # CI/CD configuration
├── docker-compose.yml # Jenkins pipeline deployment
└── docker-compose.local.yml # Local development deployment

### Deployment Options
1. Complete Stack (Recommended)
docker compose -f docker-compose.local.yml up -d
2. Application Only
docker compose -f docker-compose.local.yml up -d ollama backend frontend
3. Monitoring Only
docker compose -f docker-compose.local.yml up -d prometheus grafana alertmanager
4. Jenkins CI/CD Only
docker compose -f docker-compose.local.yml up -d jenkins

### Common Operations

# Restart Services
docker compose -f docker-compose.local.yml restart

# View Logs
# All services
docker compose -f docker-compose.local.yml logs
# Specific service
docker compose -f docker-compose.local.yml logs backend
docker compose -f docker-compose.local.yml logs frontend
# Stop Services
docker compose -f docker-compose.local.yml down
# Update and Redeploy
# Pull latest changes
git pull origin main
# Rebuild and redeploy
docker compose -f docker-compose.local.yml up -d --build

### Monitoring Features

The system includes comprehensive monitoring:
-Real-time metrics: CPU, memory, request rates
-Business metrics: Loan analysis volume, success rates
-Performance tracking: Processing times, error rates
-Alerting: Service health, performance degradation
-Dashboards: Pre-built Grafana dashboards

### API Usage

# Health check
curl http://localhost:8000/health
# API documentation
curl http://localhost:8000/docs
# Analyze a loan
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"loan_id": "12345", "customer_data": {...}}'

### Support
If you encounter issues:
Check logs: docker compose -f docker-compose.local.yml logs
Verify migration: Ensure migrate_data.py ran successfully
Check ports: Verify no conflicts on 3000, 8000, 11435, 9090, 9093, 3001, 9190
Resource check: Ensure enough RAM for Ollama LLM (8GB+ recommended)
Docker resources: Ensure Docker has enough memory and CPU allocation

### Remember
For local development, use docker-compose.local.yml
For production deployment via CI/CD, use the Jenkins pipeline
Data migration is now automatic when using the local compose file
All services are configured with health checks for reliability

### Need Help?
Check the service logs for specific errors
Verify all containers are running: docker compose -f docker-compose.local.yml ps
Ensure required data files exist in Back/Data/ and Back/PDF Loans/
Check that ports are not already in use by other applications


