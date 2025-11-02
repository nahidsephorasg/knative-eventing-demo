import os
import uuid
import logging
import re
from flask import Flask, request, jsonify

# ========================================
# CONTENT VALIDATOR SERVICE
# ========================================
# Purpose: Validate message content for safety and quality
# Pattern: Conditional Routing - pass/fail determines event type
# Technique: Rule-based validation (NO AI needed)
# ========================================

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [CONTENT_VALIDATOR] - %(levelname)s - %(message)s'
)

APP_PORT = int(os.getenv("PORT", "8080"))

# Validation rules
SPAM_KEYWORDS = [
    'viagra', 'cialis', 'lottery', 'winner', 'congratulations',
    'click here', 'free money', 'nigerian prince', 'inheritance',
    'crypto', 'bitcoin wallet', 'investment opportunity'
]

PROFANITY_LIST = [
    'spam', 'scam', 'hack', 'phishing', 'malware', 'virus'
]


class ContentValidator:
    """
    Validates message content using rule-based checks
    
    Demonstrates:
    - Content filtering
    - Multi-criteria validation
    - Error accumulation
    - Conditional event routing
    """
    
    def __init__(self):
        logging.info("✅ Content Validator initialized")
    
    def check_spam_keywords(self, text):
        """Check for spam/scam keywords"""
        text_lower = text.lower()
        found = [word for word in SPAM_KEYWORDS if word in text_lower]
        return found
    
    def check_profanity(self, text):
        """Check for profanity keywords"""
        text_lower = text.lower()
        found = [word for word in PROFANITY_LIST if word in text_lower]
        return found
    
    def check_length(self, text):
        """Validate message length"""
        issues = []
        if len(text) < 10:
            issues.append("Message too short (minimum 10 characters)")
        if len(text) > 10000:
            issues.append("Message too long (maximum 10,000 characters)")
        return issues
    
    def check_excessive_caps(self, text):
        """Check for excessive capitalization (shouting)"""
        if len(text) > 20:  # Only check if message is long enough
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text)
            if caps_ratio > 0.5:
                return "Excessive capitalization detected (>50%)"
        return None
    
    def check_urls(self, text):
        """Check for suspicious number of URLs"""
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        if len(urls) > 3:
            return f"Too many URLs detected ({len(urls)})"
        return None
    
    def check_repeated_characters(self, text):
        """Check for excessive character repetition (e.g., 'heeeeelp')"""
        pattern = r'(.)\1{4,}'  # Same character repeated 5+ times
        if re.search(pattern, text):
            return "Excessive character repetition detected"
        return None
    
    def validate(self, message):
        """
        Run all validation checks on message
        """
        content = message.get("content", "")
        message_id = message.get("message_id", "unknown")
        
        logging.info(f"[{message_id}] 🛡️  Starting content validation...")
        
        validation_results = {
            "is_valid": True,
            "checks_performed": 0,
            "issues_found": []
        }
        
        # Check spam keywords
        spam = self.check_spam_keywords(content)
        validation_results["checks_performed"] += 1
        if spam:
            validation_results["is_valid"] = False
            validation_results["issues_found"].append(f"Spam keywords: {', '.join(spam)}")
            logging.warning(f"[{message_id}] ⚠️  Spam keywords detected: {spam}")
        
        # Check profanity
        profanity = self.check_profanity(content)
        validation_results["checks_performed"] += 1
        if profanity:
            validation_results["is_valid"] = False
            validation_results["issues_found"].append(f"Profanity: {', '.join(profanity)}")
            logging.warning(f"[{message_id}] ⚠️  Profanity detected: {profanity}")
        
        # Check length
        length_issues = self.check_length(content)
        validation_results["checks_performed"] += 1
        if length_issues:
            validation_results["is_valid"] = False
            validation_results["issues_found"].extend(length_issues)
            logging.warning(f"[{message_id}] ⚠️  Length issues: {length_issues}")
        
        # Check excessive caps
        caps_issue = self.check_excessive_caps(content)
        validation_results["checks_performed"] += 1
        if caps_issue:
            validation_results["is_valid"] = False
            validation_results["issues_found"].append(caps_issue)
            logging.warning(f"[{message_id}] ⚠️  {caps_issue}")
        
        # Check URLs
        url_issue = self.check_urls(content)
        validation_results["checks_performed"] += 1
        if url_issue:
            validation_results["is_valid"] = False
            validation_results["issues_found"].append(url_issue)
            logging.warning(f"[{message_id}] ⚠️  {url_issue}")
        
        # Check repeated characters
        repeat_issue = self.check_repeated_characters(content)
        validation_results["checks_performed"] += 1
        if repeat_issue:
            validation_results["is_valid"] = False
            validation_results["issues_found"].append(repeat_issue)
            logging.warning(f"[{message_id}] ⚠️  {repeat_issue}")
        
        message["validation"] = validation_results
        message["processing_stage"] = "validated"
        
        if validation_results["is_valid"]:
            logging.info(f"[{message_id}] ✅ All validation checks passed ({validation_results['checks_performed']} checks)")
        else:
            logging.warning(f"[{message_id}] ❌ Validation failed: {len(validation_results['issues_found'])} issues")
            # Add to errors list
            for issue in validation_results["issues_found"]:
                message["errors"].append(f"validation:{issue}")
        
        return message


# Global validator instance
validator = ContentValidator()


@app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes health check"""
    return "OK", 200


@app.route('/', methods=['POST'])
def handle_event():
    """
    CloudEvent handler with conditional routing
    
    Learning Points:
    1. Validation logic
    2. Conditional event type based on validation result
    3. Error accumulation pattern
    4. Dead letter queue routing (invalid messages)
    """
    if not request.is_json:
        return jsonify({"error": "Must be JSON"}), 415

    try:
        incoming_payload = request.get_json()
        message_id = incoming_payload.get("message_id", "unknown")
        
        logging.info(f"[{message_id}] 📥 Received event from Broker")
        original_error_count = len(incoming_payload.get("errors", []))

    except Exception as e:
        logging.error(f"❌ Failed to parse event: {e}")
        return jsonify({"error": "Invalid payload"}), 400

    # Validate the message
    processed = validator.validate(incoming_payload)

    # Determine event type based on validation result
    current_error_count = len(processed.get("errors", []))
    
    if current_error_count > original_error_count:
        # New errors were added during validation
        event_type = "com.learning.message.validation-failed"
        logging.warning(f"[{message_id}] 🚨 Validation failed, routing to review queue")
    else:
        event_type = "com.learning.message.validated"
        logging.info(f"[{message_id}] ✅ Validation passed, continuing pipeline")

    # Reply with new CloudEvent
    response_headers = {
        "Ce-Specversion": "1.0",
        "Ce-Type": event_type,
        "Ce-Source": "/services/content-validator",
        "Ce-Id": str(uuid.uuid4()),
        "Ce-Subject": message_id,
    }

    logging.info(f"[{message_id}] 📤 Replying with event type '{event_type}'")
    return jsonify(processed), 200, response_headers


if __name__ == '__main__':
    logging.info(f"Service starting on port {APP_PORT}")
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
