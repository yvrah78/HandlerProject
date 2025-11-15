# 🔗 GUÍA DE INTEGRACIÓN COMPLETA - Project Handler

## Frontend ↔️ Backend Integration Guide

**Versión:** 1.0  
**Fecha:** 2025-11-15  
**Estado:** Consolidación de ramas AI3 + Frontend

---

## 📊 Resumen de la Consolidación

Este proyecto tiene **DOS integraciones de Claude AI** que se complementan:

### 1. **LangChain Integration** (Alto Nivel)
- **Archivo:** `src/agents/coordinator.py`
- **Uso:** Conversaciones naturales, memoria, prompts estructurados
- **Ventajas:** Fácil de usar, abstracciones altas
- **Cuándo usar:** Chat, NLP, workflows complejos

### 2. **Direct Claude Integration** (Bajo Nivel)
- **Archivo:** `src/integrations/claude_integration.py`
- **Uso:** Control fino, tracking de costos, rate limiting
- **Ventajas:** Performance, control granular, métricas
- **Cuándo usar:** Producción, análisis de costos, optimización

---

## 🎯 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (React/Vanilla JS)             │
│  - Authentication UI                                         │
│  - Customer/Booking Forms                                    │
│  - Chat Interface (AI Agent)                                 │
│  - Dashboard & Analytics                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTPS/REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    BACKEND API (FastAPI)                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Authentication Layer (JWT)                          │   │
│  │  - /api/v1/auth/login                               │   │
│  │  - /api/v1/auth/register                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CRUD Endpoints                                      │   │
│  │  - /api/v1/customers (GET, POST, PUT, DELETE)       │   │
│  │  - /api/v1/bookings (GET, POST, PUT, DELETE)        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  AI Agents Layer                                     │   │
│  │  - /api/v1/agents/coordinator/chat                  │   │
│  │  - /api/v1/agents/coordinator/execute               │   │
│  │  - /api/v1/agents/coordinator/status                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────┬────────────────────────────────┐   │
│  │  LangChain         │  Direct Claude Integration     │   │
│  │  Integration       │  (Low-level)                   │   │
│  │                    │                                 │   │
│  │  - ChatAnthropic   │  - AsyncClaudeAPIClient        │   │
│  │  - Memory          │  - TokenCounter                │   │
│  │  - Prompts         │  - RateLimiter                 │   │
│  │  - Chains          │  - Cost Tracking               │   │
│  └────────────────────┴────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ Anthropic API
                          │
                  ┌───────▼────────┐
                  │  Claude-3.5    │
                  │  Sonnet API    │
                  └────────────────┘
```

---

## 🚀 Flujo de Datos Completo

### Ejemplo: Usuario crea un Booking

```
1. FRONTEND (app.js)
   ↓
   User fills form → Clicks "Crear Booking"
   ↓
   handleBookingSubmit(e)
   ↓
   const bookingData = {
     customer_id: parseInt(document.getElementById('booking_customer_id').value),
     origin: document.getElementById('booking_origin').value,
     destination: document.getElementById('booking_destination').value,
     pickup_datetime: document.getElementById('booking_pickup').value,
     cargo_weight: parseFloat(document.getElementById('booking_weight').value),
     cargo_description: document.getElementById('booking_description').value
   }
   ↓
   await createBooking(bookingData)
   ↓

2. API CALL (app.js - apiCall helper)
   ↓
   fetch(`${API_BASE_URL}/api/v1/bookings`, {
     method: 'POST',
     headers: {
       'Content-Type': 'application/json',
       'Authorization': `Bearer ${auth.getToken()}`  // JWT token
     },
     body: JSON.stringify(bookingData)
   })
   ↓

3. BACKEND (FastAPI)
   ↓
   Router: src/api/routes/bookings.py
   ↓
   @router.post("/", response_model=BookingSchema)
   def create_booking(
     booking_data: BookingCreate,
     db: Session = Depends(get_db),
     current_user: User = Depends(get_current_user)  // JWT validation
   ):
   ↓
   Security check → JWT decoded → User authenticated
   ↓
   Generate booking_number = "BK-20251115-A1B2C3D4"
   ↓
   new_booking = Booking(**booking_data.model_dump(), booking_number=...)
   ↓
   db.add(new_booking)
   db.commit()
   db.refresh(new_booking)
   ↓
   return new_booking (BookingSchema)
   ↓

4. RESPONSE
   ↓
   {
     "id": 1,
     "booking_number": "BK-20251115-A1B2C3D4",
     "customer_id": 1,
     "origin": "123 Main St",
     "destination": "456 Oak Ave",
     "status": "PENDING",
     "created_at": "2025-11-15T10:30:00Z"
   }
   ↓

5. FRONTEND (app.js)
   ↓
   const result = await createBooking(bookingData);
   ↓
   showToast(`Booking creado exitosamente: ${result.booking_number}`, 'success');
   ↓
   await loadBookingsList();  // Reload table
   ↓
   User sees new booking in table ✅
```

---

## 🤖 Flujo de AI Agent

### Ejemplo: Usuario chatea con Coordinator Agent

```
1. FRONTEND (Future - Chat UI)
   ↓
   User types: "I need to create a booking for tomorrow"
   ↓
   await apiCall('/api/v1/agents/coordinator/chat', 'POST', {
     message: userInput,
     data: { customer_id: auth.user.id }
   })
   ↓

2. BACKEND (FastAPI)
   ↓
   Router: src/api/routes/agents.py
   ↓
   @router.post("/coordinator/chat")
   async def chat_with_coordinator(request: ChatRequest, current_user: User):
   ↓
   coordinator = get_coordinator_agent()  // Singleton
   ↓
   input_data = {
     "message": "I need to create a booking for tomorrow",
     "context": {
       "user_id": current_user.id,
       "user_name": current_user.full_name
     }
   }
   ↓
   result = await coordinator.execute(input_data)
   ↓

3. COORDINATOR AGENT (LangChain)
   ↓
   src/agents/coordinator.py
   ↓
   async def _process_natural_language(input_data):
   ↓
   messages = [
     SystemMessage(content=system_prompt),
     HumanMessage(content="User request: I need to create a booking...")
   ]
   ↓
   response = await self.llm.ainvoke(messages)  // Call Claude via LangChain
   ↓
   ai_response = response.content
   ↓
   routing = self._analyze_routing(ai_response, user_message)
   ↓
   return {
     "response": "I can help you create a booking! I need...",
     "routing": {
       "suggested_agents": ["operations"],
       "requires_delegation": false
     }
   }
   ↓

4. ANTHROPIC CLAUDE API
   ↓
   LangChain → ChatAnthropic → Anthropic API
   ↓
   POST https://api.anthropic.com/v1/messages
   {
     "model": "claude-3-sonnet-20240229",
     "max_tokens": 2048,
     "messages": [...]
   }
   ↓
   Response: AI-generated answer
   ↓

5. RESPONSE TO FRONTEND
   ↓
   {
     "success": true,
     "agent": "coordinator",
     "result": {
       "response": "I can help you create a booking...",
       "routing": {...}
     },
     "timestamp": "2025-11-15T10:35:00Z"
   }
   ↓

6. FRONTEND
   ↓
   Display AI response in chat UI
   ↓
   User continues conversation ✅
```

---

## 💰 Cost Tracking Flow (Direct Integration)

```
1. Use AsyncClaudeAPIClient for cost tracking
   ↓
   from src.integrations.claude_integration import get_claude_client
   ↓
   client = get_claude_client()
   ↓
   response = await client.send_message(
     system="You are a helpful assistant",
     user_message="Hello!"
   )
   ↓

2. TokenCounter automatically tracks
   ↓
   client.token_counter.update(
     input_tokens=100,
     output_tokens=50
   )
   ↓

3. Get stats anytime
   ↓
   stats = client.get_stats()
   {
     "token_counter": {
       "total_input_tokens": 100,
       "total_output_tokens": 50,
       "total_tokens": 150,
       "requests": 1
     },
     "estimated_cost_usd": 0.00045
   }
```

---

## 🔐 Autenticación Flow

```
1. Usuario → Registro/Login
   ↓
   POST /api/v1/auth/register
   {
     "username": "testuser",
     "email": "test@example.com",
     "password": "secure123",
     "full_name": "Test User"
   }
   ↓

2. Backend genera JWT
   ↓
   access_token = create_access_token(data={"sub": user.id})
   ↓
   return {"access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...", "token_type": "bearer"}
   ↓

3. Frontend guarda token
   ↓
   localStorage.setItem('auth_token', token)
   ↓

4. Todas las requests incluyen token
   ↓
   headers: {
     'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGc...'
   }
   ↓

5. Backend valida en cada endpoint
   ↓
   current_user: User = Depends(get_current_user)
   ↓
   Decode JWT → Verify → Get user from DB → Return user object
```

---

## 📁 Estructura de Archivos Consolidada

```
HandlerProject/
├── frontend/
│   ├── public/
│   │   ├── index.html          ✅ UI completa
│   │   ├── app.js              ✅ 845 líneas (auth, forms, API calls)
│   │   └── styles.css          ✅ 710 líneas (responsive)
│   └── SETUP.md                ✅ Documentación frontend
│
├── src/
│   ├── agents/
│   │   ├── base_agent.py       ✅ Clase base para agentes
│   │   ├── coordinator.py      ✅ 427 líneas (LangChain)
│   │   ├── communications.py   🔜 Pendiente (AI2)
│   │   ├── financial.py        🔜 Pendiente (AI3)
│   │   ├── operations.py       🔜 Pendiente (AI4)
│   │   └── analytics.py        🔜 Pendiente (AI4)
│   │
│   ├── integrations/
│   │   ├── __init__.py         ✅ Exports
│   │   ├── claude_integration.py  ✅ 395 líneas (de AI3)
│   │   ├── twilio_client.py    ✅ Básico
│   │   └── stripe_client.py    ✅ Básico
│   │
│   ├── api/
│   │   ├── main.py             ✅ FastAPI app
│   │   └── routes/
│   │       ├── auth.py         ✅ Login/Register
│   │       ├── customers.py    ✅ CRUD completo
│   │       ├── bookings.py     ✅ CRUD completo
│   │       ├── agents.py       ✅ 345 líneas (AI endpoints)
│   │       └── health.py       ✅ Health checks
│   │
│   ├── models/
│   │   ├── user.py             ✅ User model
│   │   ├── customer.py         ✅ Customer model
│   │   └── booking.py          ✅ Booking model
│   │
│   └── core/
│       ├── config.py           ✅ Settings
│       ├── database.py         ✅ PostgreSQL
│       ├── security.py         ✅ JWT
│       └── logging.py          ✅ Logger
│
├── tests/
│   ├── test_claude_integration.py  ✅ 269 líneas (de AI3)
│   └── ...
│
├── requirements.txt            ✅ Todas las deps
├── INTEGRATION-GUIDE.md        ✅ Este archivo
└── ROADMAP.md                  ✅ Plan general
```

---

## 🔧 Configuración Completa

### Variables de Entorno

```bash
# .env file

# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-...  # Para Claude AI
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
SENDGRID_API_KEY=SG...
STRIPE_SECRET_KEY=sk_test_...
GOOGLE_MAPS_API_KEY=AIza...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/project_handler
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
ENVIRONMENT=production
DEBUG=false
API_PORT=8000
API_HOST=0.0.0.0
```

---

## 🧪 Testing

### Test Frontend-Backend Integration

```bash
# 1. Start backend
python -m src.api.main

# 2. Open frontend
http://localhost:8000/

# 3. Test flow:
- Register user
- Login
- Create customer
- Create booking
- Chat with AI agent
- Verify all data persists
```

### Test AI Integration

```python
# Test LangChain integration
from src.agents.coordinator import CoordinatorAgent

agent = CoordinatorAgent()
result = await agent.execute({
    "message": "Help me create a booking"
})

# Test Direct integration
from src.integrations.claude_integration import get_claude_client

client = get_claude_client()
response = await client.send_message(
    system="You are a helpful assistant",
    user_message="Hello!"
)
print(client.get_stats())  # See costs
```

---

## 📊 Métricas y Monitoring

### Token Usage Tracking

```python
from src.integrations.claude_integration import get_claude_client

client = get_claude_client()

# After some API calls...
stats = client.get_stats()

print(f"Total tokens: {stats['token_counter']['total_tokens']}")
print(f"Estimated cost: ${stats['estimated_cost_usd']:.4f}")
print(f"Requests: {stats['token_counter']['requests']}")
```

### Rate Limiting

El `RateLimiter` automáticamente controla:
- Max 50 requests por minuto (configurable)
- Sliding window
- Auto-retry con backoff exponencial

---

## 🎯 Próximos Pasos

1. ✅ **Frontend Chat UI** - Interfaz para hablar con el Coordinator Agent
2. 🔜 **AI2: Communications Agent** - Twilio/SendGrid integration
3. 🔜 **AI3: Financial Agent** - Stripe integration
4. 🔜 **AI4: Operations + Analytics** - Google Maps + analytics

---

## 💡 Tips y Best Practices

### Cuándo Usar Qué Integración

**LangChain (coordinator.py):**
- ✅ Conversaciones naturales
- ✅ Workflows complejos
- ✅ Memoria conversacional
- ✅ Prototipado rápido

**Direct Integration (claude_integration.py):**
- ✅ Control de costos
- ✅ Rate limiting
- ✅ Performance crítico
- ✅ Análisis de métricas

### Performance

- Use `AsyncClaudeAPIClient` para concurrencia
- Monitor costos con `TokenCounter`
- Configura rate limits según tu tier de Anthropic
- Cache respuestas frecuentes

### Security

- ✅ Todas las rutas requieren JWT (excepto /auth/*)
- ✅ Nunca expongas API keys en frontend
- ✅ Usa HTTPS en producción
- ✅ Valida todos los inputs

---

## 📞 Soporte

- **Documentación:** Ver `/docs` endpoint
- **Issues:** GitHub Issues
- **API Docs:** https://project-handler-api.onrender.com/docs

---

**Versión consolidada:** Frontend completo + Backend AI avanzado
**Última actualización:** 2025-11-15
