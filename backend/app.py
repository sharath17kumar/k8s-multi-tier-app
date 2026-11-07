from flask import Flask, jsonify, request
import psycopg2
import os
import time

app = Flask(__name__)

# Simple metrics tracking
metrics = {
    'requests_total': 0,
    'requests_errors': 0,
    'request_duration_sum': 0,
}

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432'),
        database=os.environ.get('DB_NAME', 'appdb'),
        user=os.environ.get('DB_USER', 'appuser'),
        password=os.environ.get('DB_PASSWORD', 'apppassword')
    )
    return conn

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    metrics['requests_total'] += 1
    metrics['request_duration_sum'] += duration
    if response.status_code >= 400:
        metrics['requests_errors'] += 1
    return response

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/metrics')
def prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    output = []
    output.append(f"# HELP app_requests_total Total requests")
    output.append(f"# TYPE app_requests_total counter")
    output.append(f"app_requests_total {metrics['requests_total']}")
    output.append(f"# HELP app_requests_errors Total error responses")
    output.append(f"# TYPE app_requests_errors counter")
    output.append(f"app_requests_errors {metrics['requests_errors']}")
    output.append(f"# HELP app_request_duration_sum Total request duration in seconds")
    output.append(f"# TYPE app_request_duration_sum counter")
    output.append(f"app_request_duration_sum {metrics['request_duration_sum']:.4f}")
    return '\n'.join(output) + '\n', 200, {'Content-Type': 'text/plain'}

@app.route('/api/items', methods=['GET'])
def get_items():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, name, created_at FROM items ORDER BY created_at DESC')
        items = [{"id": row[0], "name": row[1], "created_at": str(row[2])} for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"items": items}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/db-status')
def db_status():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT version()')
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        return jsonify({"database": "connected", "version": version}), 200
    except Exception as e:
        return jsonify({"database": "disconnected", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
