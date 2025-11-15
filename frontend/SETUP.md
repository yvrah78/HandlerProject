# Frontend Setup y Uso

## 🎉 Frontend Funcional - Módulo A1 Completado

El frontend ahora está **100% funcional** y conectado al backend API en producción.

## 🔐 Sistema de Autenticación

### Primera Vez - Registro
1. Abre el frontend: https://project-handler-frontend.onrender.com
2. Verás la página de login
3. Haz clic en "Regístrate aquí"
4. Completa el formulario de registro:
   - Nombre completo
   - Usuario (único)
   - Email (único)
   - Teléfono (opcional)
   - Contraseña (mínimo 6 caracteres)
   - Rol (user o admin)
5. Click en "Registrarse"
6. Automáticamente serás redirigido al login

### Login
1. Ingresa tu usuario y contraseña
2. Click en "Iniciar Sesión"
3. Serás redirigido al dashboard

### Logout
- Click en el botón "Cerrar Sesión" en la esquina superior derecha

## 📋 Funcionalidades Implementadas

### ✅ Dashboard
- Estadísticas en tiempo real
- Contador de Bookings
- Contador de Clientes
- Información del sistema
- Estado de conexión con la API

### ✅ Gestión de Clientes
- **Crear** nuevos clientes con formulario
- **Listar** todos los clientes en tabla
- **Ver** detalles de cada cliente
- **Búsqueda** y filtros
- **Paginación** automática

### ✅ Gestión de Bookings
- **Crear** nuevos bookings con formulario
- **Listar** todos los bookings en tabla
- **Ver** detalles de cada booking
- **Filtros** por cliente y estado
- **Paginación** automática
- **Número de booking** único auto-generado

### ✅ Sistema Multi-Agente (Demo)
- Prueba de agentes (actualmente en modo demo)
- Se implementará completamente en módulos AI1-AI4

## 🔌 Conexión con Backend

El frontend se conecta automáticamente al backend según el entorno:

- **Producción**: https://project-handler-api.onrender.com
- **Local**: http://localhost:8000

## 🎨 Características UI/UX

- ✅ Diseño responsive
- ✅ Notificaciones toast
- ✅ Loading states
- ✅ Manejo de errores
- ✅ Validación de formularios
- ✅ Badges de estado
- ✅ Tablas interactivas

## 🧪 Flujo de Prueba Completo

### 1. Crear un Cliente
```
Nombre: Juan Pérez
Email: juan@example.com
Teléfono: +1234567890
Empresa: Mi Empresa S.A.
Dirección: Calle Principal 123
```

### 2. Crear un Booking
```
ID Cliente: 1 (el cliente que acabas de crear)
Origen: 123 Main St, New York
Destino: 456 Oak Ave, Boston
Fecha/Hora: [selecciona fecha futura]
Peso: 500 kg
Descripción: Paquetes electrónicos
```

### 3. Verificar Datos
- Ve al Dashboard y verifica que los contadores se actualizaron
- Ve a la sección de Bookings y verifica que aparece tu booking
- Ve a la sección de Clientes y verifica que aparece tu cliente

## 🔧 Tecnologías Utilizadas

- **Vanilla JavaScript** (ES6+)
- **Fetch API** para comunicación con backend
- **LocalStorage** para JWT token
- **CSS moderno** con variables CSS
- **Responsive Design**

## 📝 Estructura del Código

```
frontend/public/
├── index.html       # Estructura HTML
├── app.js           # Lógica completa de la aplicación
└── styles.css       # Estilos y diseño
```

## 🔐 Seguridad

- ✅ JWT Authentication
- ✅ Token almacenado en localStorage
- ✅ Auto-refresh de token
- ✅ Protección de rutas
- ✅ Manejo de sesión expirada
- ✅ Validación de formularios

## 🐛 Debugging

Abre la consola del navegador para ver:
- Estado de autenticación
- URL del API backend
- Logs de operaciones
- Errores de API

## 📞 Próximos Módulos

- **AI1-AI4**: Implementación completa de agentes inteligentes
- **F5**: Más endpoints y funcionalidades
- **Optimización**: Performance y UX mejoradas
