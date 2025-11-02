import os
import uuid
import logging
import re
from flask import Flask, request, jsonify

# ========================================
# DATA EXTRACTOR SERVICE
# ========================================
# Purpose: Extract structured data from raw text
# Pattern: Request-Reply - receives event, processes, replies with new event
# Technique: Regex-based extraction (NO AI/LLM needed)
# ========================================

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DATA_EXTRACTOR] - %(levelname)s - %(message)s'
)

APP_PORT = int(os.getenv("PORT", "8080"))


class DataExtractor:
    """
    Extracts structured information from unstructured text using regex patterns
    
    Demonstrates:
    - Pattern matching
    - Data normalization
    - Event transformation
    """
    
    def __init__(self):
        logging.info("✅ Data Extractor initialized")
        
    def extract_email(self, text):
        """Extract email address using standard email regex"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def extract_name(self, text):
        """
        Extract name using common patterns:
        - "My name is John Doe"
        - "I am Jane Smith"
        - "This is Mike Johnson"
        """
        patterns = [
            r'(?:my name is|i am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)'  # Capitalized full name
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        
        return None
    
    def extract_phone(self, text):
        """Extract phone number (US format)"""
        patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890 or 1234567890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}'      # (123) 456-7890
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def detect_urgency(self, text):
        """Detect urgency keywords"""
        urgent_keywords = [
            'urgent', 'asap', 'emergency', 'immediately',
            'critical', 'help', 'please help', 'stuck'
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in urgent_keywords)
    
    def detect_sentiment(self, text):
        """Simple keyword-based sentiment detection"""
        positive_words = ['happy', 'great', 'excellent', 'thank', 'pleased', 'love', 'wonderful']
        negative_words = ['frustrated', 'angry', 'disappointed', 'terrible', 'worst', 'hate', 'awful']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if neg_count > pos_count:
            return "negative"
        elif pos_count > neg_count:
            return "positive"
        return "neutral"
    
    def process(self, message):
        """
        Main processing logic - extract all available data
        """
        content = message.get("content", "")
        message_id = message.get("message_id", "unknown")
        
        logging.info(f"[{message_id}] 🔍 Starting data extraction...")
        
        # Extract structured data
        extracted_data = {
            "email": self.extract_email(content),
            "customer_name": self.extract_name(content),
            "phone": self.extract_phone(content),
            "sentiment": self.detect_sentiment(content),
            "is_urgent": self.detect_urgency(content),
            "content_length": len(content),
            "word_count": len(content.split())
        }
        
        logging.info(f"[{message_id}] 📊 Extracted: {extracted_data}")
        
        # Add extracted data to message
        message["extracted_data"] = extracted_data
        message["processing_stage"] = "extracted"
        
        return message


# Global extractor instance
extractor = DataExtractor()


@app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes health check"""
    return "OK", 200


@app.route('/', methods=['POST'])
def handle_event():
    """
    CloudEvent handler using Request-Reply pattern
    
    Learning Points:
    1. Receiving CloudEvents via HTTP POST
    2. Processing event payload
    3. Replying with new CloudEvent (auto-routed by Broker)
    4. Event type transformation based on processing result
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

    # Process the message
    processed = extractor.process(incoming_payload)

    # Determine event type based on extraction success
    extracted = processed.get("extracted_data", {})
    
    if extracted.get("email"):
        event_type = "com.learning.message.extracted"
        logging.info(f"[{message_id}] ✅ Data extracted successfully")
    else:
        event_type = "com.learning.message.extraction-incomplete"
        processed["errors"].append("No email address found")
        logging.warning(f"[{message_id}] ⚠️  No email found, marking as incomplete")

    # Reply with new CloudEvent
    response_headers = {
        "Ce-Specversion": "1.0",
        "Ce-Type": event_type,
        "Ce-Source": "/services/data-extractor",
        "Ce-Id": str(uuid.uuid4()),
        "Ce-Subject": message_id,
    }

    logging.info(f"[{message_id}] 📤 Replying with event type '{event_type}'")
    return jsonify(processed), 200, response_headers


if __name__ == '__main__':
    logging.info(f"Service starting on port {APP_PORT}")
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
