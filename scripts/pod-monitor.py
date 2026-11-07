#!/usr/bin/env python3
import subprocess
import json
import time
from datetime import datetime

CPU_THRESHOLD = 80
MAX_REPLICAS = 5
MIN_REPLICAS = 1
CHECK_INTERVAL = 10

def run_kubectl(command):
    try:
        result = subprocess.run(command.split(), capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return None
        return result.stdout
    except subprocess.TimeoutExpired:
        return None

def get_pod_metrics():
    output = run_kubectl("kubectl top pods --no-headers")
    if not output:
        return []
    pods = []
    for line in output.strip().split('\n'):
        parts = line.split()
        if len(parts) >= 3:
            pods.append({
                'name': parts[0],
                'cpu': parts[1],
                'memory': parts[2],
                'cpu_millicores': int(parts[1].replace('m', '')) if 'm' in parts[1] else 0,
                'memory_mi': int(parts[2].replace('Mi', '')) if 'Mi' in parts[2] else 0
            })
    return pods

def get_deployment_replicas(name):
    output = run_kubectl(f"kubectl get deployment {name} -o json")
    if not output:
        return None
    data = json.loads(output)
    return data['spec']['replicas']

def scale_deployment(name, replicas):
    print(f"\n  >>> SCALING {name} to {replicas} replicas at {datetime.now().strftime('%H:%M:%S')}")
    run_kubectl(f"kubectl scale deployment {name} --replicas={replicas}")

def check_and_scale():
    print(f"\n--- Check at {datetime.now().strftime('%H:%M:%S')} ---")
    pods = get_pod_metrics()
    if not pods:
        print("  No metrics available yet")
        return

    for pod in pods:
        print(f"  {pod['name']}: CPU={pod['cpu']}, Memory={pod['memory']}")

    backend_pods = [p for p in pods if p['name'].startswith('backend-')]
    if backend_pods:
        avg_cpu = sum(p['cpu_millicores'] for p in backend_pods) / len(backend_pods)
        current = get_deployment_replicas('backend')
        if current is None:
            return

        print(f"\n  Backend avg CPU: {avg_cpu:.0f}m | Replicas: {current}")

        if avg_cpu > CPU_THRESHOLD and current < MAX_REPLICAS:
            scale_deployment('backend', min(current + 1, MAX_REPLICAS))
        elif avg_cpu < 20 and current > MIN_REPLICAS:
            scale_deployment('backend', max(current - 1, MIN_REPLICAS))
        else:
            print("  No scaling needed")

def main():
    print("=" * 45)
    print("  Pod Monitor & Auto-Scaler")
    print(f"  CPU Threshold: {CPU_THRESHOLD}m")
    print(f"  Check every: {CHECK_INTERVAL}s")
    print("  Press Ctrl+C to stop")
    print("=" * 45)

    try:
        while True:
            check_and_scale()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")

if __name__ == '__main__':
    main()
