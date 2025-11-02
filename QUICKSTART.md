# Knative Eventing Learning Demo - Quick Start

## ✅ Complete Learning System Created!

You now have a **fully functional Knative Eventing demonstration** with **NO paid APIs required**!

### 📦 What's Included:

**8 Services** demonstrating different patterns:
1. **event-producer** - Entry point (SinkBinding pattern)
2. **data-extractor** - Regex-based data extraction (Request-Reply)
3. **content-validator** - Rule-based validation (Conditional Routing)
4. **database-enricher** - PostgreSQL integration (Event Enrichment)
5. **message-router** - Keyword-based routing (Content-Based Routing)
6. **finance-handler** - Finance inbox with UI (Event Consumer + SSE)
7. **support-handler** - Support logger (Simple Consumer)
8. **event-monitor** - Real-time dashboard (Wildcard Filtering)

**Plus**: PostgreSQL database with sample customer data

---

## 🚀 Quick Start

### Step 1: Configure Registry

```bash
cd knative-eventing-learning-demo
cp .env.example .env
# Edit .env and set your Docker Hub username
vim .env
```

### Step 2: Build All Services

```bash
chmod +x build.sh
./build.sh
```

This builds and pushes all 9 container images to your registry.

### Step 3: Deploy to Kubernetes

(K8s manifests coming in next step - want me to create them?)

---

## 📚 What You'll Learn

### Pattern 1: SinkBinding (event-producer)
- Injects Broker URL into pods
- No hardcoded event destinations
- Dynamic event routing

### Pattern 2: Request-Reply (data-extractor, content-validator, etc.)
- Service receives event
- Processes payload
- Replies with new event type
- Broker auto-routes to next step

### Pattern 3: Conditional Routing (content-validator)
- Different event types based on processing result
- Pass/fail routing
- Dead letter queue pattern

### Pattern 4: Event Enrichment (database-enricher)
- Add external data to events
- PostgreSQL integration
- Graceful degradation

### Pattern 5: Content-Based Routing (message-router)
- Route to different consumers
- Multiple subscribers per broker
- Event type filtering

### Pattern 6: Event Consumption (finance-handler, support-handler)
- Terminal consumers
- Real-time UIs
- Server-Sent Events

### Pattern 7: Monitoring (event-monitor)
- Wildcard event filtering
- Observability dashboard
- Event flow visualization

---

## 🧪 Test Scenarios

### Test 1: Happy Path
```bash
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Hi, I need help with my billing. My email is john.smith@globaltech.com"
  }'
```

**Expected Flow:**
1. Event Producer → message.received
2. Data Extractor → message.extracted (finds email)
3. Content Validator → message.validated (passes checks)
4. Database Enricher → message.enriched (finds customer)
5. Message Router → message.routed.finance
6. Finance Handler → appears in inbox UI

### Test 2: Validation Failure
```bash
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{
    "content": "spam spam spam click here for free money"
  }'
```

**Expected:** Routes to review queue (validation-failed)

### Test 3: Unknown Customer
```bash
curl -X POST http://event-producer.demo.example.com \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Help! My email is unknown@test.com"
  }'
```

**Expected:** Routes to review (customer not found)

---

## 🎯 Next Steps

Want me to create:
1. **Kubernetes manifests** (Namespace, Broker, Triggers, Services)?
2. **Deployment script**?
3. **Testing script** with sample requests?
4. **Documentation** on each Knative concept?

Let me know what you'd like next! 🚀
