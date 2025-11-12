# 🚀 PROMPT PARA NUEVA SESIÓN DE DESARROLLO - PROJECT HANDLER

**Fecha de creación:** 2025-11-12
**Progreso actual:** 70% (10/15 módulos completados)
**Branch de trabajo:** `claude/instant-quote-system-011CV2iNEUehBWLcFEXoJxC1`

---

## 📋 CONTEXTO DEL PROYECTO

### ¿Qué es Project Handler?

**Project Handler** es un sistema multi-agente de gestión de transporte y logística que integra:
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **AI/Agents:** LangChain + Claude API (pendiente de implementación completa)
- **Integraciones:** Twilio, SendGrid, Stripe, Google Maps, WhatsApp (todas funcionando ✅)
- **Frontend:** HTML/CSS/JS básico (Next.js planeado para el futuro)

### Estado Actual: 70% Completado

**Módulos completados:**
- ✅ **Foundation Layer:** 95% (F1, F2, F3, F4 al 95%)
- ✅ **Integration Layer:** 100% (I1-I5 todas las integraciones funcionando)
- 🔄 **Intelligence Layer:** 20% (estructura básica de agentes, sin lógica avanzada)
- ⏳ **Application Layer:** 0% (pendiente)

---

## 🎉 LO QUE SE COMPLETÓ EN LA ÚLTIMA SESIÓN (2025-11-12)

### Sistema de Cotización Instantánea + Costos de Operación

**Implementación completa de ~1,770 líneas de código:**

#### 1. **PricingService** (`src/services/pricing_service.py`) - 400+ líneas
Motor de cálculo de precios para clientes:
- Precio base: $15 + $1.50/km + $0.35/min
- Multiplicadores por servicio (local, premium, airport, long_distance, express)
- Surge pricing (horario pico 1.3x, fines de semana 1.1x)
- Descuentos (clientes frecuentes, códigos promocionales)
- Extras (pasajeros, equipaje, paradas adicionales)
- Impuestos configurables (8%)
- **Uso de Decimal para precisión financiera**

#### 2. **QuoteService** (`src/services/quote_service.py`) - 450+ líneas
Servicio de cotización instantánea:
- Integración con Google Maps para rutas (distancia + tiempo)
- Cálculo de precios usando PricingService
- Generación de número de cotización único (QT-YYYYMMDD-XXXXX)
- Validez de 24 horas
- Persistencia en base de datos
- **[NUEVO]** Cálculo opcional de costos operativos internos
- **Tiempo de respuesta: <2 segundos ✅**

#### 3. **VehicleOperatingCostService** (`src/services/vehicle_operating_cost_service.py`) - 380+ líneas
**[SOLO PARA USO INTERNO - NO VISIBLE PARA CLIENTES]**

Sistema de análisis de costos operativos reales:
- **Combustible/energía:** Soporte para gasolina, diésel, eléctrico, híbrido, CNG
- **Multiplicadores de tráfico:** Normal (1.0x), ligero (1.1x), medio (1.25x), pesado (1.5x)
- **Mantenimiento:** Neumáticos, frenos, aceite, general (por km)
- **Otros costos:** Depreciación, seguro, peajes
- **Análisis de rentabilidad:** Margen de ganancia y porcentaje

#### 4. **Modelos extendidos:**

**Vehicle** (`src/models/vehicle.py`):
- 30+ campos nuevos para costos operativos
- Tipos de combustible y consumo
- Costos de mantenimiento por km
- Sistema de peajes con descuentos

**Quote** (`src/models/quote.py`):
- Campos internos: `vehicle_id`, `internal_operating_costs`, `profit_margin`, `profit_margin_percent`

#### 5. **Quote API Endpoints** (`src/api/routes/quotes.py`) - 540+ líneas

**Endpoints públicos:**
- `POST /api/v1/quotes/instant` - Cotización instantánea
- `GET /api/v1/quotes/{id}` - Obtener cotización
- `PUT /api/v1/quotes/{id}/accept` - Aceptar cotización
- `PUT /api/v1/quotes/{id}/reject` - Rechazar cotización
- `GET /api/v1/quotes/customer/{id}` - Cotizaciones de cliente
- `GET /api/v1/quotes/pricing/info` - Info de precios

**Endpoints admin (internos):**
- `GET /api/v1/quotes/{id}/internal` - Costos internos y márgenes
- `GET /api/v1/quotes/analytics/profitability` - Análisis de rentabilidad

**⚠️ IMPORTANTE:** Los costos operativos y márgenes son **SOLO INTERNOS**. NUNCA se muestran a clientes.

#### 6. **Tests:**
- ✅ 70+ casos de prueba
- ✅ 9 escenarios de PricingService
- ✅ Validación de tiempo <2 segundos
- ✅ Todos los tests pasando

---

## 🎯 PRÓXIMA TAREA: COMPLETAR F4 (API ENDPOINTS)

### Objetivo

Completar el módulo F4 (API Development) del 95% al 100%.

### Endpoints Pendientes (por orden de prioridad)

#### 1. **Invoice Endpoints** (`src/api/routes/invoices.py`)
**Prioridad:** ALTA

**Endpoints a implementar:**
- `POST /api/v1/invoices` - Crear factura desde booking o quote
- `GET /api/v1/invoices` - Listar facturas (con filtros y paginación)
- `GET /api/v1/invoices/{id}` - Obtener factura por ID
- `PUT /api/v1/invoices/{id}` - Actualizar factura
- `PUT /api/v1/invoices/{id}/status` - Cambiar estado (draft, sent, paid, cancelled)
- `POST /api/v1/invoices/{id}/send` - Enviar por email (SendGrid)
- `GET /api/v1/invoices/{id}/pdf` - Generar y descargar PDF
- `GET /api/v1/invoices/customer/{customer_id}` - Facturas por cliente

**Modelo ya existe:** `src/models/invoice.py` ✅

**Integraciones necesarias:**
- SendGrid (ya funciona) para envío de email
- PDF generation library (instalar: `pip install reportlab` o `weasyprint`)

#### 2. **Vehicle/Fleet Endpoints** (`src/api/routes/vehicles.py`)
**Prioridad:** ALTA

**Endpoints a implementar:**
- `POST /api/v1/vehicles` - Crear vehículo
- `GET /api/v1/vehicles` - Listar vehículos (con filtros: status, type, etc.)
- `GET /api/v1/vehicles/{id}` - Obtener vehículo por ID
- `PUT /api/v1/vehicles/{id}` - Actualizar vehículo
- `DELETE /api/v1/vehicles/{id}` - Eliminar vehículo (soft delete)
- `PUT /api/v1/vehicles/{id}/status` - Cambiar estado (available, in_use, maintenance, out_of_service)
- `GET /api/v1/vehicles/{id}/maintenance-history` - Historial de mantenimiento
- `POST /api/v1/vehicles/{id}/maintenance` - Registrar mantenimiento
- `GET /api/v1/vehicles/{id}/operating-costs` - Obtener costos operativos (usa VehicleOperatingCostService)
- `GET /api/v1/vehicles/{id}/efficiency-score` - Score de eficiencia

**Modelo ya existe:** `src/models/vehicle.py` ✅ (con todos los campos de costos)
**Servicio ya existe:** `src/services/vehicle_operating_cost_service.py` ✅

#### 3. **Driver Endpoints** (`src/api/routes/drivers.py`)
**Prioridad:** MEDIA

**Endpoints a implementar:**
- `POST /api/v1/drivers` - Crear conductor
- `GET /api/v1/drivers` - Listar conductores
- `GET /api/v1/drivers/{id}` - Obtener conductor
- `PUT /api/v1/drivers/{id}` - Actualizar conductor
- `DELETE /api/v1/drivers/{id}` - Eliminar conductor (soft delete)
- `PUT /api/v1/drivers/{id}/status` - Cambiar disponibilidad
- `GET /api/v1/drivers/{id}/bookings` - Bookings del conductor
- `GET /api/v1/drivers/{id}/performance` - Métricas de performance

**Modelo ya existe:** `src/models/driver.py` ✅

#### 4. **Payment Endpoints** (`src/api/routes/payments.py`)
**Prioridad:** ALTA

**Endpoints a implementar:**
- `POST /api/v1/payments/process` - Procesar pago con Stripe
- `GET /api/v1/payments` - Listar pagos
- `GET /api/v1/payments/{id}` - Obtener pago por ID
- `POST /api/v1/payments/{id}/refund` - Procesar reembolso
- `GET /api/v1/payments/invoice/{invoice_id}` - Pagos de una factura
- `GET /api/v1/payments/customer/{customer_id}` - Pagos de un cliente
- `GET /api/v1/payments/{id}/receipt` - Generar recibo

**Modelo ya existe:** `src/models/payment.py` ✅
**Integración ya existe:** `src/integrations/stripe_client.py` ✅

---

## 🛠️ GUÍA DE IMPLEMENTACIÓN

### Pasos Generales para Cada Router

1. **Crear archivo de router:** `src/api/routes/{nombre}.py`

2. **Importaciones básicas:**
```python
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.core.database import get_db
from src.core.logging import get_logger
from src.core.exceptions import ValidationError
from src.models.{modelo} import {Modelo}

logger = get_logger(__name__)
router = APIRouter(prefix="/{plural}", tags=["{nombre}"])
```

3. **Definir Pydantic schemas de request/response**

4. **Implementar endpoints con:**
   - Documentación clara (docstrings)
   - Manejo de errores apropiado
   - Logging de operaciones importantes
   - Validación de entrada
   - Respuestas HTTP apropiadas

5. **Registrar router en `src/api/main.py`:**
```python
from src.api.routes import {nombre}
app.include_router({nombre}.router, prefix="/api/v1")
```

6. **Probar endpoints:**
   - Usar `/docs` (Swagger UI)
   - Verificar todos los casos (success, errors)
   - Validar respuestas

### Ejemplo Completo (Invoice Endpoints)

```python
"""Invoice API endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.invoice import Invoice, InvoiceStatus
from src.integrations.sendgrid_client import SendGridClient

logger = get_logger(__name__)
router = APIRouter(prefix="/invoices", tags=["invoices"])


class InvoiceCreateRequest(BaseModel):
    booking_id: Optional[int] = None
    quote_id: Optional[int] = None
    customer_id: int
    amount: float
    # ... más campos


class InvoiceResponse(BaseModel):
    id: int
    invoice_number: str
    customer_id: int
    status: str
    amount: float
    # ... más campos


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: InvoiceCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new invoice from booking or quote."""
    try:
        # Validar que existe booking o quote
        # Crear invoice
        # Guardar en DB
        # Retornar
        pass
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create invoice")


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get invoice by ID."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


# ... más endpoints
```

---

## 📚 RECURSOS Y DOCUMENTACIÓN

### Archivos Clave

**Modelos de datos:**
- `src/models/invoice.py` - Invoice model
- `src/models/vehicle.py` - Vehicle model (con campos de costos)
- `src/models/driver.py` - Driver model
- `src/models/payment.py` - Payment model
- `src/models/booking.py` - Booking model
- `src/models/customer.py` - Customer model

**Servicios existentes:**
- `src/services/booking_service.py` - Booking operations
- `src/services/pricing_service.py` - Price calculations
- `src/services/quote_service.py` - Quote generation
- `src/services/vehicle_operating_cost_service.py` - Vehicle cost analysis

**Integraciones externas:**
- `src/integrations/stripe_client.py` - Stripe payments ✅
- `src/integrations/sendgrid_client.py` - Email sending ✅
- `src/integrations/google_maps_client.py` - Google Maps ✅
- `src/integrations/twilio_client.py` - SMS/Voice ✅
- `src/integrations/whatsapp_client.py` - WhatsApp ✅

**Routers existentes:**
- `src/api/routes/bookings.py` - Booking endpoints ✅
- `src/api/routes/customers.py` - Customer endpoints ✅
- `src/api/routes/auth.py` - Authentication ✅
- `src/api/routes/health.py` - Health checks ✅
- `src/api/routes/quotes.py` - Quote endpoints ✅ (recién implementado)

**Core utilities:**
- `src/core/database.py` - Database connection
- `src/core/logging.py` - Logging setup
- `src/core/exceptions.py` - Custom exceptions
- `src/core/security.py` - JWT and auth utilities

### Documentación del Proyecto

**ARCHIVO PRINCIPAL:** `PROJECT-STATUS.md` - HOJA DE RUTA OFICIAL
- Estado del proyecto: 70% completado
- Módulos completados y pendientes
- Métricas y estadísticas
- Arquitectura del sistema
- Timeline estimado

**Documentación técnica:**
- `docs/architecture.md` - Arquitectura del sistema
- `docs/modules/module-overview.md` - Overview de módulos
- `src/integrations/README.md` - Documentación de integraciones
- API docs: `https://project-handler-api.onrender.com/docs`

---

## 🔧 COMANDOS ÚTILES

### Setup del entorno

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

### Desarrollo

```bash
# Correr servidor de desarrollo
uvicorn src.api.main:app --reload --port 8000

# Correr tests
pytest tests/ -v

# Verificar linting
ruff check src/
black src/

# Ver API docs
# Browser: http://localhost:8000/docs
```

### Base de datos

```bash
# Crear migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Revertir migración
alembic downgrade -1
```

### Git

```bash
# Ver estado
git status

# Branch actual
git branch

# Commit cambios
git add .
git commit -m "feat: descripción del cambio"

# Push a branch remota
git push -u origin claude/instant-quote-system-011CV2iNEUehBWLcFEXoJxC1
```

---

## ⚠️ CONSIDERACIONES IMPORTANTES

### 1. Costos Operativos (INTERNOS)

Los costos operativos calculados por `VehicleOperatingCostService` son **SOLO PARA USO INTERNO** y **NUNCA** deben mostrarse a los clientes.

- ✅ Usar en endpoints admin (con autenticación)
- ❌ NUNCA incluir en responses públicos
- ✅ Documentar claramente como `[INTERNAL USE ONLY]`

### 2. Precisión Financiera

Usar `Decimal` de Python para todos los cálculos monetarios:

```python
from decimal import Decimal

amount = Decimal("19.99")
tax = amount * Decimal("0.08")
total = amount + tax
```

### 3. Async/Await

Los servicios que hacen llamadas a APIs externas (Google Maps, Stripe) deben ser async:

```python
async def create_something(data):
    result = await external_api_client.call(data)
    return result
```

### 4. Manejo de Errores

Siempre capturar y manejar errores apropiadamente:

```python
try:
    result = service.do_something()
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except IntegrationError as e:
    raise HTTPException(status_code=502, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### 5. Logging

Usar el logger configurado:

```python
from src.core.logging import get_logger

logger = get_logger(__name__)

logger.info("Operación exitosa")
logger.warning("Advertencia")
logger.error(f"Error: {str(e)}")
```

### 6. Autenticación (Futuro)

Los endpoints admin deben tener autenticación (pendiente de implementar RBAC):

```python
@router.get("/{id}/internal", tags=["internal"])
async def get_internal_data(
    id: int,
    db: Session = Depends(get_db),
    # TODO: Agregar cuando RBAC esté listo
    # current_user: User = Depends(get_current_admin_user)
):
    """[INTERNAL USE ONLY] Admin endpoint."""
    pass
```

---

## 📊 MÉTRICAS ACTUALES

### Código Implementado

| Categoría | Cantidad | Estado |
|-----------|----------|--------|
| **Modelos de Datos** | 11 | ✅ Completo |
| **Integraciones Externas** | 5 | ✅ Completo |
| **API Endpoints** | 5 routers | 🔄 95% |
| **Servicios** | 4 | ✅ Completo |
| **Agentes** | 6 | ⚠️ Estructura básica |
| **Tests** | 70+ casos | ✅ Completo |

### Servicios Implementados

1. ✅ **BookingService** - Gestión de reservas
2. ✅ **PricingService** - Motor de cálculo de precios
3. ✅ **QuoteService** - Cotización instantánea con Google Maps
4. ✅ **VehicleOperatingCostService** - Análisis de costos operativos (interno)

### Integraciones Funcionando

1. ✅ **Twilio** - SMS, llamadas, MMS
2. ✅ **SendGrid** - Email transaccional y masivo
3. ✅ **Stripe** - Pagos, refunds, customers
4. ✅ **Google Maps** - Geocoding, directions, distance matrix, places
5. ✅ **WhatsApp** - Mensajería via Twilio

---

## 🚀 INICIANDO LA SESIÓN

### Prompt Recomendado

```
Hola! Voy a continuar el desarrollo de Project Handler.

Estado actual: 70% completado (10/15 módulos)

Acabo de leer PROJECT-STATUS.md y NEXT-SESSION-PROMPT.md.

Última implementación completada:
- ✅ Sistema de Cotización Instantánea (<2 segundos)
- ✅ Sistema de Costos Operativos para Vehículos (interno)
- ✅ ~1,770 líneas de código agregadas

Próxima tarea: Completar F4 (API Endpoints)
- Invoice endpoints
- Vehicle/Fleet endpoints
- Driver endpoints
- Payment endpoints

Branch de trabajo: claude/instant-quote-system-011CV2iNEUehBWLcFEXoJxC1

¿Por dónde comenzamos? Sugiero empezar con Invoice endpoints ya que son de prioridad ALTA.
```

---

## 📝 CHECKLIST AL COMPLETAR LA TAREA

Cuando completes los endpoints pendientes:

- [ ] Código implementado y funcionando
- [ ] Schemas Pydantic definidos
- [ ] Manejo de errores completo
- [ ] Logging apropiado
- [ ] Documentación (docstrings)
- [ ] Type hints completos
- [ ] Tests manuales en `/docs`
- [ ] Registrar routers en `main.py`
- [ ] Commit con mensaje descriptivo
- [ ] Push a branch remota
- [ ] Actualizar PROJECT-STATUS.md (progreso a 75-80%)
- [ ] Verificar en Render (si se hace deploy)

---

## 🎯 OBJETIVO FINAL DE ESTA FASE

**Completar F4 (API Development) al 100%**

Una vez completados estos endpoints, el Foundation Layer estará al 100% y podremos pasar a la siguiente gran fase: **Intelligence Layer (AI Agents con LangChain + Claude)**.

---

**¡Buena suerte con el desarrollo! 🚀**

*Última actualización: 2025-11-12*
*Creado por: Project Handler Team*
