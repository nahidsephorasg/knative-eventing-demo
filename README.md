# Knative Eventing Learning Demo

A **complete educational project** demonstrating Knative Eventing patterns with **NO paid APIs required**. Learn event-driven architecture with Kafka, PostgreSQL, and Knative.

## 🎯 Learning Objectives

This project teaches you:

1. **Knative Eventing Fundamentals**
   - CloudEvents format
   - Brokers and Triggers
   - Event filtering
   - Request-Reply pattern
   - SinkBinding

2. **Event-Driven Architecture Patterns**
   - Event sourcing
   - Saga pattern
   - Content-based routing
   - Dead letter queues
   - Event enrichment

3. **Kubernetes & Knative Integration**
   - Knative Serving (auto-scaling)
   - Kafka integration via Strimzi
   - PostgreSQL integration
   - Real-time dashboards

## 🏗️ Architecture

```
Customer Message (HTTP POST)
    ↓
[Event Producer] → message.received
    ↓
[Data Extractor] → message.extracted (regex-based)
    ↓
[Content Validator] → message.validated (rule-based)
    ↓
[Database Enricher] → message.enriched (PostgreSQL)
    ↓
[Message Router] → message.routed.{finance|support|website} (keyword-based)
    ↓
    ├→ [Finance Handler]
    ├→ [Support Handler]
    └→ [Event Monitor] (watches all events)
```

## 📦 Services Overview

| Service | Purpose | Pattern Demonstrated | API Needed |
|---------|---------|---------------------|------------|
| **event_producer** | Accepts HTTP requests, publishes CloudEvents | SinkBinding, Event Publishing | ❌ None |
| **data_extractor** | Extracts structured data (email, name) | Request-Reply, Regex Processing | ❌ None |
| **content_validator** | Validates content safety | Event Filtering, Conditional Routing | ❌ None |
| **database_enricher** | Enriches with customer data | Database Integration, Event Enrichment | ❌ None |
| **message_router** | Routes based on content | Content-Based Routing | ❌ None |
| **finance_handler** | Handles finance messages | Event Consumer, Web UI | ❌ None |
| **support_handler** | Handles support messages | Event Consumer, Web UI | ❌ None |
| **event_monitor** | Real-time event dashboard | Wildcard Filtering, SSE | ❌ None |

## 🚀 Quick Start

### Prerequisites

1. **Kubernetes cluster** with:
   - Knative Serving
   - Knative Eventing
   - Strimzi (Kafka operator)
   - Knative Kafka Broker

2. **Tools**:
   - `kubectl`
   - `docker`
   - Access to container registry

### Installation

```bash
# 1. Clone and navigate
cd knative-eventing-learning-demo

# 2. Configure your registry
cp .env.example .env
# Edit .env with your Docker Hub username

# 3. Build all services
./scripts/build-all.sh

# 4. Deploy to Kubernetes
./scripts/deploy.sh

# 5. Test the system
./scripts/test.sh
```

## 📚 Learning Scenarios

### Scenario 1: Basic Event Flow
**Learn**: CloudEvents, Broker, Triggers

```bash
# Send a simple message
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello World"}'

# Watch events flow through the system
kubectl port-forward -n knative-demo svc/event-monitor 9999:80
# Open http://localhost:9999
```

### Scenario 2: Data Extraction
**Learn**: Event transformation, Request-Reply pattern

```bash
# Send message with email and name
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hi, my name is John Doe and my email is john@example.com"
  }'

# See extracted data in event monitor
```

### Scenario 3: Content Validation
**Learn**: Conditional routing, Dead letter queue

```bash
# Send message with spam keywords
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Click here for free spam virus phishing"
  }'

# This will be routed to review queue
```

### Scenario 4: Database Enrichment
**Learn**: External system integration, Event enrichment

```bash
# Send message with known customer email
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I need help. My email is john.smith@globaltech.com"
  }'

# Customer data from PostgreSQL will be added to event
```

### Scenario 5: Content-Based Routing
**Learn**: Event filtering, Multiple subscribers

```bash
# Finance message
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{
    "content": "I have a billing issue with my invoice payment"
  }'

# Support message
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The app is broken and I need help troubleshooting"
  }'

# Each routes to different handler
```

## 🔧 Technology Stack

- **Knative Serving** - Serverless deployment
- **Knative Eventing** - Event routing
- **Strimzi** - Kafka operator
- **Kafka** - Event broker
- **PostgreSQL** - Customer database
- **Python/Flask** - Service implementation
- **Docker** - Containerization

## 📖 Documentation

- [Architecture Deep Dive](docs/ARCHITECTURE.md)
- [Knative Concepts](docs/KNATIVE_CONCEPTS.md)
- [Service Details](docs/SERVICES.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

