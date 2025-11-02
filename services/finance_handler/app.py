import os
import json
import logging
import queue
import collections
from flask import Flask, request, jsonify, render_template_string, Response

# ========================================
# FINANCE HANDLER SERVICE
# ========================================
# Purpose: Handle finance-related messages with web UI
# Pattern: Event Consumer + Server-Sent Events (SSE)
# UI: Real-time inbox for finance team
# ========================================

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [FINANCE_HANDLER] - %(levelname)s - %(message)s'
)

APP_PORT = int(os.getenv("PORT", "8080"))


class MessageAnnouncer:
    """
    Manages Server-Sent Events (SSE) for real-time UI updates
    
    Demonstrates:
    - SSE implementation
    - In-memory message queue
    - Multiple client connections
    - Message history
    """
    
    def __init__(self):
        self.listeners = []
        self.history = collections.deque(maxlen=100)  # Keep last 100 messages
    
    def listen(self):
        """Generator for SSE stream - sends history then new messages"""
        # Send history first
        for msg in list(self.history):
            yield msg
        
        # Then listen for new messages
        q = queue.Queue(maxsize=10)
        self.listeners.append(q)
        try:
            while True:
                msg = q.get()
                yield msg
        finally:
            self.listeners.remove(q)
    
    def announce(self, msg):
        """Send message to all connected clients"""
        self.history.append(msg)
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]


announcer = MessageAnnouncer()


# Simple HTML UI template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Finance Team Inbox - Knative Learning Demo</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        h1 { color: #2c3e50; }
        .stats { background: white; padding: 15px; margin: 20px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .message { background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .message.urgent { border-left-color: #e74c3c; }
        .message-header { display: flex; justify-content: space-between; margin-bottom: 10px; }
        .customer-info { background: #ecf0f1; padding: 10px; border-radius: 3px; margin: 10px 0; }
        .content { margin: 10px 0; padding: 10px; background: #fafafa; border-radius: 3px; }
        .metadata { font-size: 12px; color: #7f8c8d; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 11px; margin-right: 5px; }
        .badge-urgent { background: #e74c3c; color: white; }
        .badge-negative { background: #e67e22; color: white; }
        .badge-positive { background: #27ae60; color: white; }
        .badge-known { background: #3498db; color: white; }
        .no-messages { text-align: center; padding: 40px; color: #95a5a6; }
    </style>
</head>
<body>
    <h1>💰 Finance Team Inbox</h1>
    <div class="stats">
        <strong>Status:</strong> <span id="status">Connecting...</span> | 
        <strong>Messages Received:</strong> <span id="count">0</span>
    </div>
    <div id="messages">
        <div class="no-messages">Waiting for finance messages...</div>
    </div>
    <script>
        let messageCount = 0;
        const messagesDiv = document.getElementById('messages');
        const statusSpan = document.getElementById('status');
        const countSpan = document.getElementById('count');
        
        const eventSource = new EventSource('/stream');
        
        eventSource.onopen = function() {
            statusSpan.textContent = '✅ Connected';
            statusSpan.style.color = '#27ae60';
        };
        
        eventSource.onerror = function() {
            statusSpan.textContent = '❌ Disconnected';
            statusSpan.style.color = '#e74c3c';
        };
        
        eventSource.addEventListener('finance_message', function(e) {
            const data = JSON.parse(e.data);
            
            if (messageCount === 0) {
                messagesDiv.innerHTML = '';
            }
            
            messageCount++;
            countSpan.textContent = messageCount;
            
            const extracted = data.extracted_data || {};
            const customer = data.customer_data || {};
            const routing = data.routing || {};
            const validation = data.validation || {};
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message' + (extracted.is_urgent ? ' urgent' : '');
            
            let badges = '';
            if (extracted.is_urgent) badges += '<span class="badge badge-urgent">URGENT</span>';
            if (extracted.sentiment === 'negative') badges += '<span class="badge badge-negative">Negative</span>';
            if (extracted.sentiment === 'positive') badges += '<span class="badge badge-positive">Positive</span>';
            if (customer.is_known_customer) badges += '<span class="badge badge-known">Known Customer</span>';
            
            let customerInfo = '';
            if (customer.is_known_customer) {
                customerInfo = `
                    <div class="customer-info">
                        <strong>👤 Customer:</strong> ${customer.first_name} ${customer.last_name} (ID: ${customer.customer_id})<br>
                        <strong>📧 Email:</strong> ${extracted.email || 'N/A'}<br>
                        <strong>🏢 Company:</strong> ${customer.company_name || 'N/A'}<br>
                        <strong>📱 Phone:</strong> ${customer.phone || 'N/A'}<br>
                        <strong>💰 Total Purchases:</strong> $${customer.total_purchases || 0}
                    </div>
                `;
            }
            
            messageDiv.innerHTML = `
                <div class="message-header">
                    <div><strong>Message ${data.message_id.substring(0, 8)}</strong></div>
                    <div>${badges}</div>
                </div>
                ${customerInfo}
                <div class="content">${data.content}</div>
                <div class="metadata">
                    📊 Routing Score: ${routing.confidence_score || 0} | 
                    🕐 ${new Date(data.timestamp).toLocaleString()}
                </div>
            `;
            
            messagesDiv.insertBefore(messageDiv, messagesDiv.firstChild);
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve the finance inbox UI"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes health check"""
    return "OK", 200


@app.route('/stream')
def stream():
    """SSE endpoint for real-time updates"""
    return Response(announcer.listen(), mimetype='text/event-stream')


@app.route('/', methods=['POST'])
def handle_event():
    """
    CloudEvent handler for finance messages
    
    Learning Points:
    1. Event consumption (terminal consumer)
    2. Real-time UI updates via SSE
    3. Message persistence (in-memory)
    4. No reply needed (terminal handler)
    """
    if not request.is_json:
        return jsonify({"error": "Must be JSON"}), 415

    try:
        event_type = request.headers.get('Ce-Type', 'unknown')
        message_id = request.headers.get('Ce-Subject', 'unknown')
        payload = request.get_json()
        
        logging.info(f"[{message_id}] 📥 Finance message received (type: {event_type})")
        
        # Format for SSE
        sse_msg = f"event: finance_message\ndata: {json.dumps(payload)}\n\n"
        
        # Announce to all connected clients
        announcer.announce(sse_msg)
        
        logging.info(f"[{message_id}] ✅ Message delivered to {len(announcer.listeners)} connected clients")
        
        # Acknowledge receipt (no reply event needed - this is a terminal consumer)
        return jsonify({"status": "received"}), 200

    except Exception as e:
        logging.error(f"Error handling event: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logging.info(f"Finance Handler UI starting on port {APP_PORT}")
    logging.info("Access the inbox at http://localhost:8080")
    app.run(host='0.0.0.0', port=APP_PORT, debug=True, threaded=True)
