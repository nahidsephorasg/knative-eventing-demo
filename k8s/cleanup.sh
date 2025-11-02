#!/bin/bash

# ========================================
# Cleanup Knative Learning Demo
# ========================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🧹 Cleaning up Knative Learning Demo...${NC}"
echo ""

# Delete all resources
kubectl delete namespace knative-demo --ignore-not-found=true

echo ""
echo -e "${GREEN}✅ Cleanup complete!${NC}"
echo ""
echo "All resources in the 'knative-demo' namespace have been deleted."
