# Analytics Agent Documentation

## Overview

The **Analytics Agent** is an AI-powered business intelligence system that provides real-time metrics, automated reporting, and predictive analytics for the Project Handler transportation management system.

**Powered by:**
- **LangChain** - Advanced chain-of-thought reasoning
- **Claude AI (Anthropic)** - Natural language insights generation
- **Python 3.11+** - Modern async/await patterns

---

## Features

### 1. **Real-Time Metrics Collection**
- Revenue metrics (total revenue, booking value, growth rate)
- Operational metrics (bookings, completion rates, fleet utilization)
- Customer metrics (satisfaction, retention, acquisition)
- Fleet metrics (vehicle efficiency, maintenance status)

### 2. **AI-Powered Report Generation**
Five specialized report types with AI-generated insights:

- **Performance Reports** - Overall system performance and KPIs
- **Financial Reports** - Revenue analysis and cost optimization
- **Operations Reports** - Fleet efficiency and route optimization
- **Customer Reports** - Satisfaction trends and retention strategies
- **Predictive Reports** - Forecasting and demand predictions

### 3. **Business Intelligence**
- Automated insights with actionable recommendations
- Trend analysis and pattern detection
- Strategic planning support
- Risk identification and mitigation strategies

### 4. **Key Performance Indicators (KPIs)**
Automatically calculated KPIs:
- Revenue per booking
- Customer acquisition cost
- Booking completion rate
- Fleet efficiency
- Customer satisfaction score
- Revenue growth rate

---

## Architecture

### Agent Structure

```python
AnalyticsAgent
├── LangChain Integration
│   ├── ChatAnthropic (Claude model)
│   ├── Prompt Templates (5 specialized)
│   ├── LLM Chains
│   └── Conversation Memory
├── Metrics Collection
│   ├── Revenue metrics
│   ├── Operations metrics
│   ├── Customer metrics
│   └── Fleet metrics
├── Report Generation
│   ├── AI-powered insights
│   ├── Basic fallback insights
│   └── Metrics formatting
└── KPI Calculation
```

### AI Prompt Templates

The agent uses specialized prompt templates for different analysis types:

1. **Performance Analyst Prompt** - System-wide performance analysis
2. **Financial Analyst Prompt** - Revenue and cost analysis
3. **Operations Analyst Prompt** - Fleet and logistics optimization
4. **Customer Success Prompt** - Customer experience and retention
5. **Data Scientist Prompt** - Predictive analytics and forecasting

---

## API Endpoints

### Base URL
```
/api/v1/analytics
```

### Authentication
All endpoints require JWT authentication via Bearer token.

### Endpoints

#### 1. Get Agent Status
```http
GET /api/v1/analytics/status
```

**Response:**
```json
{
  "agent": "analytics",
  "description": "AI-powered analytics, reporting, and business intelligence",
  "status": "initialized",
  "ai_enabled": true,
  "created_at": "2025-11-15T09:00:00Z",
  "last_execution": "2025-11-15T10:00:00Z"
}
```

---

#### 2. Get Metrics
```http
GET /api/v1/analytics/metrics?time_period=daily
```

**Query Parameters:**
- `time_period` (optional): `daily`, `weekly`, `monthly`, `yearly` (default: `daily`)

**Response:**
```json
{
  "timestamp": "2025-11-15T10:00:00Z",
  "time_period": "daily",
  "revenue": {
    "total_revenue": 45000.00,
    "average_booking_value": 150.00,
    "revenue_growth": 12.5,
    "payment_success_rate": 98.5
  },
  "operations": {
    "total_bookings": 300,
    "completed_bookings": 285,
    "completion_rate": 95.0
  },
  "customers": {
    "total_customers": 1200,
    "customer_satisfaction": 4.6,
    "retention_rate": 85.0
  },
  "fleet": {
    "total_vehicles": 25,
    "active_vehicles": 20,
    "average_vehicle_efficiency": 82.0
  }
}
```

---

#### 3. Get KPIs
```http
GET /api/v1/analytics/kpis?time_period=daily
```

**Response:**
```json
{
  "time_period": "daily",
  "kpis": {
    "revenue_per_booking": 150.00,
    "customer_acquisition_cost": 1000.00,
    "booking_completion_rate": 95.0,
    "fleet_efficiency": 82.0,
    "customer_satisfaction": 4.6,
    "revenue_growth": 12.5
  },
  "timestamp": "2025-11-15T10:00:00Z"
}
```

---

#### 4. Generate Report (POST)
```http
POST /api/v1/analytics/reports
```

**Request Body:**
```json
{
  "report_type": "financial",
  "time_period": "monthly",
  "use_ai": true
}
```

**Valid Report Types:**
- `performance`
- `financial`
- `operations`
- `customer`
- `predictive`

**Response:**
```json
{
  "report_type": "financial",
  "time_period": "monthly",
  "generated_at": "2025-11-15T10:00:00Z",
  "metrics": { ... },
  "insights": "Revenue is performing exceptionally well with 12.5% growth...",
  "ai_generated": true,
  "recommendations": [
    "Consider expanding fleet capacity",
    "Optimize pricing strategy for peak hours"
  ]
}
```

---

#### 5. Quick Report Endpoints (GET)

Shortcut endpoints for common reports:

```http
GET /api/v1/analytics/performance?time_period=daily
GET /api/v1/analytics/financial?time_period=monthly
GET /api/v1/analytics/operations?time_period=weekly
GET /api/v1/analytics/customer?time_period=daily
GET /api/v1/analytics/predictive?time_period=yearly
```

---

#### 6. Get AI Insights
```http
POST /api/v1/analytics/insights
```

**Request Body:**
```json
{
  "context": "Focus on revenue optimization strategies"
}
```

**Response:**
```json
{
  "insights": "Based on current performance data, I recommend...",
  "ai_enabled": true,
  "generated_at": "2025-11-15T10:00:00Z"
}
```

---

## Usage Examples

### Python Client

```python
import httpx

# Authentication
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
base_url = "https://project-handler-api.onrender.com/api/v1/analytics"

# Get daily metrics
response = httpx.get(f"{base_url}/metrics?time_period=daily", headers=headers)
metrics = response.json()

# Generate financial report
report_request = {
    "report_type": "financial",
    "time_period": "monthly",
    "use_ai": True
}
response = httpx.post(f"{base_url}/reports", json=report_request, headers=headers)
report = response.json()

print(f"Insights: {report['insights']}")
```

### JavaScript/TypeScript

```typescript
const API_URL = 'https://project-handler-api.onrender.com/api/v1/analytics';
const headers = { 'Authorization': 'Bearer YOUR_JWT_TOKEN' };

// Get KPIs
const response = await fetch(`${API_URL}/kpis?time_period=weekly`, { headers });
const kpis = await response.json();

console.log('KPIs:', kpis.kpis);

// Generate performance report
const reportResponse = await fetch(`${API_URL}/performance?time_period=daily`, {
  headers
});
const report = await reportResponse.json();

console.log('AI Insights:', report.insights);
```

### cURL

```bash
# Get metrics
curl -X GET "https://project-handler-api.onrender.com/api/v1/analytics/metrics?time_period=daily" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Generate report
curl -X POST "https://project-handler-api.onrender.com/api/v1/analytics/reports" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "financial",
    "time_period": "monthly",
    "use_ai": true
  }'
```

---

## Configuration

### Environment Variables

```bash
# Required for AI features
ANTHROPIC_API_KEY=your_claude_api_key_here

# Optional - defaults provided
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### AI Model Configuration

The agent uses **Claude 3 Sonnet** by default with:
- `temperature=0.3` (focused, analytical responses)
- `max_tokens=2048` (comprehensive insights)

To customize:

```python
# In src/agents/analytics.py
self.llm = ChatAnthropic(
    model="claude-3-opus-20240229",  # For longer, more detailed analysis
    temperature=0.5,  # For more creative insights
    max_tokens=4096  # For very detailed reports
)
```

---

## AI Features

### When AI is Enabled (with API key)

- ✅ Natural language insights
- ✅ Context-aware analysis
- ✅ Actionable recommendations
- ✅ Trend interpretation
- ✅ Strategic planning support

### Fallback (without API key)

- ✅ Real-time metrics collection
- ✅ KPI calculation
- ✅ Basic numerical insights
- ⚠️ No AI-generated text insights

---

## Performance Considerations

### Caching
- Metrics are cached by time period
- Reduces redundant database queries
- Improves response times

### Async Operations
- All methods use async/await
- Non-blocking I/O
- Concurrent request handling

### Rate Limiting
- Recommended: Implement rate limiting for AI endpoints
- Claude API has usage limits
- Monitor API costs

---

## Error Handling

### Common Errors

**ValidationError**
```json
{
  "detail": "Invalid report type. Must be one of: [performance, financial, ...]"
}
```

**Agent Execution Error**
```json
{
  "detail": "Error generating report: AI service unavailable"
}
```

### Best Practices

1. Always check `ai_enabled` flag in responses
2. Handle graceful degradation when AI is unavailable
3. Validate time periods before requests
4. Implement retry logic for transient failures

---

## Testing

### Run Unit Tests

```bash
# Test Analytics Agent
pytest tests/unit/test_analytics_agent.py -v

# With coverage
pytest tests/unit/test_analytics_agent.py --cov=src.agents.analytics
```

### Run Integration Tests

```bash
# Test Analytics API
pytest tests/integration/test_analytics_api.py -v
```

### Example Test

```python
import pytest
from src.agents.analytics import AnalyticsAgent

@pytest.mark.asyncio
async def test_generate_financial_report():
    agent = AnalyticsAgent()

    report = await agent.generate_report(
        report_type="financial",
        time_period="monthly",
        use_ai=False
    )

    assert report["report_type"] == "financial"
    assert "insights" in report
    assert "metrics" in report
```

---

## Roadmap

### Current Features (v0.1.0)
- ✅ Real-time metrics collection
- ✅ AI-powered report generation
- ✅ KPI calculation
- ✅ 5 specialized report types
- ✅ RESTful API endpoints

### Planned Features (v0.2.0)
- 🔄 Database integration (replace simulated metrics)
- 🔄 Historical data analysis
- 🔄 Custom date range support
- 🔄 Export reports (PDF, Excel)
- 🔄 Scheduled reports
- 🔄 Email notifications
- 🔄 Dashboard visualizations

### Future Enhancements (v1.0.0)
- 📊 Real-time data streaming
- 📊 Machine learning predictions
- 📊 Anomaly detection
- 📊 Comparative analysis (YoY, MoM)
- 📊 Custom KPI definitions
- 📊 Multi-tenant support

---

## Support

### Documentation
- [Main README](../README.md)
- [API Documentation](https://project-handler-api.onrender.com/docs)
- [Architecture Overview](./architecture.md)

### Issues
Report issues at: https://github.com/yvrah78/HandlerProject/issues

### Contact
For questions: Open a GitHub issue or contact the development team

---

## License

MIT License - See [LICENSE](../LICENSE) for details

---

**Built with ❤️ using Claude AI and LangChain**
