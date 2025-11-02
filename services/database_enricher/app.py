import os
import uuid
import logging
import psycopg2
from psycopg2 import sql
from flask import Flask, request, jsonify

# ========================================
# DATABASE ENRICHER SERVICE
# ========================================
# Purpose: Enrich events with data from PostgreSQL
# Pattern: Event Enrichment - add external data to events
# Integration: PostgreSQL database lookup
# ========================================

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [DATABASE_ENRICHER] - %(levelname)s - %(message)s'
)

APP_PORT = int(os.getenv("PORT", "8080"))

# Database configuration
DB_HOST = os.getenv("DB_HOST", "customer-database")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "customers")
DB_USER = os.getenv("DB_USER", "demo")
DB_PASSWORD = os.getenv("DB_PASSWORD", "demo123")


class DatabaseEnricher:
    """
    Enriches messages with customer data from PostgreSQL
    
    Demonstrates:
    - Database integration
    - Event enrichment pattern
    - Connection management
    - Error handling with databases
    """
    
    def __init__(self):
        self.conn_string = f"dbname='{DB_NAME}' user='{DB_USER}' password='{DB_PASSWORD}' host='{DB_HOST}' port='{DB_PORT}'"
        logging.info("✅ Database Enricher initialized")
        
        # Test connection on startup
        try:
            with psycopg2.connect(self.conn_string) as conn:
                logging.info(f"✅ Connected to database '{DB_NAME}' at {DB_HOST}:{DB_PORT}")
        except psycopg2.OperationalError as e:
            logging.error(f"❌ Database connection failed: {e}")
            raise SystemExit(f"Cannot start without database connection")
    
    def lookup_customer(self, email):
        """
        Look up customer by email address
        """
        connection = None
        cursor = None
        
        try:
            connection = psycopg2.connect(self.conn_string)
            cursor = connection.cursor()
            
            query = sql.SQL("""
                SELECT 
                    customer_id, 
                    first_name, 
                    last_name, 
                    company_name, 
                    country, 
                    phone,
                    account_status,
                    total_purchases,
                    last_purchase_date
                FROM customers 
                WHERE email = %s
            """)
            
            cursor.execute(query, (email,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "customer_id": result[0],
                    "first_name": result[1],
                    "last_name": result[2],
                    "company_name": result[3],
                    "country": result[4],
                    "phone": result[5],
                    "account_status": result[6],
                    "total_purchases": float(result[7]) if result[7] else 0.0,
                    "last_purchase_date": result[8].isoformat() if result[8] else None,
                    "is_known_customer": True
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Database query error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def enrich(self, message):
        """
        Enrich message with customer data from database
        """
        message_id = message.get("message_id", "unknown")
        extracted_data = message.get("extracted_data", {})
        email = extracted_data.get("email")
        
        if not email:
            logging.warning(f"[{message_id}] ⚠️  No email address to look up")
            message["errors"].append("enrichment:no-email")
            message["customer_data"] = {"is_known_customer": False}
            return message
        
        logging.info(f"[{message_id}] 🔍 Looking up customer: {email}")
        
        try:
            customer_data = self.lookup_customer(email)
            
            if customer_data:
                logging.info(f"[{message_id}] ✅ Customer found: {customer_data.get('first_name')} {customer_data.get('last_name')} (ID: {customer_data.get('customer_id')})")
                message["customer_data"] = customer_data
            else:
                logging.warning(f"[{message_id}] ⚠️  Customer not found in database")
                message["customer_data"] = {"is_known_customer": False}
                message["errors"].append(f"enrichment:customer-not-found:{email}")
        
        except Exception as e:
            logging.error(f"[{message_id}] ❌ Database lookup failed: {e}")
            message["errors"].append(f"enrichment:database-error:{str(e)}")
            message["customer_data"] = {"is_known_customer": False}
        
        message["processing_stage"] = "enriched"
        return message


# Global enricher instance
enricher = DatabaseEnricher()


@app.route('/healthz', methods=['GET'])
def healthz():
    """Kubernetes health check with database connectivity check"""
    try:
        with psycopg2.connect(enricher.conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
        return "OK", 200
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return "Database connection failed", 503


@app.route('/', methods=['POST'])
def handle_event():
    """
    CloudEvent handler with database enrichment
    
    Learning Points:
    1. External system integration (PostgreSQL)
    2. Event enrichment pattern
    3. Handling missing data gracefully
    4. Database connection management in event-driven systems
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

    # Enrich with database data
    processed = enricher.enrich(incoming_payload)

    # Determine event type based on enrichment result
    current_error_count = len(processed.get("errors", []))
    customer_data = processed.get("customer_data", {})
    
    if current_error_count > original_error_count:
        # Enrichment failed or customer not found
        event_type = "com.learning.message.enrichment-failed"
        logging.warning(f"[{message_id}] ⚠️  Enrichment incomplete, routing to review")
    elif customer_data.get("is_known_customer"):
        event_type = "com.learning.message.enriched"
        logging.info(f"[{message_id}] ✅ Customer data added, continuing pipeline")
    else:
        event_type = "com.learning.message.unknown-customer"
        logging.warning(f"[{message_id}] ⚠️  Unknown customer, routing to review")

    # Reply with new CloudEvent
    response_headers = {
        "Ce-Specversion": "1.0",
        "Ce-Type": event_type,
        "Ce-Source": "/services/database-enricher",
        "Ce-Id": str(uuid.uuid4()),
        "Ce-Subject": message_id,
    }

    logging.info(f"[{message_id}] 📤 Replying with event type '{event_type}'")
    return jsonify(processed), 200, response_headers


if __name__ == '__main__':
    logging.info(f"Service starting on port {APP_PORT}")
    app.run(host='0.0.0.0', port=APP_PORT, debug=True)
