-- Sample customer data for testing
-- These are fictional customers for the Knative Eventing learning demo

INSERT INTO customers (email, first_name, last_name, company_name, country, phone, account_status, total_purchases, last_purchase_date) VALUES
('john.smith@globaltech.com', 'John', 'Smith', 'Global Tech Solutions', 'USA', '+1-555-0101', 'active', 15750.50, '2024-10-15'),
('jane.doe@example.com', 'Jane', 'Doe', 'Example Corp', 'USA', '+1-555-0102', 'active', 8920.00, '2024-10-20'),
('alice.johnson@acme.com', 'Alice', 'Johnson', 'Acme Industries', 'Canada', '+1-555-0103', 'active', 25400.75, '2024-11-01'),
('bob.wilson@techstart.io', 'Bob', 'Wilson', 'TechStart Inc', 'UK', '+44-20-1234-5678', 'active', 5230.00, '2024-09-28'),
('carol.brown@innovate.co', 'Carol', 'Brown', 'Innovate Co', 'Australia', '+61-2-9876-5432', 'active', 12100.25, '2024-10-18'),
('david.lee@startup.com', 'David', 'Lee', 'Startup Ventures', 'Singapore', '+65-6123-4567', 'active', 18950.00, '2024-10-25'),
('emma.davis@enterprise.net', 'Emma', 'Davis', 'Enterprise Solutions', 'Germany', '+49-30-12345678', 'active', 31500.00, '2024-10-30'),
('frank.miller@consulting.biz', 'Frank', 'Miller', 'Miller Consulting', 'USA', '+1-555-0104', 'active', 9870.50, '2024-10-12'),
('grace.taylor@design.studio', 'Grace', 'Taylor', 'Taylor Design Studio', 'France', '+33-1-23-45-67-89', 'active', 6420.00, '2024-09-15'),
('henry.anderson@agency.io', 'Henry', 'Anderson', 'Anderson Agency', 'USA', '+1-555-0105', 'active', 14200.75, '2024-10-22'),
('isabel.martinez@media.com', 'Isabel', 'Martinez', 'Martinez Media Group', 'Spain', '+34-91-123-4567', 'active', 7890.00, '2024-10-05'),
('jack.robinson@finance.co', 'Jack', 'Robinson', 'Robinson Financial', 'USA', '+1-555-0106', 'suspended', 0.00, '2024-08-10'),
('karen.white@logistics.net', 'Karen', 'White', 'White Logistics', 'Netherlands', '+31-20-123-4567', 'active', 22350.25, '2024-10-28'),
('liam.harris@ecommerce.shop', 'Liam', 'Harris', 'Harris E-commerce', 'Canada', '+1-555-0107', 'active', 11200.00, '2024-10-19'),
('maria.garcia@healthcare.org', 'Maria', 'Garcia', 'Garcia Healthcare', 'USA', '+1-555-0108', 'active', 19800.50, '2024-10-26'),
('nathan.clark@education.edu', 'Nathan', 'Clark', 'Clark Education Services', 'UK', '+44-20-9876-5432', 'active', 3450.00, '2024-09-22'),
('olivia.lewis@nonprofit.org', 'Olivia', 'Lewis', 'Lewis Foundation', 'USA', '+1-555-0109', 'active', 0.00, '2024-06-15'),
('peter.walker@manufacturing.com', 'Peter', 'Walker', 'Walker Manufacturing', 'Japan', '+81-3-1234-5678', 'active', 42100.00, '2024-10-31'),
('quinn.hall@research.lab', 'Quinn', 'Hall', 'Hall Research Lab', 'USA', '+1-555-0110', 'active', 8750.25, '2024-10-08'),
('rachel.young@marketing.agency', 'Rachel', 'Young', 'Young Marketing', 'Australia', '+61-3-9876-5432', 'active', 13450.00, '2024-10-24')
ON CONFLICT (email) DO NOTHING;
