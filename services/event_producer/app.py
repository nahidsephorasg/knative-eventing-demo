import os
import uuid
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime

# ========================================
# EVENT PRODUCER SERVICE
# ========================================
# Purpose: Entry point for the system
# Pattern: SinkBinding - publishes events to Kafka Broker
# No external APIs required
# ========================================

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [EVENT_PRODUCER] - %(levelname)s - %(message)s'
)

APP_PORT = int(os.getenv("PORT", "8080"))
K_SINK = os.getenv('K_SINK')  # Injected by Knative SinkBinding

if not K_SINK:
    logging.error("❌ K_SINK environment variable not set")
    raise SystemExit("K_SINK required for event publishing")

logging.info(f"✅ Events will be published to: {K_SINK}")
logging.info(f"✅ Service listening on port: {APP_PORT}")


def create_cloudevent(content):
    """
    Creates a CloudEvent following the CloudEvents 1.0 specification
    
    CloudEvent components:
    - ce-specversion: CloudEvents version (1.0)
    - ce-type: Event type for filtering
    - ce-source: Origin of the event
    - ce-id: Unique event identifier
    - ce-subject: Business entity identifier
    - data: Event payload (JSON)
    """
    event_id = str(uuid.uuid4())
    message_id = event_id  # Same ID for demo simplicity
    
    payload = {
        "message_id": message_id,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
        "processing_stage": "received",
        "metadata": {
            "source_ip": "demo",
            "user_agent": "learning-demo"
        },
        "errors": []
    }
    
    headers = {
        "Ce-Specversion": "1.0",
        "Ce-Type": "com.learning.message.received",
        "Ce-Source": "/services/event-producer",
        "Ce-Id": event_id,
        "Ce-Subject": message_id,
        "Content-Type": "application/json",
    }
    
    return headers, payload


@app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes health check endpoint"""
    return "OK", 200


@app.route('/', methods=['POST'])
def produce_event():
    """
    HTTP endpoint that receives messages and publishes them as CloudEvents
    
    Learning Points:
    1. REST API to Event conversion
    2. CloudEvent creation
    3. Publishing to Kafka Broker via SinkBinding
    4. Error handling
    """
    if not request.is_json:
        logging.warning("⚠️  Request rejected: not JSON")
        return jsonify({"error": "Content-Type must be application/json"}), 415

    data = request.get_json()

    if not data or "content" not in data:
        logging.warning("⚠️  Request rejected: missing 'content' field")
        return jsonify({"error": "Payload must include 'content' field"}), 400

    content = data.get("content")

    if not isinstance(content, str) or not content.strip():
        logging.warning("⚠️  Request rejected: content must be non-empty string")
        return jsonify({"error": "'content' must be a non-empty string"}), 400

    logging.info("📥 Received message, creating CloudEvent...")
    headers, payload = create_cloudevent(content)

    try:
        logging.info(f"📤 Publishing event {headers['Ce-Id']} to Broker...")
        
        # Post to Kafka Broker via K_SINK (injected by SinkBinding)
        response = requests.post(
            K_SINK,
            json=payload,
            headers=headers,
            timeout=5.0
        )
        response.raise_for_status()

        logging.info(f"✅ Event published successfully (status: {response.status_code})")
        
        return jsonify({
            "status": "success",
            "message": "Event published to Kafka Broker",
            "event_id": headers['Ce-Id'],
            "event_type": headers['Ce-Type']
        }), 202

    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Failed to publish event: {e}")
        return jsonify({
            "status": "error",
            "message": "Failed to publish event to broker"
        }), 503


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
