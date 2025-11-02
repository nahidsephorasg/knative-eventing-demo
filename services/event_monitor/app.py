import os
import json
import logging
import queue
import collections
from flask import Flask, request, jsonify, render_template_string, Response

# ========================================
# EVENT MONITOR SERVICE
# ========================================
# Purpose: Monitor ALL events in the system
# Pattern: Wildcard Event Consumer + Real-time Dashboard
# UI: Complete event flow visualization
# ========================================

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [EVENT_MONITOR] - %(levelname)s - %(message)s'
)

APP_PORT = int(os.getenv("PORT", "8080"))


class EventAnnouncer:
    """Manages SSE for real-time event monitoring"""
    
    def __init__(self):
        self.listeners = []
        self.history = collections.deque(maxlen=200)
    
    def listen(self):
        for msg in list(self.history):
            yield msg
        q = queue.Queue(maxsize=20)
        self.listeners.append(q)
        try:
            while True:
                msg = q.get()
                yield msg
        finally:
            self.listeners.remove(q)
    
    def announce(self, msg):
        self.history.append(msg)
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]


announcer = EventAnnouncer()


# Dashboard HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Event Monitor - Knative Learning Demo</title>
    <style>
        body { font-family: 'Courier New', monospace; margin: 0; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
        h1 { color: #4ec9b0; margin-bottom: 5px; }
        .subtitle { color: #808080; margin-bottom: 20px; }
        .stats { background: #252526; padding: 15px; margin-bottom: 20px; border-radius: 5px; border-left: 3px solid #4ec9b0; }
        .event { background: #252526; padding: 12px; margin: 8px 0; border-left: 3px solid #569cd6; border-radius: 3px; font-size: 13px; }
        .event.received { border-left-color: #4ec9b0; }
        .event.extracted { border-left-color: #dcdcaa; }
        .event.validated { border-left-color: #b5cea8; }
        .event.enriched { border-left-color: #9cdcfe; }
        .event.routed { border-left-color: #c586c0; }
        .event.failed { border-left-color: #f48771; }
        .event-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .event-type { color: #4fc1ff; font-weight: bold; }
        .event-source { color: #ce9178; }
        .event-id { color: #808080; font-size: 11px; }
        .event-subject { color: #dcdcaa; }
        .event-data { background: #1e1e1e; padding: 8px; margin-top: 8px; border-radius: 3px; font-size: 11px; }
        .key { color: #9cdcfe; }
        .string { color: #ce9178; }
        .number { color: #b5cea8; }
        .boolean { color: #569cd6; }
        .null { color: #808080; }
        .no-events { text-align: center; padding: 40px; color: #808080; }
    </style>
</head>
<body>
    <h1>🔍 Knative Event Monitor</h1>
    <div class="subtitle">Real-time CloudEvents Flow Visualization</div>
    <div class="stats">
        <strong>Status:</strong> <span id="status">Connecting...</span> | 
        <strong>Events Captured:</strong> <span id="count">0</span> |
        <strong>Clients Connected:</strong> <span id="clients">0</span>
    </div>
    <div id="events">
        <div class="no-events">Waiting for events...</div>
    </div>
    <script>
        let eventCount = 0;
        const eventsDiv = document.getElementById('events');
        const statusSpan = document.getElementById('status');
        const countSpan = document.getElementById('count');
        
        const eventSource = new EventSource('/stream');
        
        eventSource.onopen = function() {
            statusSpan.textContent = '✅ Connected';
            statusSpan.style.color = '#4ec9b0';
        };
        
        eventSource.onerror = function() {
            statusSpan.textContent = '❌ Disconnected';
            statusSpan.style.color = '#f48771';
        };
        
        eventSource.addEventListener('monitor_event', function(e) {
            const data = JSON.parse(e.data);
            
            if (eventCount === 0) {
                eventsDiv.innerHTML = '';
            }
            
            eventCount++;
            countSpan.textContent = eventCount;
            
            const ce = data.cloudEvent;
            const stage = data.stage || 'unknown';
            
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event ' + stage;
            
            const timestamp = new Date(ce.payload.timestamp || Date.now()).toLocaleTimeString();
            
            eventDiv.innerHTML = `
                <div class="event-header">
                    <div>
                        <span class="event-type">${ce.type}</span> 
                        <span class="event-id">(${ce.id.substring(0, 8)}...)</span>
                    </div>
                    <div>${timestamp}</div>
                </div>
                <div>
                    <span class="key">Source:</span> <span class="event-source">${ce.source}</span> | 
                    <span class="key">Subject:</span> <span class="event-subject">${ce.subject.substring(0, 8)}...</span>
                </div>
                <div class="event-data">
                    <div><span class="key">Stage:</span> <span class="string">"${ce.payload.processing_stage || 'N/A'}"</span></div>
                    <div><span class="key">Content:</span> <span class="string">"${(ce.payload.content || '').substring(0, 100)}..."</span></div>
                    ${ce.payload.errors && ce.payload.errors.length > 0 ? 
                        `<div><span class="key">Errors:</span> <span class="string">${ce.payload.errors.join(', ')}</span></div>` : ''}
                </div>
            `;
            
            eventsDiv.insertBefore(eventDiv, eventsDiv.firstChild);
            
            // Keep only last 50 events in DOM
            if (eventsDiv.children.length > 50) {
                eventsDiv.removeChild(eventsDiv.lastChild);
            }
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Serve the event monitor dashboard"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes health check"""
    return "OK", 200


@app.route('/stream')
def stream():
    """SSE endpoint for real-time event updates"""
    return Response(announcer.listen(), mimetype='text/event-stream')


@app.route('/', methods=['POST'])
def handle_event():
    """
    CloudEvent handler - captures ALL events
    
    Learning Points:
    1. Wildcard event filtering (via Trigger config)
    2. Event monitoring/observability
    3. Real-time dashboard
    4. Event flow visualization
    """
    try:
        # Extract CloudEvent metadata from headers
        cloud_event = {
            "type": request.headers.get('Ce-Type', 'unknown'),
            "source": request.headers.get('Ce-Source', 'unknown'),
            "id": request.headers.get('Ce-Id', 'unknown'),
            "specversion": request.headers.get('Ce-Specversion', '1.0'),
            "subject": request.headers.get('Ce-Subject', 'unknown'),
            "payload": request.get_json()
        }
        
        message_id = cloud_event["subject"]
        
        # Determine processing stage from event type
        event_type = cloud_event["type"]
        if "received" in event_type:
            stage = "received"
        elif "extracted" in event_type:
            stage = "extracted"
        elif "validated" in event_type or "validation" in event_type:
            stage = "validated"
        elif "enriched" in event_type:
            stage = "enriched"
        elif "routed" in event_type:
            stage = "routed"
        elif "failed" in event_type or "error" in event_type:
            stage = "failed"
        else:
            stage = "unknown"
        
        logging.info(f"[{message_id}] 📊 Event captured: {event_type} (stage: {stage})")
        
        # Format for SSE
        sse_data = {
            "messageId": message_id,
            "cloudEvent": cloud_event,
            "stage": stage
        }
        
        sse_msg = f"event: monitor_event\ndata: {json.dumps(sse_data)}\n\n"
        
        # Announce to all connected clients
        announcer.announce(sse_msg)
        
        logging.debug(f"[{message_id}] Broadcasted to {len(announcer.listeners)} monitors")
        
        # Acknowledge receipt
        return jsonify({"status": "monitored"}), 200

    except Exception as e:
        logging.error(f"Error monitoring event: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    logging.info(f"Event Monitor starting on port {APP_PORT}")
    logging.info("Access the dashboard at http://localhost:8080")
    app.run(host='0.0.0.0', port=APP_PORT, debug=True, threaded=True)
