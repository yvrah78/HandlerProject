# 🔧 GUÍA DETALLADA: Configurar Variables de Entorno en Render

## Paso 2.4 - Variables de Entorno (EXPLICADO PASO A PASO)

Cuando estés en la pantalla de configuración del Web Service, verás algo como esto:

```
Name: project-handler-api
Region: Oregon
Branch: (tu rama)
Root Directory: (vacío)
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT

Instance Type: Free

[Advanced] ← AQUÍ HAZ CLICK
```

---

## 📍 UBICACIÓN EXACTA DEL BOTÓN "Advanced"

**El botón "Advanced"** está ubicado:
- Justo DEBAJO de "Instance Type: Free"
- ANTES del botón azul "Create Web Service"
- Es un texto pequeño que dice "Advanced" (puede tener un ícono de flecha ▼)

### Si no ves "Advanced":
- Scroll hacia abajo en la página
- Busca después de la sección "Instance Type"
- Está colapsado por defecto

---

## 🎯 DESPUÉS DE HACER CLICK EN "Advanced"

Cuando hagas click en "Advanced", se expandirá una sección grande con estas pestañas/secciones:

```
┌─────────────────────────────────────────────────┐
│ ▼ Advanced                                      │
├─────────────────────────────────────────────────┤
│                                                 │
│ 🔹 Environment Variables                        │
│ 🔹 Secret Files                                 │
│ 🔹 Disk                                         │
│ 🔹 Docker                                       │
│ 🔹 Health Check Path                            │
│ 🔹 Auto-Deploy                                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**Lo que necesitas está en la PRIMERA opción: "Environment Variables"**

---

## 📝 PASO A PASO: Agregar Variables de Entorno

### PASO 1: Localizar "Environment Variables"

En la sección expandida de "Advanced", busca:
```
🔹 Environment Variables
   Add Environment Variable [+ Add Environment Variable]
```

### PASO 2: Hacer Click en "+ Add Environment Variable"

Verás dos campos que aparecen:
```
┌──────────────────────────────────────┐
│ Key:   [___________________]         │
│ Value: [___________________]         │
│        [x Remove]                    │
└──────────────────────────────────────┘
```

### PASO 3: Agregar la Primera Variable

**En el campo "Key"** escribe exactamente:
```
PYTHON_VERSION
```

**En el campo "Value"** escribe exactamente:
```
3.11.0
```

Se verá así:
```
Key:   PYTHON_VERSION
Value: 3.11.0
```

### PASO 4: Agregar Otra Variable

Haz click NUEVAMENTE en "+ Add Environment Variable"

Aparecerán otros dos campos debajo del primero:

```
Key:   PYTHON_VERSION
Value: 3.11.0

Key:   [___________________]  ← NUEVO
Value: [___________________]  ← NUEVO
```

**En el nuevo "Key"** escribe:
```
ENVIRONMENT
```

**En el nuevo "Value"** escribe:
```
production
```

### PASO 5: Continuar Agregando Variables

Repite el proceso haciendo click en "+ Add Environment Variable" para cada una:

**Variable 3:**
```
Key:   DEBUG
Value: false
```

**Variable 4:**
```
Key:   ANTHROPIC_API_KEY
Value: (déjalo VACÍO por ahora - solo presiona el campo y déjalo en blanco)
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

## ✅ VERIFICACIÓN

Después de agregar todas las variables, deberías ver algo como:

```
Environment Variables

Key: PYTHON_VERSION          Value: 3.11.0            [x Remove]
Key: ENVIRONMENT             Value: production        [x Remove]
Key: DEBUG                   Value: false             [x Remove]
Key: ANTHROPIC_API_KEY       Value:                   [x Remove]
Key: TWILIO_ACCOUNT_SID      Value:                   [x Remove]
Key: TWILIO_AUTH_TOKEN       Value:                   [x Remove]
Key: SENDGRID_API_KEY        Value:                   [x Remove]
Key: STRIPE_SECRET_KEY       Value:                   [x Remove]
Key: GOOGLE_MAPS_API_KEY     Value:                   [x Remove]

[+ Add Environment Variable]
```

---

## ⚠️ IMPORTANTE: NO agregues DATABASE_URL ni REDIS_URL todavía

**¿Por qué?** Porque primero necesitas CREAR la base de datos y Redis.

**Orden correcto:**
1. ✅ Agregar las variables que acabamos de poner arriba
2. ❌ NO crear el Web Service todavía
3. ➡️ IR AL PASO 2.4.1 (crear PostgreSQL primero)
4. ➡️ IR AL PASO 2.4.2 (crear Redis después)
5. ➡️ VOLVER y agregar DATABASE_URL y REDIS_URL
6. ✅ ENTONCES SÍ crear el Web Service

---

## 🎯 DESPUÉS DE AGREGAR ESTAS VARIABLES

**NO hagas click en "Create Web Service" todavía.**

En su lugar:
1. Deja esta pestaña abierta
2. Abre una NUEVA pestaña en tu navegador
3. Ve al Dashboard de Render en esa nueva pestaña
4. Sigue el PASO 2.4.1 (crear PostgreSQL)

---

## 🗄️ PASO 2.4.1 - Crear PostgreSQL (BASE DE DATOS)

### EN UNA NUEVA PESTAÑA:

1. Ve al Dashboard de Render: https://dashboard.render.com

2. En la parte superior derecha, busca el botón azul **"New +"**

3. Haz click en "New +" → Se abre un menú dropdown

4. Selecciona **"PostgreSQL"** (tiene un ícono de elefante 🐘)

5. Se abre una nueva página. Llena los campos:

```
Name: project-handler-db
Database: project_handler
User: (déjalo automático)
Region: Oregon (o la misma que elegiste para el Web Service)
PostgreSQL Version: 16 (o la más reciente)
Datadog API Key: (déjalo vacío)

Instance Type: Free
```

6. Scroll hacia abajo y haz click en el botón azul **"Create Database"**

7. Espera 1-2 minutos. Verás una barra de progreso.

8. Cuando esté listo, verás "Available" en verde.

### COPIAR LA URL DE LA BASE DE DATOS:

9. En la página de la base de datos que acabas de crear, busca la sección **"Connections"**

10. Verás varios campos con URLs. Busca específicamente:
```
Internal Database URL
postgresql://project_handler_user:xxxxxxxxxxxx@dpg-xxxxx/project_handler
```

11. Haz click en el ícono de **"Copy"** (📋) al lado de "Internal Database URL"

⚠️ **IMPORTANTE:** Copia la "Internal Database URL", NO la "External Database URL"

### VOLVER AL WEB SERVICE Y AGREGAR LA VARIABLE:

12. Vuelve a la pestaña donde estabas configurando el Web Service

13. En la sección "Environment Variables", haz click en "+ Add Environment Variable"

14. Agrega:
```
Key:   DATABASE_URL
Value: (pega la URL que copiaste - debe empezar con postgresql://)
```

15. Verifica que se pegó completa (puede ser larga)

---

## 🔴 PASO 2.4.2 - Crear Redis (CACHE)

### EN UNA NUEVA PESTAÑA (O USA LA MISMA DE POSTGRESQL):

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

### COPIAR LA URL DE REDIS:

7. En la página de Redis, busca la sección **"Connections"**

8. Verás:
```
Internal Redis URL
redis://red-xxxxx:6379
```

9. Haz click en el ícono de **"Copy"** (📋) al lado de "Internal Redis URL"

⚠️ **IMPORTANTE:** Copia la "Internal Redis URL", NO la "External Redis URL"

### VOLVER AL WEB SERVICE Y AGREGAR LA VARIABLE:

10. Vuelve a la pestaña del Web Service

11. Haz click en "+ Add Environment Variable"

12. Agrega:
```
Key:   REDIS_URL
Value: (pega la URL que copiaste - debe empezar con redis://)
```

---

## ✅ VERIFICACIÓN FINAL

Ahora deberías tener TODAS estas variables en tu Web Service:

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

## 🚀 AHORA SÍ - CREAR EL WEB SERVICE

**DESPUÉS de tener todas las variables configuradas:**

1. Scroll hacia abajo en la página
2. Busca el botón azul grande **"Create Web Service"**
3. Haz click
4. Espera 3-5 minutos mientras Render despliega tu aplicación

---

## 🎊 RESULTADO

Verás una pantalla con logs scrolleando. Cuando termine, verás:

```
==> Build successful 🎉
==> Deploying...
==> Your service is live 🎉
```

Y tu API estará disponible en:
```
https://project-handler-api.onrender.com
```

---

## ❓ PROBLEMAS COMUNES

### "No encuentro el botón Advanced"
- Scroll hacia abajo después de "Instance Type"
- Está justo antes del botón "Create Web Service"

### "No veo Environment Variables"
- Primero debes hacer click en "Advanced"
- Environment Variables es la primera opción en Advanced

### "La URL de PostgreSQL no funciona"
- Asegúrate de copiar la "Internal" URL, no la "External"
- Debe empezar con `postgresql://`

### "La URL de Redis no funciona"
- Asegúrate de copiar la "Internal" URL, no la "External"
- Debe empezar con `redis://`

### "No puedo pegar en el campo Value"
- Haz click directamente en el campo
- Usa Ctrl+V (Windows/Linux) o Cmd+V (Mac/iPad)
- En iPad: mantén presionado y selecciona "Paste"

---

## 📸 RESUMEN VISUAL

```
1. Scroll hasta encontrar "Advanced" ▼

2. Click en "Advanced"
   → Se expande mostrando opciones

3. En "Environment Variables"
   → Click en "+ Add Environment Variable"

4. Aparecen campos Key y Value
   → Llenar uno por uno

5. Click en "+ Add Environment Variable"
   → Repetir para cada variable

6. Crear PostgreSQL en nueva pestaña
   → Copiar Internal Database URL
   → Volver y agregar como DATABASE_URL

7. Crear Redis en nueva pestaña
   → Copiar Internal Redis URL
   → Volver y agregar como REDIS_URL

8. Verificar que todas las variables estén
   → Click en "Create Web Service"

9. ¡Listo! 🎉
```

---

¿Llegaste hasta aquí? ¿En qué paso específico te encuentras ahora?
