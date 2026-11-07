#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "  Kubernetes Cluster Health Report"
echo "  $(date)"
echo "========================================="
echo ""

echo -e "${YELLOW}[1/5] Node Status${NC}"
echo "-------------------"
NODE_STATUS=$(kubectl get nodes --no-headers)
echo "$NODE_STATUS"
if echo "$NODE_STATUS" | grep -q "NotReady"; then
    echo -e "${RED}WARNING: Some nodes are NotReady!${NC}"
else
    echo -e "${GREEN}All nodes are Ready${NC}"
fi
echo ""

echo -e "${YELLOW}[2/5] Pod Status${NC}"
echo "-------------------"
TOTAL_PODS=$(kubectl get pods --all-namespaces --no-headers | wc -l)
RUNNING_PODS=$(kubectl get pods --all-namespaces --no-headers | grep -c "Running\|Completed")
FAILED_PODS=$(kubectl get pods --all-namespaces --no-headers | grep -c "Error\|CrashLoopBackOff\|ImagePullBackOff\|Pending")
echo "Total Pods: $TOTAL_PODS"
echo -e "Healthy: ${GREEN}$RUNNING_PODS${NC}"
echo -e "Unhealthy: ${RED}$FAILED_PODS${NC}"
if [ "$FAILED_PODS" -gt 0 ]; then
    echo ""
    echo -e "${RED}Unhealthy Pods:${NC}"
    kubectl get pods --all-namespaces --no-headers | grep -E "Error|CrashLoopBackOff|ImagePullBackOff|Pending"
fi
echo ""

echo -e "${YELLOW}[3/5] Resource Usage${NC}"
echo "-------------------"
kubectl top nodes 2>/dev/null || echo "Metrics not available"
echo ""

echo -e "${YELLOW}[4/5] Deployment Status${NC}"
echo "-------------------"
kubectl get deployments --no-headers | while read line; do
    NAME=$(echo $line | awk '{print $1}')
    READY=$(echo $line | awk '{print $2}')
    DESIRED=$(echo $READY | cut -d'/' -f2)
    ACTUAL=$(echo $READY | cut -d'/' -f1)
    if [ "$ACTUAL" -eq "$DESIRED" ]; then
        echo -e "${GREEN}$NAME: $READY replicas ready${NC}"
    else
        echo -e "${RED}$NAME: $READY replicas (expected $DESIRED)${NC}"
    fi
done
echo ""

echo -e "${YELLOW}[5/5] Services${NC}"
echo "-------------------"
kubectl get services --no-headers | while read line; do
    NAME=$(echo $line | awk '{print $1}')
    TYPE=$(echo $line | awk '{print $2}')
    PORT=$(echo $line | awk '{print $5}')
    echo "$NAME ($TYPE) - $PORT"
done
echo ""
echo "========================================="
echo "  Health check complete"
echo "========================================="
