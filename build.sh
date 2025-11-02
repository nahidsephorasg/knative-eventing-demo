#!/bin/bash

# ========================================
# Build All Services Script
# Knative Eventing Learning Demo
# ========================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Knative Eventing Learning Demo${NC}"
echo -e "${BLUE}Build All Services${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Load environment variables
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo -e "${YELLOW}Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env with your Docker Hub username${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Loading environment variables...${NC}"
set -a
source .env
set +a

# Validate configuration
if [ -z "$IMAGE_REGISTRY" ] || [ "$IMAGE_REGISTRY" = "docker.io/your-dockerhub-username" ]; then
    echo -e "${RED}❌ IMAGE_REGISTRY not configured in .env${NC}"
    echo -e "${YELLOW}Please edit .env and set your Docker Hub username${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Registry: ${IMAGE_REGISTRY}${NC}"
echo -e "${GREEN}✓ Tag: ${IMAGE_TAG}${NC}"
echo ""

# Array of all services
services=(
    "event-producer"
    "data-extractor"
    "content-validator"
    "database-enricher"
    "message-router"
    "finance-handler"
    "support-handler"
    "event-monitor"
    "customer-database"
)

# Function to build and push
build_and_push() {
    local service=$1
    local image_name="${IMAGE_REGISTRY}/${service}:${IMAGE_TAG}"
    
    echo -e "${YELLOW}🔨 Building ${service}...${NC}"
    
    if docker build \
        --platform linux/amd64 \
        --target "${service}" \
        -t "${image_name}" \
        -f Dockerfile \
        . ; then
        
        echo -e "${GREEN}✓ Built ${service}${NC}"
        echo -e "${YELLOW}📤 Pushing ${service}...${NC}"
        
        if docker push "${image_name}"; then
            echo -e "${GREEN}✓ Pushed ${service}${NC}"
            echo ""
            return 0
        else
            echo -e "${RED}❌ Failed to push ${service}${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Failed to build ${service}${NC}"
        return 1
    fi
}

# Main build loop
echo -e "${GREEN}🚀 Building ${#services[@]} services...${NC}"
echo ""

success_count=0
fail_count=0
failed_services=()

for service in "${services[@]}"; do
    if build_and_push "$service"; then
        ((success_count++))
    else
        ((fail_count++))
        failed_services+=("$service")
    fi
done

# Summary
echo "========================================"
echo -e "${GREEN}✅ Successfully built: ${success_count}/${#services[@]}${NC}"

if [ $fail_count -gt 0 ]; then
    echo -e "${RED}❌ Failed: ${fail_count}/${#services[@]}${NC}"
    echo -e "${RED}Failed services:${NC}"
    for service in "${failed_services[@]}"; do
        echo -e "${RED}  - ${service}${NC}"
    done
    exit 1
else
    echo -e "${GREEN}🎉 All services built and pushed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  1. Deploy to Kubernetes: ${YELLOW}kubectl apply -f k8s/${NC}"
    echo -e "  2. Check service status: ${YELLOW}kubectl get ksvc -n knative-demo${NC}"
    echo -e "  3. View logs: ${YELLOW}kubectl logs -f <pod-name> -n knative-demo${NC}"
fi
