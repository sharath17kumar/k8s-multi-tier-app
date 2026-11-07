#!/bin/bash

RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

TARGET=${1:-"backend"}

echo "========================================="
echo "  Incident Response Report"
echo "  Target: $TARGET"
echo "  Time: $(date)"
echo "========================================="

REPORT_DIR="/tmp/incident-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$REPORT_DIR"

echo -e "\n${YELLOW}[1/5] Pod Status${NC}"
kubectl get pods | grep "$TARGET"

echo -e "\n${YELLOW}[2/5] Pod Events${NC}"
for pod in $(kubectl get pods --no-headers | grep "$TARGET" | awk '{print $1}'); do
    echo "--- $pod ---"
    kubectl describe pod "$pod" | tail -15
    kubectl describe pod "$pod" > "$REPORT_DIR/describe-$pod.txt"
done

echo -e "\n${YELLOW}[3/5] Recent Logs${NC}"
for pod in $(kubectl get pods --no-headers | grep "$TARGET" | awk '{print $1}'); do
    echo "--- $pod logs (last 20 lines) ---"
    kubectl logs "$pod" --tail=20
    kubectl logs "$pod" --tail=200 > "$REPORT_DIR/logs-$pod.txt"
done

echo -e "\n${YELLOW}[4/5] Resource Usage${NC}"
kubectl top pods 2>/dev/null | grep "$TARGET"

echo -e "\n${YELLOW}[5/5] Recent Events${NC}"
kubectl get events --sort-by='.lastTimestamp' | tail -10
kubectl get events --sort-by='.lastTimestamp' > "$REPORT_DIR/events.txt"

echo ""
echo "========================================="
echo -e "  Full report saved to: ${YELLOW}$REPORT_DIR${NC}"
echo "========================================="
