import os
import uuid
import logging
from flask import Flask, request, jsonify

# ========================================
# MESSAGE ROUTER SERVICE
# ========================================
# Purpose: Route messages to appropriate handlers based on content
# Pattern: Content-Based Routing
# Technique: Keyword matching (NO AI needed)
# ========================================

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [MESSAGE_ROUTER] - %(levelname)s - %(message)s'
)

APP_PORT = int(os.getenv("PORT", "8080"))


class MessageRouter:
    """
    Routes messages to appropriate departments using keyword matching
    
    Demonstrates:
    - Content-based routing
    - Multi-criteria classification
    - Scoring algorithm
    - Dynamic event type generation
    """
    
    def __init__(self):
        logging.info("✅ Message Router initialized")
        
        # Define routing rules with weighted keywords
        self.routing_rules = {
            'finance': {
                'keywords': [
                    'billing', 'invoice', 'payment', 'refund', 'charge',
                    'subscription', 'price', 'cost', 'fee', 'credit card',
                    'bank', 'transaction', 'receipt', 'balance', 'overcharged'
                ],
                'weight': 1.0
            },
            'support': {
                'keywords': [
                    'help', 'issue', 'problem', 'error', 'bug', 'broken',
                    'not working', 'troubleshoot', 'fix', 'support',
                    'assistance', 'technical', 'crash', 'freeze'
                ],
                'weight': 1.0
            },
            'website': {
                'keywords': [
                    'login', 'password', 'access', 'account', 'sign in',
                    'reset', 'locked out', 'username', 'authentication',
                    'forgot password', 'cannot log in', 'registration'
                ],
                'weight': 1.0
            }
        }
    
    def calculate_route_scores(self, text):
        """Calculate confidence scores for each route"""
        text_lower = text.lower()
        scores = {}
        
        for category, config in self.routing_rules.items():
            keywords = config['keywords']
            weight = config['weight']
            
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            
            # Calculate weighted score
            score = matches * weight
            scores[category] = {
                'score': score,
                'matches': matches
            }
        
        return scores
    
    def determine_route(self, scores):
        """Determine best route based on scores"""
        # Get category with highest score
        max_score = 0
        best_category = 'unknown'
        
        for category, data in scores.items():
            if data['score'] > max_score:
                max_score = data['score']
                best_category = category
        
        # Require minimum confidence
        if max_score == 0:
            return 'unknown', 0, 'No keywords matched'
        
        return best_category, max_score, f"Matched {scores[best_category]['matches']} keywords"
    
    def route(self, message):
        """
        Classify and route message based on content
        """
        content = message.get("content", "")
        message_id = message.get("message_id", "unknown")
        
        logging.info(f"[{message_id}] 🎯 Starting message routing...")
        
        # Calculate scores
        scores = self.calculate_route_scores(content)
        
        # Determine best route
        category, confidence, reason = self.determine_route(scores)
        
        routing_info = {
            "category": category,
            "confidence_score": confidence,
            "reason": reason,
            "all_scores": {cat: data['score'] for cat, data in scores.items()}
        }
        
        message["routing"] = routing_info
        message["processing_stage"] = "routed"
        
        logging.info(f"[{message_id}] 🎯 Routed to: {category} (confidence: {confidence})")
        logging.debug(f"[{message_id}] Detailed scores: {scores}")
        
        return message


# Global router instance
router = MessageRouter()


@app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes health check"""
    return "OK", 200


@app.route('/', methods=['POST'])
def handle_event():
    """
    CloudEvent handler with content-based routing
    
    Learning Points:
    1. Content analysis and classification
    2. Dynamic event type generation
    3. Multiple possible downstream consumers
    4. Routing confidence/scoring
    """
    if not request.is_json:
        return jsonify({"error": "Must be JSON"}), 415

    try:
        incoming_payload = request.get_json()
        message_id = incoming_payload.get("message_id", "unknown")
        
        logging.info(f"[{message_id}] 📥 Received event from Broker")

    except Exception as e:
        logging.error(f"❌ Failed to parse event: {e}")
        return jsonify({"error": "Invalid payload"}), 400

    # Route the message
    processed = router.route(incoming_payload)

    # Generate event type based on routing decision
    routing = processed.get("routing", {})
    category = routing.get("category", "unknown")
    
    if category == 'finance':
        event_type = "com.learning.message.routed.finance"
    elif category == 'support':
        event_type = "com.learning.message.routed.support"
    elif category == 'website':
        event_type = "com.learning.message.routed.website"
    else:
        event_type = "com.learning.message.routed.unknown"
        logging.warning(f"[{message_id}] ⚠️  Could not classify message")

    # Reply with new CloudEvent
    response_headers = {
        "Ce-Specversion": "1.0",
        "Ce-Type": event_type,
        "Ce-Source": "/services/message-router",
        "Ce-Id": str(uuid.uuid4()),
        "Ce-Subject": message_id,
    }

    logging.info(f"[{message_id}] 📤 Replying with event type '{event_type}'")
    return jsonify(processed), 200, response_headers


if __name__ == '__main__':
    logging.info(f"Service starting on port {APP_PORT}")
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
