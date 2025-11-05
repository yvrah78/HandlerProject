# Project Handler - Frontend Simple

Frontend básico HTML/JavaScript para interactuar con el sistema Project Handler.

## 🚀 Inicio Rápido

### Opción 1: Usar el servidor Python incluido (Recomendado)

```bash
# Desde el directorio raíz del proyecto
cd frontend
python server.py

# El frontend estará disponible en:
# http://localhost:3000
```

### Opción 2: Usar Python http.server directamente

```bash
cd frontend/public
python -m http.server 3000

# Abre http://localhost:3000 en tu navegador
```

### Opción 3: Usar cualquier servidor web

```bash
# Con Node.js
cd frontend/public
npx http-server -p 3000

# Con PHP
cd frontend/public
php -S localhost:3000
```

## ⚠️ Requisito Importante

**El backend API debe estar corriendo** en `http://localhost:8000`

```bash
# En otra terminal, desde el directorio raíz:
uvicorn src.api.main:app --reload
```

## 📱 Características del Frontend

### Dashboard Principal
- Vista general del sistema
- Estadísticas en tiempo real (preparadas para datos reales)
- Información del sistema
- Quick actions para operaciones comunes

### Gestión de Bookings
- Formulario para crear nuevos bookings
- Campos: origen, destino, fecha/hora, peso, descripción
- Vista preparada para listar bookings existentes

### Gestión de Clientes
- Formulario para crear nuevos clientes
- Campos: nombre, email, teléfono, empresa, dirección
- Vista preparada para listar clientes existentes

### Sistema Multi-Agente
- Visualización de los 5 agentes del sistema
- Botones para probar cada agente individualmente
- Visualización de resultados en JSON

### Documentación API
- Enlaces directos a Swagger UI y ReDoc
- Lista de endpoints disponibles

## 🔌 Conexión con la API

El frontend se conecta automáticamente a `http://localhost:8000`

### Endpoints Utilizados

**Actuales (funcionan ahora):**
- `GET /` - Información de la API
- `GET /info` - Información del sistema
- `GET /api/v1/health` - Health check

**Futuros (Módulo F4):**
- `POST /api/v1/bookings` - Crear booking
- `GET /api/v1/bookings` - Listar bookings
- `POST /api/v1/customers` - Crear cliente
- `GET /api/v1/customers` - Listar clientes

**Agentes (Módulos AI1-AI4):**
- `POST /api/v1/agents/{agent_name}/execute` - Ejecutar agente

## 📋 Estado Actual

### ✅ Implementado
- Estructura HTML completa
- Estilos CSS modernos y responsive
- Navegación entre páginas
- Verificación de estado de la API
- Carga de información del sistema
- Formularios funcionales (frontend)
- Sistema de notificaciones (toasts)
- Diseño responsive

### 🔄 Pendiente (próximos módulos)
- Conexión real con endpoints de CRUD (Módulo F4)
- Autenticación de usuarios (Módulo F3)
- Ejecución real de agentes (Módulos AI1-AI4)
- Listado y edición de datos
- Métricas y gráficas (Módulo A2)

## 🎨 Tecnologías

- **HTML5** - Estructura semántica
- **CSS3** - Estilos modernos con variables CSS
- **JavaScript Vanilla** - Sin frameworks, puro JS
- **Fetch API** - Comunicación con el backend

## 🖼️ Navegación

El frontend tiene 5 páginas principales:

1. **Dashboard** - Vista general del sistema
2. **Bookings** - Gestión de reservas
3. **Clientes** - Gestión de clientes
4. **Agentes** - Sistema multi-agente
5. **API** - Documentación de la API

## 🐛 Troubleshooting

### El frontend no carga
- Verifica que estés en el directorio correcto
- Asegúrate de que el puerto 3000 no esté en uso

### "API Desconectada"
- Verifica que el backend esté corriendo en `http://localhost:8000`
- Ejecuta: `uvicorn src.api.main:app --reload`
- Verifica en el navegador: `http://localhost:8000/api/v1/health`

### CORS errors
- El servidor Python incluido maneja CORS automáticamente
- Si usas otro servidor, asegúrate de que soporte CORS

### Los formularios no guardan datos
- **Esto es normal** - Los endpoints de CRUD se implementarán en el Módulo F4
- Por ahora, los formularios muestran una notificación demo
- Los datos se muestran en la consola del navegador (F12)

## 📝 Notas

- Este es un **frontend básico funcional** para desarrollo
- El frontend completo profesional se desarrollará en el **Módulo A1**
- Usa este frontend para probar y visualizar el sistema durante el desarrollo
- Todos los datos son demo hasta que se implementen los endpoints reales

## 🔜 Próximos Pasos

1. **Módulo F2** - Implementar modelos de datos completos
2. **Módulo F3** - Agregar autenticación
3. **Módulo F4** - Implementar endpoints CRUD
4. **Módulos AI1-AI4** - Implementar agentes inteligentes
5. **Módulo A1** - Frontend profesional con Next.js

---

**Para más información, consulta el README principal del proyecto.**
