#!/bin/bash

# ========================================
# Deploy Knative Learning Demo
# ========================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Knative Eventing Learning Demo${NC}"
echo -e "${BLUE}Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl.${NC}"
    exit 1
fi

# Check if connected to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Not connected to Kubernetes cluster${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Connected to Kubernetes cluster${NC}"
kubectl cluster-info | head -1
echo ""

# Deploy in order
echo -e "${YELLOW}📦 Deploying Knative Learning Demo...${NC}"
echo ""

echo -e "${BLUE}Step 1/10:${NC} Creating namespace..."
kubectl apply -f k8s/01-namespace.yaml

echo -e "${BLUE}Step 2/10:${NC} Creating Kafka Broker..."
kubectl apply -f k8s/02-broker.yaml

echo -e "${BLUE}Step 3/10:${NC} Deploying PostgreSQL database..."
kubectl apply -f k8s/03-database.yaml

echo -e "${BLUE}Step 4/10:${NC} Deploying Event Producer..."
kubectl apply -f k8s/10-event-producer.yaml

echo -e "${BLUE}Step 5/10:${NC} Deploying Data Extractor..."
kubectl apply -f k8s/20-data-extractor.yaml

echo -e "${BLUE}Step 6/10:${NC} Deploying Content Validator..."
kubectl apply -f k8s/30-content-validator.yaml

echo -e "${BLUE}Step 7/10:${NC} Deploying Database Enricher..."
kubectl apply -f k8s/40-database-enricher.yaml

echo -e "${BLUE}Step 8/10:${NC} Deploying Message Router..."
kubectl apply -f k8s/50-message-router.yaml

echo -e "${BLUE}Step 9/10:${NC} Deploying Finance Handler..."
kubectl apply -f k8s/60-finance-handler.yaml

echo -e "${BLUE}Step 10/10:${NC} Deploying Support Handler & Event Monitor..."
kubectl apply -f k8s/61-support-handler.yaml
kubectl apply -f k8s/70-event-monitor.yaml

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""

# Wait for resources
echo -e "${YELLOW}⏳ Waiting for resources to be ready...${NC}"
echo ""

echo "Waiting for database..."
kubectl wait --for=condition=ready pod -l app=customer-database -n knative-demo --timeout=120s || true

echo "Waiting for Knative Services..."
kubectl wait --for=condition=Ready ksvc --all -n knative-demo --timeout=180s || true

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Show status
echo -e "${YELLOW}📊 Deployment Status:${NC}"
echo ""
echo "Knative Services:"
kubectl get ksvc -n knative-demo

echo ""
echo "Regular Deployments:"
kubectl get deployment -n knative-demo

echo ""
echo "Triggers:"
kubectl get trigger -n knative-demo

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo ""
echo "1. Get Event Producer URL:"
echo -e "   ${GREEN}kubectl get ksvc event-producer -n knative-demo${NC}"
echo ""
echo "2. Access Finance Handler UI:"
echo -e "   ${GREEN}kubectl port-forward -n knative-demo svc/finance-handler 8888:80${NC}"
echo -e "   Then open: ${BLUE}http://localhost:8888${NC}"
echo ""
echo "3. Access Event Monitor Dashboard:"
echo -e "   ${GREEN}kubectl port-forward -n knative-demo svc/event-monitor 9999:80${NC}"
echo -e "   Then open: ${BLUE}http://localhost:9999${NC}"
echo ""
echo "4. Send a test message:"
echo -e "   ${GREEN}kubectl port-forward -n knative-demo svc/event-producer 8080:80${NC}"
echo -e "   ${GREEN}curl -X POST http://localhost:8080 \\${NC}"
echo -e "   ${GREEN}  -H 'Content-Type: application/json' \\${NC}"
echo -e "   ${GREEN}  -d '{\"content\": \"Hi, I need help with billing. Email: john.smith@globaltech.com\"}'${NC}"
echo ""
echo "5. Watch logs:"
echo -e "   ${GREEN}kubectl logs -f -l app=event-producer -n knative-demo${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
