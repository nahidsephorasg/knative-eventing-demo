-- Customer Database Schema
-- Educational demo database for Knative Eventing learning

CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    company_name VARCHAR(255),
    country VARCHAR(100),
    phone VARCHAR(50),
    account_status VARCHAR(50) DEFAULT 'active',
    total_purchases DECIMAL(10, 2) DEFAULT 0.00,
    last_purchase_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);

-- Create index on account_status
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(account_status);
