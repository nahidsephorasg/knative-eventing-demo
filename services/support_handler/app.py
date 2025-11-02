import os
import json
import logging
from flask import Flask, request, jsonify

# ========================================
# SUPPORT HANDLER SERVICE
# ========================================
# Purpose: Handle support-related messages
# Pattern: Event Consumer (simple logger)
# Demo: Basic event consumption without UI
# ========================================

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SUPPORT_HANDLER] - %(levelname)s - %(message)s'
)

APP_PORT = int(os.getenv("PORT", "8080"))

# In-memory storage for demo
support_messages = []


@app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes health check"""
    return "OK", 200


@app.route('/messages', methods=['GET'])
def get_messages():
    """API endpoint to retrieve support messages"""
    return jsonify({
        "total": len(support_messages),
        "messages": support_messages[-50:]  # Last 50 messages
    }), 200


@app.route('/', methods=['POST'])
def handle_event():
    """
    CloudEvent handler for support messages
    
    Learning Points:
    1. Simple event consumption
    2. Event logging
    3. In-memory storage
    4. REST API for message retrieval
    """
    if not request.is_json:
        return jsonify({"error": "Must be JSON"}), 415

    try:
        event_type = request.headers.get('Ce-Type', 'unknown')
        message_id = request.headers.get('Ce-Subject', 'unknown')
        payload = request.get_json()
        
        logging.info(f"[{message_id}] 📥 Support message received (type: {event_type})")
        
        # Store message
        support_messages.append({
            "event_type": event_type,
            "message_id": message_id,
            "payload": payload,
            "received_at": payload.get("timestamp")
        })
        
        # Log important details
        extracted = payload.get("extracted_data", {})
        customer = payload.get("customer_data", {})
        
        logging.info(f"[{message_id}] 📧 From: {extracted.get('customer_name', 'Unknown')}")
        logging.info(f"[{message_id}] 📊 Sentiment: {extracted.get('sentiment', 'neutral')}")
        if extracted.get('is_urgent'):
            logging.warning(f"[{message_id}] ⚠️  URGENT support request!")
        
        if customer.get('is_known_customer'):
            logging.info(f"[{message_id}] 👤 Known customer: {customer.get('first_name')} {customer.get('last_name')}")
        
        # Acknowledge receipt
        return jsonify({"status": "received", "queue_position": len(support_messages)}), 200

    except Exception as e:
        logging.error(f"Error handling event: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logging.info(f"Support Handler starting on port {APP_PORT}")
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
