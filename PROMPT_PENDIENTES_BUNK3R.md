# PROMPT_PENDIENTES_BUNK3R-W3B.md

---

## MENÚ DE INICIO
Al iniciar cada sesión, el agente DEBE preguntar:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
¿Qué quieres hacer?
1️⃣ CONTINUAR    → Retomo la siguiente sección pendiente
2️⃣ NUEVO PROMPT → Agrega nueva tarea/funcionalidad  
3️⃣ VER PROGRESO → Muestra estado actual del proyecto
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Esperando tu respuesta...
```

---

## ESTADO GENERAL DEL PROYECTO

| Métrica | Valor |
|---------|-------|
| Proyecto | BUNK3R-W3B |
| Última actualización | 6 Diciembre 2025 |
| Sección actual | 27-29 |
| Total secciones | 3 |
| Completadas | 0 ✅ |
| Pendientes | 3 ⏳ |
| En progreso | 0 🔄 |
| Crítico | 1 🔴 |

---

## REGLAS BASE DEL AGENTE – OBLIGATORIAS

### 1. Comunicación de Progreso
```
INICIO:   "Comenzando sección [X]: [Nombre]"
FIN:      "Completada sección [X]: [Nombre] | Pendientes: [lista]"
ERROR:    "Problema en sección [X]: [Descripción]"
```

### 2. Verificación Obligatoria
Antes de marcar como completado, el agente DEBE:
- [ ] Probar la funcionalidad como usuario real
- [ ] Confirmar que no rompe funcionalidades previas
- [ ] Verificar comportamiento correcto de la UI
- [ ] Revisar logs y consola para errores ocultos
- [ ] Solo marcar completado cuando funcione al 100%

### 3. Normas de Desarrollo
- Código limpio, ordenado y legible
- Comentarios cuando sea adecuado
- Evitar complejidad innecesaria
- Detectar duplicaciones y refactorizar
- Mantener consistencia en estilo y arquitectura

### 4. Normas de Documentación
Actualizar replit.md con:
- Qué se hizo
- Qué falta
- Errores detectados
- Siguientes pasos
- Nuevas dependencias
- Cambios en arquitectura

### 5. Normas de Seguridad
**NO HACER:**
- Eliminar archivos sin confirmación
- Cambios destructivos sin aprobación
- Exponer datos sensibles
- Gestionar API keys en el panel (usar Secrets de Replit)

**OBLIGATORIO:**
- Respaldo antes de cambios mayores
- Validar entradas del usuario
- Mantener integridad del proyecto

---

### 6. ⚠️ REGLA CRÍTICA: TODO DEBE FUNCIONAR AL 100% ⚠️

**PROHIBIDO DEJAR COSAS SIN FUNCIONALIDAD:**
El agente NUNCA debe crear elementos de UI que no funcionen. TODO lo que se implemente DEBE:

1. **Botones:** Cada botón DEBE tener su evento y ejecutar una acción real
2. **Links/Navegación:** Cada link DEBE llevar a una página/sección que EXISTA
3. **Formularios:** Cada formulario DEBE enviar datos al backend correctamente
4. **Modales:** Cada modal DEBE abrirse, cerrarse y funcionar completamente
5. **Tablas:** Los datos DEBEN cargarse de la base de datos real, NO datos mock
6. **Filtros/Búsquedas:** DEBEN filtrar datos realmente, no ser solo visuales
7. **Paginación:** DEBE funcionar con datos reales
8. **Gráficos:** DEBEN mostrar datos reales de la BD
9. **Acciones:** Aprobar, rechazar, banear, etc. DEBEN ejecutarse en el backend
10. **Exportaciones:** DEBEN generar archivos descargables reales

**ANTES DE MARCAR CUALQUIER TAREA COMO COMPLETADA:**
- [ ] Verificar que TODOS los botones funcionan
- [ ] Verificar que TODAS las páginas/secciones existen
- [ ] Verificar que los datos vienen de la BD (no hardcodeados)
- [ ] Verificar que las acciones modifican la BD correctamente
- [ ] Verificar en consola que NO hay errores JS
- [ ] Verificar en logs del servidor que NO hay errores 500
- [ ] Probar cada funcionalidad como usuario real

**SI ALGO NO SE PUEDE IMPLEMENTAR COMPLETAMENTE:**
- Informar al usuario ANTES de crear el elemento
- NO crear botones/links que digan "Próximamente" o no hagan nada
- Mejor no crear el elemento hasta que pueda funcionar

**CERO TOLERANCIA A:**
- Botones que no hacen nada
- Links que llevan a páginas 404
- Formularios que no envían datos
- Tablas con datos falsos/hardcodeados
- Acciones que solo muestran toast pero no ejecutan nada
- Gráficos con datos inventados

---

## SECCIONES DE TRABAJO PENDIENTES

### Leyenda de Estados:
| Símbolo | Significado |
|---------|-------------|
| ✅ | Completado |
| 🔄 | En progreso |
| ⏳ | Pendiente |
| ❌ | Bloqueado/Error |

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 27: PANEL DE ADMINISTRACIÓN COMPLETO ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Agregado:** 6 Diciembre 2025  
**Estado:** PENDIENTE

---

### OBJETIVO PRINCIPAL:
Crear un Panel de Administración profesional y completo que permita al owner/admin tener visibilidad y control TOTAL sobre la plataforma BUNK3R en tiempo real.

---

### ARQUITECTURA DEL PANEL ADMIN

**Acceso:** Solo usuarios con `is_owner = true` o rol `admin`
**Ruta:** `/admin` o sección especial en la app
**Seguridad:** Requiere 2FA + validación de IP

---

## ═══════════════════════════════════════
## FASE 27.1: DASHBOARD PRINCIPAL ⏳
## ═══════════════════════════════════════

**Pantalla de inicio del admin con resumen de TODO**

### 27.1.1 - Métricas en Tiempo Real (Cards superiores)
- [ ] Total de usuarios registrados
- [ ] Usuarios activos HOY
- [ ] Total B3C en circulación
- [ ] Balance Hot Wallet (TON)
- [ ] Transacciones últimas 24h
- [ ] Ingresos del día (comisiones)

### 27.1.2 - Gráficos del Dashboard
- [ ] Gráfico de usuarios nuevos (últimos 30 días)
- [ ] Gráfico de transacciones (últimos 7 días)
- [ ] Gráfico de ingresos por comisiones
- [ ] Gráfico de uso por sección de la app

### 27.1.3 - Actividad Reciente (Feed en vivo)
- [ ] Últimas 10 transacciones
- [ ] Últimos 5 usuarios registrados
- [ ] Últimas alertas del sistema
- [ ] Auto-refresh cada 30 segundos

### 27.1.4 - Alertas Críticas
- [ ] Banner rojo si hay errores del sistema
- [ ] Alerta si hot wallet tiene bajo balance
- [ ] Alerta de retiros pendientes de aprobar
- [ ] Alerta de reportes de contenido sin revisar

---

## ═══════════════════════════════════════
## FASE 27.2: GESTIÓN DE USUARIOS ⏳
## ═══════════════════════════════════════

### 27.2.1 - Lista de Usuarios
- [ ] Tabla paginada con TODOS los usuarios
- [ ] Columnas: ID, Username, Nombre, Email, Fecha registro
- [ ] Columnas: Última conexión, IP, País, Dispositivo
- [ ] Columnas: Balance B3C, Estado (activo/baneado), Verificado
- [ ] Búsqueda por username, ID, IP
- [ ] Filtros: Estado, País, Fecha de registro
- [ ] Ordenar por cualquier columna
- [ ] Exportar a CSV

### 27.2.2 - Detalle de Usuario (al hacer clic)
- [ ] Información completa del perfil
- [ ] Historial de IPs usadas
- [ ] Dispositivos conectados
- [ ] Historial de sesiones
- [ ] Todas las transacciones del usuario
- [ ] Publicaciones del usuario
- [ ] Compras de números virtuales
- [ ] Notas del admin sobre el usuario

### 27.2.3 - Acciones sobre Usuario
- [ ] Banear/Suspender (temporal o permanente)
- [ ] Desbanear
- [ ] Cerrar todas las sesiones activas
- [ ] Ajustar balance B3C manualmente (con razón)
- [ ] Enviar notificación al usuario
- [ ] Agregar nota interna
- [ ] Ver como este usuario (impersonar)

### 27.2.4 - Detección de Fraude
- [ ] Alertas de múltiples cuentas (misma IP)
- [ ] Alertas de cambios de IP frecuentes
- [ ] Alertas de actividad sospechosa
- [ ] Lista de IPs bloqueadas
- [ ] Agregar IP a blacklist

---

## ═══════════════════════════════════════
## FASE 27.3: TRANSACCIONES Y FINANZAS ⏳
## ═══════════════════════════════════════

### 27.3.1 - Dashboard Financiero
- [ ] Total B3C vendidos (histórico)
- [ ] Total TON recibidos
- [ ] Total comisiones ganadas
- [ ] Gráfico de ingresos diarios
- [ ] Gráfico de volumen de transacciones
- [ ] Comparativa mes actual vs anterior

### 27.3.2 - Lista de Transacciones
- [ ] Tabla con TODAS las transacciones
- [ ] Tipos: Compra B3C, Venta B3C, Transferencia P2P, Retiro
- [ ] Columnas: ID, Usuario, Tipo, Monto, Estado, Fecha, TX Hash
- [ ] Filtros: Tipo, Estado, Fecha, Usuario
- [ ] Búsqueda por TX hash o ID
- [ ] Ver detalle de cada transacción
- [ ] Link a TonScan para transacciones blockchain

### 27.3.3 - Compras de B3C
- [ ] Lista de todas las compras
- [ ] Estado: Pendiente, Confirmada, Fallida, Expirada
- [ ] Acreditar manualmente si es necesario
- [ ] Ver wallet de depósito usada
- [ ] Ver transacción en blockchain

### 27.3.4 - Retiros
- [ ] Lista de solicitudes de retiro
- [ ] Estados: Pendiente, Aprobado, Procesado, Rechazado
- [ ] Aprobar retiro (requiere 2FA)
- [ ] Rechazar retiro (con razón)
- [ ] Marcar como procesado
- [ ] Ver historial de retiros procesados

### 27.3.5 - Transferencias P2P
- [ ] Lista de transferencias entre usuarios
- [ ] Ver emisor y receptor
- [ ] Detectar transferencias sospechosas
- [ ] Revertir transferencia (si es necesario)

### 27.3.6 - Estadísticas por Período
- [ ] Selector de rango de fechas
- [ ] Estadísticas del período seleccionado
- [ ] Exportar reporte a CSV/PDF

---

## ═══════════════════════════════════════
## FASE 27.4: WALLETS Y BLOCKCHAIN ⏳
## ═══════════════════════════════════════

### 27.4.1 - Hot Wallet
- [ ] Balance actual en TON (tiempo real)
- [ ] Dirección de la hot wallet
- [ ] Botón para ver en TonScan
- [ ] Historial de transacciones entrantes/salientes
- [ ] Alerta si balance bajo (configurable)

### 27.4.2 - Wallets de Depósito
- [ ] Lista de todas las wallets generadas
- [ ] Estado: Disponible, Asignada, Usada, Consolidada
- [ ] Balance de cada wallet
- [ ] Usuario asignado (si aplica)
- [ ] Consolidar fondos manualmente
- [ ] Consolidar todas las wallets con balance

### 27.4.3 - Pool de Wallets
- [ ] Estadísticas del pool
- [ ] Wallets disponibles vs usadas
- [ ] Generar más wallets (llenar pool)
- [ ] Configurar tamaño mínimo del pool

### 27.4.4 - Historial Blockchain
- [ ] Todas las transacciones on-chain
- [ ] Consolidaciones realizadas
- [ ] Retiros enviados
- [ ] Estado de confirmaciones

---

## ═══════════════════════════════════════
## FASE 27.5: CONTENIDO Y PUBLICACIONES ⏳
## ═══════════════════════════════════════

### 27.5.1 - Moderación de Contenido
- [ ] Lista de publicaciones recientes
- [ ] Publicaciones reportadas (prioridad)
- [ ] Preview del contenido (texto + media)
- [ ] Aprobar publicación
- [ ] Eliminar publicación
- [ ] Advertir al usuario
- [ ] Banear usuario por contenido

### 27.5.2 - Reportes de Contenido
- [ ] Lista de reportes pendientes
- [ ] Ver publicación reportada
- [ ] Ver quién reportó
- [ ] Razón del reporte
- [ ] Resolver reporte (acción tomada)
- [ ] Desestimar reporte

### 27.5.3 - Gestión de Hashtags
- [ ] Hashtags trending actuales
- [ ] Bloquear hashtags inapropiados
- [ ] Promover hashtags manualmente
- [ ] Estadísticas por hashtag

### 27.5.4 - Stories
- [ ] Stories activas
- [ ] Moderar stories
- [ ] Eliminar stories

---

## ═══════════════════════════════════════
## FASE 27.6: NÚMEROS VIRTUALES ⏳
## ═══════════════════════════════════════

### 27.6.1 - Estadísticas VN
- [ ] Total números comprados
- [ ] Ingresos por números virtuales
- [ ] Servicios más usados (WhatsApp, Telegram, etc.)
- [ ] Países más solicitados

### 27.6.2 - Compras de Números
- [ ] Lista de todas las compras VN
- [ ] Estado: Activo, SMS Recibido, Cancelado, Expirado
- [ ] Usuario que compró
- [ ] Servicio y país
- [ ] Costo (B3C)
- [ ] SMS recibidos

### 27.6.3 - Balance SMSPool
- [ ] Balance actual de la API
- [ ] Alerta si balance bajo
- [ ] Link para recargar

---

## ═══════════════════════════════════════
## FASE 27.7: GESTIÓN DE BOTS ⏳
## ═══════════════════════════════════════

### 27.7.1 - Lista de Bots
- [ ] Todos los bots disponibles
- [ ] Nombre, descripción, estado
- [ ] Precio/comisión de cada bot
- [ ] Usuarios usando cada bot

### 27.7.2 - Estadísticas por Bot
- [ ] Usos totales
- [ ] Ingresos generados
- [ ] Usuarios activos
- [ ] Gráfico de uso en el tiempo

### 27.7.3 - Configuración de Bots
- [ ] Activar/desactivar bot
- [ ] Cambiar precio/comisión
- [ ] Editar descripción
- [ ] Ver logs del bot

### 27.7.4 - Ingresos por Bots
- [ ] Total ingresos por bots
- [ ] Desglose por bot
- [ ] Historial de cobros

---

## ═══════════════════════════════════════
## FASE 27.8: LOGS Y AUDITORÍA ⏳
## ═══════════════════════════════════════

### 27.8.1 - Log de Acciones Admin
- [ ] Todas las acciones de administradores
- [ ] Quién, qué, cuándo
- [ ] IP desde donde se hizo
- [ ] Filtrar por admin, acción, fecha

### 27.8.2 - Log de Errores del Sistema
- [ ] Errores con stack traces
- [ ] Nivel: Error, Warning, Critical
- [ ] Fecha y hora
- [ ] Endpoint afectado
- [ ] Marcar como resuelto

### 27.8.3 - Log de Intentos de Login
- [ ] Logins exitosos y fallidos
- [ ] IP, usuario, fecha
- [ ] Detectar intentos de fuerza bruta
- [ ] Bloquear IP automáticamente después de X intentos

### 27.8.4 - Historial de Configuración
- [ ] Cambios en configuración del sistema
- [ ] Quién lo cambió
- [ ] Valor anterior vs nuevo
- [ ] Fecha del cambio

### 27.8.5 - Exportación de Logs
- [ ] Exportar a CSV
- [ ] Exportar a JSON
- [ ] Rango de fechas seleccionable
- [ ] Filtros aplicados

---

## ═══════════════════════════════════════
## FASE 27.9: ANALYTICS Y MÉTRICAS ⏳
## ═══════════════════════════════════════

### 27.9.1 - Usuarios
- [ ] Usuarios activos: Hoy, Esta semana, Este mes
- [ ] Usuarios nuevos por día (gráfico 30 días)
- [ ] Tasa de retención
- [ ] Usuarios por país (tabla con banderas)
- [ ] Usuarios por dispositivo (iOS, Android, Desktop)

### 27.9.2 - Uso de la App
- [ ] Secciones más visitadas
- [ ] Tiempo promedio en la app
- [ ] Horarios pico de actividad (gráfico 24h)
- [ ] Días más activos

### 27.9.3 - Conversión
- [ ] Usuarios que compraron B3C
- [ ] Usuarios que usaron números virtuales
- [ ] Usuarios que publicaron contenido
- [ ] Funnel de conversión

---

## ═══════════════════════════════════════
## FASE 27.10: SOPORTE Y TICKETS ⏳
## ═══════════════════════════════════════

### 27.10.1 - Sistema de Tickets
- [ ] Lista de tickets abiertos
- [ ] Prioridad: Baja, Media, Alta, Urgente
- [ ] Estado: Nuevo, En progreso, Resuelto, Cerrado
- [ ] Asignar ticket a admin
- [ ] Historial de respuestas

### 27.10.2 - Chat con Usuario
- [ ] Responder ticket
- [ ] Adjuntar imágenes
- [ ] Templates de respuestas comunes
- [ ] Cerrar ticket

### 27.10.3 - FAQ Editable
- [ ] Lista de preguntas frecuentes
- [ ] Agregar/editar/eliminar FAQs
- [ ] Ordenar por categoría
- [ ] Publicar/despublicar

### 27.10.4 - Mensajes Masivos
- [ ] Enviar notificación a TODOS los usuarios
- [ ] Enviar a usuarios específicos (filtros)
- [ ] Programar envío
- [ ] Ver historial de envíos

---

## ═══════════════════════════════════════
## FASE 27.11: MARKETPLACE ⏳
## ═══════════════════════════════════════

### 27.11.1 - Productos/Servicios
- [ ] Lista de todos los listings
- [ ] Estado: Activo, Pausado, Eliminado
- [ ] Vendedor
- [ ] Precio, categoría
- [ ] Ventas realizadas

### 27.11.2 - Moderación de Listings
- [ ] Aprobar nuevos listings
- [ ] Rechazar con razón
- [ ] Editar listing (admin)
- [ ] Eliminar listing

### 27.11.3 - Ventas del Marketplace
- [ ] Historial de ventas
- [ ] Comisiones cobradas
- [ ] Disputas activas

### 27.11.4 - Disputas
- [ ] Lista de disputas
- [ ] Ver conversación
- [ ] Resolver a favor de comprador/vendedor
- [ ] Reembolsar

---

## ═══════════════════════════════════════
## FASE 27.12: CONFIGURACIÓN DEL SISTEMA ⏳
## ═══════════════════════════════════════

### 27.12.1 - Precios y Comisiones
- [ ] Precio actual de B3C (ver, NO editar aquí)
- [ ] Comisión por transacción
- [ ] Comisión por retiro
- [ ] Monto mínimo de retiro
- [ ] Monto máximo por transacción

### 27.12.2 - Modo Mantenimiento
- [ ] Activar/desactivar modo mantenimiento
- [ ] Mensaje personalizado para usuarios
- [ ] Permitir acceso solo a admins
- [ ] Programar mantenimiento

### 27.12.3 - Estado del Sistema
- [ ] Estado de la base de datos
- [ ] Estado de conexión a TonCenter API
- [ ] Estado de SMSPool API
- [ ] Uptime del servidor

### 27.12.4 - Variables de Entorno (Solo vista)
- [ ] Ver qué secrets están configurados (SÍ/NO, no el valor)
- [ ] Indicador de secrets faltantes
- [ ] Link a panel de Secrets de Replit para configurar

---

## ═══════════════════════════════════════
## FASE 27.13: NOTIFICACIONES ADMIN ⏳
## ═══════════════════════════════════════

### 27.13.1 - Alertas en el Panel
- [ ] Centro de notificaciones
- [ ] Notificaciones no leídas
- [ ] Marcar como leída
- [ ] Categorías: Transacciones, Seguridad, Sistema, Usuarios

### 27.13.2 - Notificaciones Telegram
- [ ] Notificar al owner cuando:
  - Nueva compra grande (>X TON)
  - Nuevo retiro pendiente
  - Error crítico del sistema
  - Nuevo reporte de contenido
  - Usuario baneado por sistema
  - Hot wallet con balance bajo

### 27.13.3 - Configurar Notificaciones
- [ ] Activar/desactivar cada tipo
- [ ] Definir umbrales (ej: notificar si compra > 10 TON)
- [ ] Horario de no molestar (opcional)

---

## ═══════════════════════════════════════
## FASE 27.14: BACKUP Y MANTENIMIENTO ⏳
## ═══════════════════════════════════════

### 27.14.1 - Backups
- [ ] Último backup realizado
- [ ] Crear backup manual
- [ ] Descargar backup
- [ ] Programar backups automáticos

### 27.14.2 - Estado del Servidor
- [ ] Uso de CPU
- [ ] Uso de memoria RAM
- [ ] Uso de disco
- [ ] Conexiones activas

### 27.14.3 - Acciones de Mantenimiento
- [ ] Limpiar cache
- [ ] Limpiar sesiones expiradas
- [ ] Limpiar logs antiguos
- [ ] Reiniciar servicios

---

## ═══════════════════════════════════════
## FASE 27.15: ACCESO Y SESIONES ⏳
## ═══════════════════════════════════════

### 27.15.1 - Sesiones Activas
- [ ] Lista de sesiones activas de TODOS los usuarios
- [ ] Usuario, IP, Dispositivo, Última actividad
- [ ] Cerrar sesión específica
- [ ] Cerrar TODAS las sesiones de un usuario

### 27.15.2 - Control de IPs
- [ ] Lista de IPs bloqueadas
- [ ] Agregar IP a blacklist
- [ ] Quitar IP de blacklist
- [ ] Whitelist de IPs para admin
- [ ] Ver historial de bloqueos

### 27.15.3 - Forzar Logout
- [ ] Forzar logout de un usuario específico
- [ ] Forzar logout de TODOS los usuarios
- [ ] Excluir admins del logout masivo

---

## ═══════════════════════════════════════
## DISEÑO Y UI DEL PANEL ADMIN
## ═══════════════════════════════════════

### Estilo Visual
- Tema oscuro consistente con el resto de la app
- Sidebar izquierdo con navegación
- Header con búsqueda global y notificaciones
- Cards con métricas
- Tablas responsivas con paginación
- Gráficos con Chart.js o similar
- Iconos SVG consistentes
- Loading states y skeletons

### Navegación del Panel
```
SIDEBAR:
├── Dashboard
├── Usuarios
│   ├── Lista
│   ├── Baneados
│   └── Sesiones
├── Transacciones
│   ├── Todas
│   ├── Compras B3C
│   ├── Retiros
│   └── Transferencias
├── Wallets
│   ├── Hot Wallet
│   ├── Pool de Depósito
│   └── Consolidación
├── Contenido
│   ├── Publicaciones
│   ├── Reportes
│   └── Hashtags
├── Números Virtuales
├── Bots
├── Logs
│   ├── Acciones Admin
│   ├── Errores
│   └── Logins
├── Analytics
├── Soporte
│   ├── Tickets
│   └── FAQ
├── Marketplace
├── Configuración
└── Notificaciones
```

---

## CRITERIOS DE ACEPTACIÓN SECCIÓN 27:

### Funcionalidad
- [ ] Todas las secciones accesibles y funcionales
- [ ] Datos en tiempo real donde corresponda
- [ ] Acciones funcionan correctamente
- [ ] Búsquedas y filtros operativos
- [ ] Exportaciones funcionando

### Seguridad
- [ ] Solo accesible para owner/admin
- [ ] Requiere 2FA para acciones críticas
- [ ] Log de todas las acciones
- [ ] API keys NO expuestas (usar Secrets de Replit)
- [ ] Validación de permisos en backend

### UX/UI
- [ ] Diseño profesional y consistente
- [ ] Responsive en todos los tamaños
- [ ] Loading states apropiados
- [ ] Mensajes de error claros
- [ ] Confirmación antes de acciones destructivas

---

## ARCHIVOS A CREAR/MODIFICAR:

### Backend (app.py o módulo separado)
- Endpoints `/api/admin/*` para todas las operaciones
- Middleware de autenticación admin
- Logging de acciones admin

### Frontend
- `static/js/admin.js` - Lógica del panel admin
- `static/css/admin.css` - Estilos del panel
- `templates/admin.html` o sección en index.html

### Base de Datos
- Tabla `admin_logs` - Log de acciones admin
- Tabla `support_tickets` - Sistema de tickets
- Tabla `blocked_ips` - IPs bloqueadas
- Tabla `system_config` - Configuración del sistema
- Índices para búsquedas rápidas

---

## ORDEN DE IMPLEMENTACIÓN SUGERIDO:

1. **FASE 27.1** - Dashboard Principal (base del panel)
2. **FASE 27.2** - Gestión de Usuarios (crítico para seguridad)
3. **FASE 27.3** - Transacciones y Finanzas (crítico para operación)
4. **FASE 27.4** - Wallets y Blockchain
5. **FASE 27.8** - Logs y Auditoría
6. **FASE 27.15** - Acceso y Sesiones
7. **FASE 27.5** - Contenido y Publicaciones
8. **FASE 27.6** - Números Virtuales
9. **FASE 27.7** - Gestión de Bots
10. **FASE 27.9** - Analytics
11. **FASE 27.10** - Soporte y Tickets
12. **FASE 27.11** - Marketplace
13. **FASE 27.12** - Configuración
14. **FASE 27.13** - Notificaciones Admin
15. **FASE 27.14** - Backup y Mantenimiento

---

**NOTA DE SEGURIDAD:**
Las API keys y secrets NUNCA se mostrarán ni gestionarán desde el panel. 
Solo se mostrará si están configuradas (SÍ/NO) y se proporcionará un link 
al panel de Secrets de Replit para configurarlas de forma segura.

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 28: REDISEÑO COMPLETO DEL PERFIL DE USUARIO ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Agregado:** 6 Diciembre 2025  
**Estado:** PENDIENTE

**Referencia visual:** Ver imagen del perfil actual en `attached_assets/`

---

### OBJETIVO PRINCIPAL:
Rediseñar completamente la pantalla de perfil de usuario para que:
1. Use el mismo estilo visual profesional de la app (colores oscuros + dorado)
2. TODAS las funcionalidades estén implementadas y funcionando
3. Se vea moderno y profesional tipo Instagram/Binance
4. Reorganizar elementos que se ven desordenados

---

### PALETA DE COLORES A USAR (Consistente con la app):
```css
--bg-primary: #0B0E11;      /* Fondo principal */
--bg-secondary: #1E2329;    /* Cards, modales */
--bg-tertiary: #2B3139;     /* Inputs, bordes */
--text-primary: #EAECEF;    /* Texto principal */
--text-secondary: #848E9C;  /* Texto secundario */
--accent-gold: #F0B90B;     /* Dorado - acentos */
--success: #0ECB81;         /* Verde */
--danger: #F6465D;          /* Rojo */
```

---

## ═══════════════════════════════════════
## FASE 28.1: HEADER DEL PERFIL ⏳
## ═══════════════════════════════════════

### 28.1.1 - Avatar Mejorado
- [ ] Avatar circular grande (80-100px)
- [ ] Si tiene foto: mostrar foto real
- [ ] Si no tiene foto: inicial con gradiente dorado
- [ ] Borde dorado sutil alrededor
- [ ] Botón de cámara para cambiar foto (funcional)
- [ ] Preview antes de subir
- [ ] Subida real a Cloudinary/servidor

### 28.1.2 - Información Principal
- [ ] Username (@demo_user) con estilo elegante
- [ ] Nombre completo debajo (si existe)
- [ ] Badge de verificado (si aplica)
- [ ] Badge de DEV_MODE (solo si es developer)
- [ ] Fecha de registro "Miembro desde Dic 2025"

### 28.1.3 - Bio del Usuario
- [ ] Área de biografía editable
- [ ] Máximo 150 caracteres
- [ ] Placeholder si está vacía
- [ ] Links clickeables en bio

---

## ═══════════════════════════════════════
## FASE 28.2: ESTADÍSTICAS DEL PERFIL ⏳
## ═══════════════════════════════════════

### 28.2.1 - Contadores (DEBEN SER CLICKEABLES)
- [ ] **Publicaciones** - Al hacer clic: scroll a grid de publicaciones
- [ ] **Seguidores** - Al hacer clic: abre modal con lista de seguidores
- [ ] **Siguiendo** - Al hacer clic: abre modal con lista de seguidos
- [ ] Números grandes, labels pequeños debajo
- [ ] Formato: 1.2K para miles, 1.5M para millones

### 28.2.2 - Modal de Seguidores/Siguiendo
- [ ] Lista scrolleable de usuarios
- [ ] Avatar + username + nombre
- [ ] Botón Seguir/Dejar de seguir (funcional)
- [ ] Búsqueda dentro del modal
- [ ] Paginación/infinite scroll

---

## ═══════════════════════════════════════
## FASE 28.3: BOTONES DE ACCIÓN ⏳
## ═══════════════════════════════════════

### 28.3.1 - Botón "Editar Perfil" (DEBE FUNCIONAR)
- [ ] Abre modal/pantalla de edición
- [ ] Campos editables:
  - Foto de perfil
  - Nombre
  - Username (con validación de disponibilidad)
  - Bio
  - Ubicación (opcional)
  - Website/link (opcional)
- [ ] Guardar cambios en BD
- [ ] Validaciones en tiempo real
- [ ] Feedback de éxito/error

### 28.3.2 - Botón "Compartir Perfil" (DEBE FUNCIONAR)
- [ ] Genera link del perfil
- [ ] Opciones: Copiar link, Compartir en Telegram
- [ ] QR code del perfil (opcional)
- [ ] Toast de confirmación al copiar

### 28.3.3 - Perfil de OTRO usuario (cuando visitas otro perfil)
- [ ] Botón "Seguir" / "Siguiendo" (toggle funcional)
- [ ] Botón "Mensaje" (si hay sistema de mensajes)
- [ ] Menú de 3 puntos: Reportar, Bloquear, Copiar link

---

## ═══════════════════════════════════════
## FASE 28.4: TABS DE CONTENIDO ⏳
## ═══════════════════════════════════════

### 28.4.1 - Sistema de Tabs
- [ ] Tab 1: Grid de publicaciones (icono grid 3x3)
- [ ] Tab 2: Publicaciones guardadas (icono bookmark) - solo en perfil propio
- [ ] Tab 3: Publicaciones con tags/menciones (icono usuario)
- [ ] Indicador visual de tab activo (línea dorada)
- [ ] Transición suave entre tabs

### 28.4.2 - Grid de Publicaciones
- [ ] Grid 3 columnas responsive
- [ ] Thumbnails cuadrados
- [ ] Overlay con icono si es video
- [ ] Overlay con contador si es carrusel
- [ ] Click abre publicación completa
- [ ] Infinite scroll / paginación
- [ ] Mensaje "Sin publicaciones" si está vacío (con icono elegante)

### 28.4.3 - Publicaciones Guardadas
- [ ] Solo visible en perfil propio
- [ ] Grid igual que publicaciones
- [ ] Mensaje si no hay guardadas

---

## ═══════════════════════════════════════
## FASE 28.5: INFORMACIÓN ADICIONAL ⏳
## ═══════════════════════════════════════

### 28.5.1 - Sección de Wallet (opcional en perfil)
- [ ] Balance B3C visible (si es propio)
- [ ] Link rápido a wallet
- [ ] Oculto en perfiles ajenos

### 28.5.2 - Badges y Logros
- [ ] Badge de verificado
- [ ] Badge de early adopter
- [ ] Badge de top seller (marketplace)
- [ ] Badge de developer
- [ ] Otros badges futuros

### 28.5.3 - Links Externos
- [ ] Website personal
- [ ] Telegram
- [ ] Twitter/X
- [ ] Iconos clickeables

---

## ═══════════════════════════════════════
## FASE 28.6: DISEÑO VISUAL MEJORADO ⏳
## ═══════════════════════════════════════

### 28.6.1 - Layout General
- [ ] Fondo oscuro consistente (#0B0E11)
- [ ] Espaciado uniforme
- [ ] Sin bordes innecesarios
- [ ] Jerarquía visual clara

### 28.6.2 - Tipografía
- [ ] Username: Bold, tamaño grande
- [ ] Nombre: Regular, tamaño medio
- [ ] Stats: Números bold, labels light
- [ ] Bio: Regular, color secundario

### 28.6.3 - Botones
- [ ] Editar perfil: Borde dorado, fondo transparente
- [ ] Compartir: Borde gris, fondo transparente
- [ ] Seguir: Fondo dorado, texto negro
- [ ] Siguiendo: Borde dorado, fondo transparente

### 28.6.4 - Animaciones
- [ ] Transición suave al cambiar tabs
- [ ] Hover effects en botones
- [ ] Loading skeleton mientras carga
- [ ] Fade in de imágenes

---

## ═══════════════════════════════════════
## FASE 28.7: ENDPOINTS BACKEND ⏳
## ═══════════════════════════════════════

### 28.7.1 - Endpoints necesarios
- [ ] `GET /api/profile/:userId` - Obtener perfil
- [ ] `PUT /api/profile` - Actualizar perfil propio
- [ ] `POST /api/profile/avatar` - Subir avatar
- [ ] `GET /api/profile/:userId/followers` - Lista de seguidores
- [ ] `GET /api/profile/:userId/following` - Lista de seguidos
- [ ] `POST /api/follow/:userId` - Seguir usuario
- [ ] `DELETE /api/follow/:userId` - Dejar de seguir
- [ ] `GET /api/profile/:userId/posts` - Publicaciones del usuario

### 28.7.2 - Tablas de BD
- [ ] Verificar tabla `users` tiene campos: bio, website, location
- [ ] Verificar tabla `followers` existe y funciona
- [ ] Verificar tabla `posts` relacionada con usuario

---

## CRITERIOS DE ACEPTACIÓN SECCIÓN 28:

### Funcionalidad
- [ ] Editar perfil guarda cambios en BD
- [ ] Cambiar avatar funciona completamente
- [ ] Seguir/dejar de seguir funciona
- [ ] Contadores se actualizan en tiempo real
- [ ] Modales de seguidores/siguiendo cargan datos reales
- [ ] Grid de publicaciones muestra datos reales
- [ ] Compartir perfil genera link funcional

### Diseño
- [ ] Colores consistentes con el resto de la app
- [ ] Diseño profesional tipo Instagram/Binance
- [ ] Responsive en móvil
- [ ] Sin elementos desordenados o feos
- [ ] Iconos SVG (no emojis)

### Sin errores
- [ ] Todos los botones funcionan
- [ ] No hay errores en consola
- [ ] No hay errores 500 en servidor
- [ ] Todas las páginas/modales existen

---

## ARCHIVOS A MODIFICAR:

### Frontend
- `templates/index.html` - Sección de perfil
- `static/js/app.js` - Lógica del perfil
- `static/css/styles.css` - Estilos del perfil

### Backend
- `app.py` - Endpoints de perfil

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 29: CONFIGURACIÓN COMPLETA DEL USUARIO ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🟡 ALTA  
**Agregado:** 6 Diciembre 2025  
**Estado:** PENDIENTE

---

### OBJETIVO PRINCIPAL:
Rediseñar completamente la pantalla de Configuración/Ajustes del usuario para que:
1. Use el mismo estilo visual profesional de la app (colores oscuros + dorado)
2. TODAS las opciones tengan funcionalidad REAL (no botones muertos)
3. Organización clara por categorías
4. Diseño moderno tipo Telegram/Binance Settings
5. Cada sección lleve a su propia página o modal funcional

---

### PALETA DE COLORES A USAR (Consistente con la app):
```css
--bg-primary: #0B0E11;      /* Fondo principal */
--bg-secondary: #1E2329;    /* Cards, secciones */
--bg-tertiary: #2B3139;     /* Inputs, toggles */
--text-primary: #EAECEF;    /* Texto principal */
--text-secondary: #848E9C;  /* Texto secundario */
--accent-gold: #F0B90B;     /* Dorado - acentos, iconos activos */
--success: #0ECB81;         /* Verde - toggles activos */
--danger: #F6465D;          /* Rojo - eliminar, cerrar sesión */
--border-color: #2B3139;    /* Bordes sutiles */
```

---

## ═══════════════════════════════════════
## FASE 29.1: ESTRUCTURA PRINCIPAL ⏳
## ═══════════════════════════════════════

### 29.1.1 - Header de Configuración
- [ ] Botón de volver (flecha izquierda)
- [ ] Título "Configuración" centrado
- [ ] Fondo oscuro consistente (#0B0E11)

### 29.1.2 - Perfil Mini en la parte superior
- [ ] Avatar del usuario (circular, 50px)
- [ ] Username (@usuario)
- [ ] Nombre completo debajo
- [ ] Flecha para ir al perfil completo
- [ ] Click lleva a la pantalla de perfil

### 29.1.3 - Organización por Categorías
Las opciones se agrupan en cards/secciones visuales:
- [ ] **Cuenta** - Información personal, verificación
- [ ] **Seguridad** - 2FA, dispositivos, contraseña
- [ ] **Privacidad** - Quién puede ver tu contenido
- [ ] **Notificaciones** - Qué alertas recibir
- [ ] **Apariencia** - Tema, idioma
- [ ] **Wallet** - Configuración de billetera
- [ ] **Datos y Almacenamiento** - Caché, descargas
- [ ] **Ayuda** - FAQ, soporte, sobre la app
- [ ] **Cerrar Sesión** - Botón rojo al final

---

## ═══════════════════════════════════════
## FASE 29.2: SECCIÓN CUENTA ⏳
## ═══════════════════════════════════════

**Ruta:** Configuración > Cuenta
**Página separada con opciones de la cuenta**

### 29.2.1 - Información Personal
- [ ] **Foto de perfil** - Click para cambiar (modal con cámara/galería)
- [ ] **Username** - Mostrar actual, opción para cambiar (si permitido)
- [ ] **Nombre** - Editable
- [ ] **Bio** - Editable (máx 150 caracteres)
- [ ] **Fecha de nacimiento** - Opcional
- [ ] **Género** - Opcional (selector)
- [ ] Botón "Guardar cambios" (funcional)

### 29.2.2 - Información de Contacto
- [ ] **Email** - Mostrar si existe, opción para agregar/cambiar
- [ ] Verificación de email (enviar código)
- [ ] **Teléfono** - Opcional, para recuperación

### 29.2.3 - Verificación de Cuenta
- [ ] Estado de verificación (verificado/no verificado)
- [ ] Badge de verificado (si aplica)
- [ ] Botón "Solicitar verificación" (si no está verificado)
- [ ] Requisitos para verificación

### 29.2.4 - Cuenta de Telegram
- [ ] Mostrar ID de Telegram
- [ ] Username de Telegram vinculado
- [ ] Estado: Conectado
- [ ] Información de cuándo se conectó

---

## ═══════════════════════════════════════
## FASE 29.3: SECCIÓN SEGURIDAD ⏳
## ═══════════════════════════════════════

**Ruta:** Configuración > Seguridad
**Página separada con todas las opciones de seguridad**

### 29.3.1 - Indicador de Seguridad
- [ ] Barra de progreso visual del nivel de seguridad
- [ ] Porcentaje (ej: 75%)
- [ ] Nivel: Alto/Medio/Bajo con colores
- [ ] Tips para mejorar seguridad

### 29.3.2 - Autenticación de Dos Factores (2FA)
- [ ] Toggle para activar/desactivar 2FA
- [ ] Si está desactivado: botón "Configurar 2FA"
- [ ] Si está activado: mostrar "Activo" con check verde
- [ ] Opción para regenerar códigos de respaldo
- [ ] Modal de configuración con QR funcional
- [ ] Verificación con código de 6 dígitos

### 29.3.3 - Dispositivos de Confianza
- [ ] Lista de dispositivos donde has iniciado sesión
- [ ] Mostrar: Nombre del dispositivo, IP, Última vez activo
- [ ] Botón "Cerrar sesión" en cada dispositivo
- [ ] Botón "Cerrar todas las sesiones" (excepto actual)
- [ ] Dispositivo actual marcado con badge "Este dispositivo"

### 29.3.4 - Wallet Conectada
- [ ] Mostrar wallet principal conectada (parcial: UQA...x4F5)
- [ ] Estado: Conectada/No conectada
- [ ] Botón para desconectar wallet
- [ ] Botón para conectar wallet de respaldo
- [ ] Historial de wallets usadas

### 29.3.5 - Actividad de Seguridad
- [ ] Últimas 10 acciones de seguridad
- [ ] Fecha, Tipo (Login, Cambio de config, etc.)
- [ ] IP y dispositivo
- [ ] Alertas de actividad sospechosa

### 29.3.6 - Bloqueo de Cuenta
- [ ] Opción para bloquear cuenta temporalmente
- [ ] Requiere 2FA para desbloquear
- [ ] Mensaje de confirmación antes de bloquear

---

## ═══════════════════════════════════════
## FASE 29.4: SECCIÓN PRIVACIDAD ⏳
## ═══════════════════════════════════════

**Ruta:** Configuración > Privacidad
**Página separada con opciones de privacidad**

### 29.4.1 - Visibilidad del Perfil
- [ ] **Cuenta privada** - Toggle (solo seguidores ven tu contenido)
- [ ] **Mostrar estado en línea** - Toggle
- [ ] **Mostrar última conexión** - Toggle
- [ ] **Mostrar cuando escribes** - Toggle

### 29.4.2 - Quién puede contactarte
- [ ] **Mensajes directos** - Todos / Solo seguidores / Nadie
- [ ] **Solicitudes de mensaje** - Permitir / No permitir
- [ ] **Comentarios en publicaciones** - Todos / Seguidores / Desactivados

### 29.4.3 - Contenido
- [ ] **Quién puede ver tus publicaciones** - Todos / Seguidores
- [ ] **Quién puede ver tu lista de seguidores** - Todos / Solo tú
- [ ] **Quién puede ver tu lista de seguidos** - Todos / Solo tú
- [ ] **Permitir compartir tus publicaciones** - Toggle

### 29.4.4 - Bloqueos y Restricciones
- [ ] **Usuarios bloqueados** - Ver lista y gestionar
- [ ] Buscar usuario para bloquear
- [ ] Desbloquear desde la lista
- [ ] **Palabras silenciadas** - Lista de palabras a ocultar en comentarios

### 29.4.5 - Datos y Privacidad
- [ ] **Descargar mis datos** - Exportar toda tu información
- [ ] **Eliminar cuenta** - Con confirmación y advertencias
- [ ] Período de gracia antes de eliminación definitiva

---

## ═══════════════════════════════════════
## FASE 29.5: SECCIÓN NOTIFICACIONES ⏳
## ═══════════════════════════════════════

**Ruta:** Configuración > Notificaciones
**Página separada con todas las preferencias de notificación**

### 29.5.1 - Notificaciones Push
- [ ] **Activar notificaciones push** - Toggle principal
- [ ] Permiso del navegador/app

### 29.5.2 - Actividad Social
- [ ] **Likes** - Toggle (alguien da like a tu publicación)
- [ ] **Comentarios** - Toggle (alguien comenta tu publicación)
- [ ] **Menciones** - Toggle (alguien te menciona)
- [ ] **Nuevos seguidores** - Toggle
- [ ] **Solicitudes de seguimiento** - Toggle (si cuenta privada)

### 29.5.3 - Mensajes
- [ ] **Mensajes nuevos** - Toggle
- [ ] **Solicitudes de mensaje** - Toggle

### 29.5.4 - Stories
- [ ] **Reacciones a tu story** - Toggle
- [ ] **Menciones en stories** - Toggle

### 29.5.5 - Transacciones
- [ ] **Compras de B3C** - Toggle
- [ ] **Ventas/Transferencias recibidas** - Toggle
- [ ] **Retiros procesados** - Toggle
- [ ] **Alertas de precio B3C** - Toggle

### 29.5.6 - Bots y Servicios
- [ ] **Notificaciones de bots** - Toggle
- [ ] **Números virtuales** - Toggle (SMS recibido)
- [ ] **Marketplace** - Toggle (ventas, mensajes)

### 29.5.7 - Sistema
- [ ] **Actualizaciones de la app** - Toggle
- [ ] **Ofertas y promociones** - Toggle
- [ ] **Tips y tutoriales** - Toggle

### 29.5.8 - Sonidos
- [ ] **Sonido de notificación** - Toggle
- [ ] **Vibración** - Toggle
- [ ] Selector de tono de notificación

---

## ═══════════════════════════════════════
## FASE 29.6: SECCIÓN APARIENCIA ⏳
## ═══════════════════════════════════════

**Ruta:** Configuración > Apariencia
**Página separada con opciones visuales**

### 29.6.1 - Tema
- [ ] **Tema oscuro** - Opción (actual, predeterminado)
- [ ] **Tema claro** - Opción (futuro)
- [ ] **Automático** - Seguir sistema
- [ ] Preview visual de cada tema

### 29.6.2 - Color de Acento
- [ ] Selector de color de acento (dorado por defecto)
- [ ] Opciones: Dorado, Azul, Verde, Morado, Rojo
- [ ] Vista previa en tiempo real

### 29.6.3 - Idioma
- [ ] Selector de idioma
- [ ] Opciones: Español, English, Português
- [ ] Cambio inmediato sin reiniciar

### 29.6.4 - Tamaño de Texto
- [ ] Slider para ajustar tamaño de fuente
- [ ] Pequeño / Normal / Grande / Muy grande
- [ ] Vista previa del cambio

### 29.6.5 - Animaciones
- [ ] **Animaciones de UI** - Toggle
- [ ] **Efectos de transición** - Toggle
- [ ] Para usuarios que prefieren menos movimiento

---

## ═══════════════════════════════════════
## FASE 29.7: SECCIÓN WALLET ⏳
## ═══════════════════════════════════════

**Ruta:** Configuración > Wallet
**Página separada con configuración de billetera**

### 29.7.1 - Wallet Principal
- [ ] Dirección wallet conectada (parcial)
- [ ] Botón "Ver completa" (copia al portapapeles)
- [ ] Balance actual en B3C
- [ ] Balance en TON (si aplica)
- [ ] Botón "Desconectar wallet"

### 29.7.2 - Wallet de Respaldo
- [ ] Estado: Configurada / No configurada
- [ ] Botón "Agregar wallet de respaldo"
- [ ] Para recuperación de cuenta

### 29.7.3 - Preferencias de Transacción
- [ ] **Confirmación antes de enviar** - Toggle
- [ ] **Monto máximo sin confirmación** - Input numérico
- [ ] **Notificar transacciones mayores a X** - Input

### 29.7.4 - Historial
- [ ] Link a "Ver historial de transacciones"
- [ ] Exportar historial (CSV)

### 29.7.5 - Seguridad de Wallet
- [ ] **Requerir 2FA para retiros** - Toggle (recomendado)
- [ ] **Lista blanca de direcciones** - Agregar direcciones seguras

---

## ═══════════════════════════════════════
## FASE 29.8: SECCIÓN DATOS Y ALMACENAMIENTO ⏳
## ═══════════════════════════════════════

**Ruta:** Configuración > Datos y Almacenamiento
**Página separada con opciones de datos**

### 29.8.1 - Uso de Datos
- [ ] **Ahorro de datos** - Toggle (cargar imágenes en baja calidad)
- [ ] **Precargar contenido** - Toggle
- [ ] **Reproducir videos automáticamente** - Siempre / Wi-Fi / Nunca

### 29.8.2 - Almacenamiento Local
- [ ] Espacio usado por la app
- [ ] Desglose: Imágenes, Videos, Caché
- [ ] Botón "Limpiar caché"
- [ ] Botón "Limpiar todo" (con confirmación)

### 29.8.3 - Descargas
- [ ] **Calidad de descarga de imágenes** - Original / Comprimida
- [ ] **Ubicación de descargas** - Mostrar ruta

### 29.8.4 - Sincronización
- [ ] **Sincronizar contactos** - Toggle (para encontrar amigos)
- [ ] Última sincronización: fecha/hora

---

## ═══════════════════════════════════════
## FASE 29.9: SECCIÓN AYUDA ⏳
## ═══════════════════════════════════════

**Ruta:** Configuración > Ayuda
**Página separada con recursos de ayuda**

### 29.9.1 - Centro de Ayuda
- [ ] Link a FAQ completo
- [ ] Búsqueda de preguntas frecuentes
- [ ] Categorías: Cuenta, Wallet, Seguridad, etc.

### 29.9.2 - Contactar Soporte
- [ ] Botón "Abrir ticket de soporte"
- [ ] Formulario con asunto y descripción
- [ ] Adjuntar capturas de pantalla
- [ ] Ver tickets anteriores

### 29.9.3 - Reportar un Problema
- [ ] Formulario para reportar bugs
- [ ] Incluir logs automáticamente (opcional)
- [ ] Categoría del problema

### 29.9.4 - Sobre BUNK3R
- [ ] Versión de la app
- [ ] Changelog / Novedades
- [ ] Términos y condiciones
- [ ] Política de privacidad
- [ ] Licencias de código abierto

### 29.9.5 - Comunidad
- [ ] Link a canal de Telegram oficial
- [ ] Link a Twitter/X
- [ ] Link a Discord (si existe)

---

## ═══════════════════════════════════════
## FASE 29.10: CERRAR SESIÓN Y ELIMINAR ⏳
## ═══════════════════════════════════════

### 29.10.1 - Cerrar Sesión
- [ ] Botón "Cerrar sesión" (rojo, al final de la lista)
- [ ] Confirmación antes de cerrar
- [ ] Limpia tokens y datos locales
- [ ] Redirige a pantalla de login

### 29.10.2 - Cerrar Todas las Sesiones
- [ ] Opción para cerrar en todos los dispositivos
- [ ] Requiere 2FA si está activo
- [ ] Confirmación con contraseña/código

### 29.10.3 - Eliminar Cuenta (en sección Privacidad)
- [ ] Advertencia clara de lo que se perderá
- [ ] Lista de datos que se eliminarán
- [ ] Período de gracia de 30 días
- [ ] Posibilidad de cancelar eliminación
- [ ] Requiere 2FA y confirmación por Telegram

---

## ═══════════════════════════════════════
## DISEÑO Y UI DE CONFIGURACIÓN
## ═══════════════════════════════════════

### Estilo de Items de Configuración
```
┌─────────────────────────────────────────┐
│ 🔒  Seguridad                     >     │
│     Protege tu cuenta                   │
└─────────────────────────────────────────┘
```
- Icono a la izquierda (SVG, color dorado)
- Título principal (texto blanco)
- Subtítulo/descripción (texto gris)
- Flecha derecha para navegar
- Para toggles: switch en lugar de flecha

### Estilo de Toggle Switch
- Fondo inactivo: #2B3139
- Fondo activo: #0ECB81 (verde)
- Círculo: blanco
- Animación suave al cambiar

### Estilo de Secciones/Cards
```css
.settings-section {
    background: #1E2329;
    border-radius: 12px;
    margin: 8px 16px;
    overflow: hidden;
}

.settings-item {
    padding: 16px;
    border-bottom: 1px solid #2B3139;
    display: flex;
    align-items: center;
    gap: 12px;
}

.settings-item:last-child {
    border-bottom: none;
}
```

### Navegación
- Cada sección principal abre una nueva página (no modal)
- Botón de volver en cada sub-página
- Breadcrumb opcional: Configuración > Seguridad
- Animación de slide al navegar

---

## CRITERIOS DE ACEPTACIÓN SECCIÓN 29:

### Funcionalidad
- [ ] TODOS los toggles guardan en base de datos
- [ ] TODOS los botones ejecutan su acción
- [ ] TODOS los links llevan a páginas que existen
- [ ] Cambios se reflejan inmediatamente
- [ ] 2FA se configura y funciona correctamente
- [ ] Dispositivos se listan y se pueden cerrar sesión
- [ ] Cerrar sesión realmente cierra la sesión
- [ ] Eliminación de cuenta funciona con período de gracia

### Diseño
- [ ] Colores consistentes con el resto de la app
- [ ] Diseño profesional tipo Telegram Settings
- [ ] Responsive en móvil
- [ ] Iconos SVG consistentes (no emojis en producción)
- [ ] Tipografía clara y legible
- [ ] Espaciado correcto entre elementos
- [ ] Transiciones suaves

### Datos
- [ ] Preferencias se cargan desde la BD
- [ ] Cambios se guardan en la BD
- [ ] Estado de toggles refleja valores reales
- [ ] No hay datos hardcodeados

### Sin errores
- [ ] Todos los botones funcionan
- [ ] No hay errores en consola
- [ ] No hay errores 500 en servidor
- [ ] Todas las páginas existen y cargan

---

## ARCHIVOS A MODIFICAR:

### Frontend
- `templates/index.html` - Estructura HTML de configuración
- `static/js/app.js` - Lógica JavaScript
- `static/css/styles.css` - Estilos CSS

### Backend
- `app.py` - Endpoints de configuración
- `tracking/database.py` - Métodos de BD para preferencias
- `tracking/security.py` - Lógica de seguridad

### Endpoints Necesarios
- `GET /api/settings/account` - Obtener info de cuenta
- `PUT /api/settings/account` - Actualizar info de cuenta
- `GET /api/settings/privacy` - Obtener preferencias de privacidad
- `PUT /api/settings/privacy` - Actualizar privacidad
- `GET /api/settings/notifications` - Obtener preferencias de notificaciones
- `PUT /api/settings/notifications` - Actualizar notificaciones
- `GET /api/settings/appearance` - Obtener preferencias de apariencia
- `PUT /api/settings/appearance` - Actualizar apariencia
- `GET /api/settings/wallet` - Obtener config de wallet
- `PUT /api/settings/wallet` - Actualizar config wallet
- `GET /api/settings/blocked-users` - Lista de usuarios bloqueados
- `POST /api/settings/block-user` - Bloquear usuario
- `DELETE /api/settings/unblock-user/:id` - Desbloquear usuario
- `POST /api/settings/logout` - Cerrar sesión
- `POST /api/settings/logout-all` - Cerrar todas las sesiones
- `POST /api/settings/delete-account` - Iniciar eliminación de cuenta
- `POST /api/settings/cancel-deletion` - Cancelar eliminación

### Tablas de BD (verificar/crear)
- `user_preferences` - Preferencias generales del usuario
- `user_privacy_settings` - Configuraciones de privacidad
- `notification_preferences` - Preferencias de notificaciones
- `blocked_users` - Usuarios bloqueados
- `account_deletions` - Solicitudes de eliminación pendientes

---

## ORDEN DE IMPLEMENTACIÓN SUGERIDO:

1. **Primero:** Estructura HTML y navegación entre páginas
2. **Segundo:** Estilos CSS para items, toggles, cards
3. **Tercero:** Sección Seguridad (ya hay endpoints)
4. **Cuarto:** Sección Notificaciones (ya hay endpoints)
5. **Quinto:** Sección Cuenta (crear endpoints)
6. **Sexto:** Sección Privacidad (crear endpoints)
7. **Séptimo:** Sección Wallet (integrar con lo existente)
8. **Octavo:** Sección Apariencia (tema, idioma)
9. **Noveno:** Sección Datos y Almacenamiento
10. **Décimo:** Sección Ayuda y Cerrar Sesión

---
