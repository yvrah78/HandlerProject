# 🚀 Guía de Deployment en Render

Esta guía te ayudará a desplegar Project Handler en Render **GRATIS** y accederlo desde cualquier dispositivo, incluyendo tu iPad.

## ⏱️ Tiempo Estimado: 10-15 minutos

---

## 📋 PRE-REQUISITOS

1. ✅ Cuenta de GitHub (ya la tienes)
2. ✅ Código pusheado a GitHub (ya está listo)
3. 🆕 Cuenta en Render.com (gratis, la crearemos ahora)

---

## 🎯 PASO 1: Crear Cuenta en Render

### 1.1 Ve a [https://render.com](https://render.com)

### 1.2 Click en "Get Started" o "Sign Up"

### 1.3 Selecciona "Sign up with GitHub"
- Esto conectará automáticamente tu cuenta de GitHub
- Autoriza a Render para acceder a tus repositorios

---

## 🔧 PASO 2: Deploy del Backend (API)

### 2.1 Desde el Dashboard de Render, click en "New +" → "Web Service"

### 2.2 Conecta tu repositorio:
- Selecciona el repositorio: `HandlerProject`
- Click en "Connect"

### 2.3 Configura el servicio:

**Nombre del servicio:**
```
project-handler-api
```

**Region:**
```
Oregon (US West) - O la más cercana a ti
```

**Branch:**
```
claude/project-handler-initial-setup-011CUq3Aisnmx8JzKSCq3mdX
```

**Root Directory:**
```
(déjalo vacío - usa la raíz del proyecto)
```

**Environment:**
```
Python 3
```

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

**Plan:**
```
Free
```

### 2.4 Variables de Entorno (Environment Variables)

Click en "Advanced" y agrega estas variables:

**VARIABLES BÁSICAS:**
```
PYTHON_VERSION = 3.11.0
ENVIRONMENT = production
DEBUG = false
```

**API KEYS (vacías por ahora para desarrollo):**
```
ANTHROPIC_API_KEY =
TWILIO_ACCOUNT_SID =
TWILIO_AUTH_TOKEN =
SENDGRID_API_KEY =
STRIPE_SECRET_KEY =
GOOGLE_MAPS_API_KEY =
```

---

#### ✅ GUÍA PASO A PASO: Configurar Variables de Entorno

**Ubicación del botón "Advanced":**
- Está ubicado justo DEBAJO de "Instance Type: Free"
- ANTES del botón azul "Create Web Service"
- Es un texto que dice "Advanced" (puede tener un ícono de flecha ▼)
- Si no lo ves, scroll hacia abajo

**Después de hacer click en "Advanced":**

Se expandirá una sección grande con estas opciones:
```
┌─────────────────────────────────────┐
│ ▼ Advanced                          │
├─────────────────────────────────────┤
│ 🔹 Environment Variables            │
│ 🔹 Secret Files                     │
│ 🔹 Disk                             │
│ 🔹 Docker                           │
│ 🔹 Health Check Path                │
│ 🔹 Auto-Deploy                      │
└─────────────────────────────────────┘
```

**Haz click en "Environment Variables"** (la primera opción)

---

#### 📝 AGREGAR VARIABLES - PASO A PASO:

**PASO 1:** En "Environment Variables", busca el botón "+ Add Environment Variable"

**PASO 2:** Aparecerán dos campos:
```
Key:   [___________________]
Value: [___________________]
       [x Remove]
```

**PASO 3:** Agrega las variables UNA POR UNA haciendo click en "+ Add Environment Variable" cada vez:

**Variable 1:**
```
Key:   PYTHON_VERSION
Value: 3.11.0
```

**Variable 2:**
```
Key:   ENVIRONMENT
Value: production
```

**Variable 3:**
```
Key:   DEBUG
Value: false
```

**Variable 4:**
```
Key:   ANTHROPIC_API_KEY
Value: (déjalo VACÍO)
```

**Variable 5:**
```
Key:   TWILIO_ACCOUNT_SID
Value: (vacío)
```

**Variable 6:**
```
Key:   TWILIO_AUTH_TOKEN
Value: (vacío)
```

**Variable 7:**
```
Key:   SENDGRID_API_KEY
Value: (vacío)
```

**Variable 8:**
```
Key:   STRIPE_SECRET_KEY
Value: (vacío)
```

**Variable 9:**
```
Key:   GOOGLE_MAPS_API_KEY
Value: (vacío)
```

---

#### ⚠️ IMPORTANTE: No agregues DATABASE_URL ni REDIS_URL todavía

**Orden correcto:**
1. ✅ Agregar las variables de arriba
2. ❌ NO crear el Web Service todavía
3. ➡️ Ir al PASO 2.4.1 (crear PostgreSQL primero)
4. ➡️ Ir al PASO 2.4.2 (crear Redis después)
5. ➡️ Volver y agregar DATABASE_URL y REDIS_URL
6. ✅ ENTONCES crear el Web Service

---

#### 🗄️ PASO 2.4.1 - Crear PostgreSQL (BASE DE DATOS)

**EN UNA NUEVA PESTAÑA:**

1. Ve al Dashboard de Render: https://dashboard.render.com

2. Haz click en el botón azul **"New +"** (superior derecha)

3. Selecciona **"PostgreSQL"** del menú

4. Llena los campos:
```
Name: project-handler-db
Database: project_handler
User: (déjalo automático)
Region: Oregon (misma que el Web Service)
PostgreSQL Version: 16 (o la más reciente)
Instance Type: Free
```

5. Haz click en **"Create Database"**

6. Espera 1-2 minutos hasta que veas "Available" en verde

**COPIAR LA URL:**

7. En la página de la base de datos, busca la sección **"Connections"**

8. Busca el campo:
```
Internal Database URL
postgresql://project_handler_user:xxxxxxxxxxxx@dpg-xxxxx/project_handler
```

9. ⚠️ **IMPORTANTE:** Copia la "Internal Database URL", NO la "External"

10. Haz click en el ícono **"Copy"** (📋) al lado

**VOLVER AL WEB SERVICE:**

11. Vuelve a la pestaña del Web Service

12. En "Environment Variables", haz click en "+ Add Environment Variable"

13. Agrega:
```
Key:   DATABASE_URL
Value: (pega la URL que copiaste - debe empezar con postgresql://)
```

---

#### 🔴 PASO 2.4.2 - Crear Redis (CACHE)

**EN UNA NUEVA PESTAÑA:**

1. Ve al Dashboard de Render: https://dashboard.render.com

2. Haz click en **"New +"** (botón azul superior derecha)

3. Selecciona **"Redis"** del menú

4. Llena los campos:
```
Name: project-handler-redis
Region: Oregon (misma que el Web Service)
Maxmemory Policy: noeviction
Plan: Free
```

5. Haz click en **"Create Redis"**

6. Espera 1-2 minutos hasta que veas "Available" en verde

**COPIAR LA URL:**

7. En la página de Redis, busca la sección **"Connections"**

8. Busca:
```
Internal Redis URL
redis://red-xxxxx:6379
```

9. ⚠️ **IMPORTANTE:** Copia la "Internal Redis URL", NO la "External"

10. Haz click en el ícono **"Copy"** (📋)

**VOLVER AL WEB SERVICE:**

11. Vuelve a la pestaña del Web Service

12. Haz click en "+ Add Environment Variable"

13. Agrega:
```
Key:   REDIS_URL
Value: (pega la URL que copiaste - debe empezar con redis://)
```

---

#### ✅ VERIFICACIÓN FINAL

Ahora deberías tener TODAS estas variables:

```
✅ PYTHON_VERSION = 3.11.0
✅ ENVIRONMENT = production
✅ DEBUG = false
✅ ANTHROPIC_API_KEY = (vacío)
✅ TWILIO_ACCOUNT_SID = (vacío)
✅ TWILIO_AUTH_TOKEN = (vacío)
✅ SENDGRID_API_KEY = (vacío)
✅ STRIPE_SECRET_KEY = (vacío)
✅ GOOGLE_MAPS_API_KEY = (vacío)
✅ DATABASE_URL = postgresql://project_handler_user:...
✅ REDIS_URL = redis://red-xxxxx:6379
```

---

#### 🚀 CREAR EL WEB SERVICE

**DESPUÉS de tener TODAS las variables configuradas:**

1. Scroll hacia abajo
2. Busca el botón azul grande **"Create Web Service"**
3. Haz click
4. Espera 3-5 minutos mientras Render despliega tu aplicación

Verás logs scrolleando. Cuando termine:
```
==> Build successful 🎉
==> Deploying...
==> Your service is live 🎉
```

Tu API estará disponible en:
```
https://project-handler-api.onrender.com
```

### 2.5 Deploy!

Click en "Create Web Service"

Render comenzará a:
1. Clonar tu repositorio
2. Instalar dependencias
3. Construir el servicio
4. Desplegarlo

**Esto tomará 3-5 minutos.**

### 2.6 Obtén tu URL del Backend

Una vez que el deploy termine (verás "Live" en verde), tu API estará en:

```
https://project-handler-api.onrender.com
```

Prueba que funciona visitando:
```
https://project-handler-api.onrender.com/api/v1/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "service": "project-handler-api"
}
```

---

## 🎨 PASO 3: Deploy del Frontend

### 3.1 Desde el Dashboard, click "New +" → "Static Site"

### 3.2 Conecta el mismo repositorio:
- Selecciona `HandlerProject`
- Click "Connect"

### 3.3 Configura el sitio:

**Nombre:**
```
project-handler-frontend
```

**Branch:**
```
claude/project-handler-initial-setup-011CUq3Aisnmx8JzKSCq3mdX
```

**Build Command:**
```
echo "No build needed"
```

**Publish Directory:**
```
frontend/public
```

**Plan:**
```
Free
```

### 3.4 Deploy!

Click en "Create Static Site"

Esto tomará 1-2 minutos.

### 3.5 Obtén tu URL del Frontend

Una vez listo, tu frontend estará en:

```
https://project-handler-frontend.onrender.com
```

---

## ✅ PASO 4: Verificar que Todo Funciona

### 4.1 Abre el Frontend en tu navegador:
```
https://project-handler-frontend.onrender.com
```

### 4.2 Deberías ver:
- ✅ El dashboard cargando
- ✅ El punto verde (API Conectada) en el sidebar
- ✅ Información del sistema en la página principal

### 4.3 Prueba desde tu iPad:
- Abre Safari
- Ve a: `https://project-handler-frontend.onrender.com`
- ¡Debería funcionar perfectamente!

---

## 🎊 ¡LISTO! URLs FINALES

### 🎨 Frontend (Dashboard):
```
https://project-handler-frontend.onrender.com
```
👆 **USA ESTA DESDE TU iPad**

### 🔧 Backend API:
```
https://project-handler-api.onrender.com
```

### 📖 Documentación API (Swagger):
```
https://project-handler-api.onrender.com/docs
```

---

## ⚠️ IMPORTANTE: Plan Gratuito

El plan gratuito de Render tiene estas características:

### ✅ Ventajas:
- Totalmente gratis
- HTTPS automático
- Deployment automático desde GitHub
- PostgreSQL + Redis incluidos

### ⚠️ Limitaciones:
- **Se "duerme" después de 15 minutos sin actividad**
- Al despertar, toma ~30 segundos en responder
- 750 horas/mes de uso (suficiente para desarrollo)

### 💡 Cómo funciona:
1. Visitas la URL
2. Si estaba dormido, verás "Loading..."
3. Espera 30 segundos
4. La app despierta y funciona normalmente
5. Mientras la uses, permanece activa

### 💰 Para Evitar que se Duerma:
**Opción 1:** Upgrade al plan Paid ($7/mes por servicio)
```
Backend: $7/mes
Frontend: Gratis (los static sites no se duermen)
Total: $7/mes
```

**Opción 2:** Usa un servicio de "keep-alive" gratis:
- [UptimeRobot](https://uptimerobot.com) (ping cada 5 min)
- [Cron-job.org](https://cron-job.org) (ping programado)

---

## 🔄 AUTO-DEPLOYMENT

¡Lo mejor de Render! Cada vez que hagas `git push` a tu rama, Render:
1. Detecta los cambios automáticamente
2. Re-despliega el backend/frontend
3. En 2-3 minutos tienes la nueva versión live

**No necesitas hacer nada más** - solo push a GitHub.

---

## 🐛 TROUBLESHOOTING

### ❌ "Application failed to respond"
- El servicio está despertando
- Espera 30-60 segundos y recarga

### ❌ "API Desconectada" (punto rojo)
- Verifica que el backend esté "Live" en Render
- Revisa las variables de entorno
- Checa los logs: Dashboard → project-handler-api → Logs

### ❌ "Build failed"
- Revisa los logs de build en Render
- Verifica que requirements.txt esté correcto
- Asegúrate de que la rama esté actualizada

### ❌ Frontend carga pero no conecta con API
- Verifica que app.js tenga la URL correcta del backend
- Checa CORS en el backend (ya está configurado)
- Revisa la consola del navegador (F12)

---

## 📞 SOPORTE

Si tienes problemas:
1. Revisa los logs en Render Dashboard
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que DATABASE_URL y REDIS_URL sean las "Internal URLs"

---

## 🎉 ¡DISFRUTA!

Ahora tienes Project Handler desplegado en la nube, accesible desde cualquier dispositivo, ¡incluido tu iPad!

**URLs para compartir:**
- Dashboard: `https://project-handler-frontend.onrender.com`
- API Docs: `https://project-handler-api.onrender.com/docs`

---

**Nota:** Si decides hacer el upgrade a plan pagado más adelante, los nombres de tus servicios permanecerán iguales, solo mejorarás el rendimiento.
