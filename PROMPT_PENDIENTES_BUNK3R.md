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
| Sección actual | 27 |
| Total secciones | 1 |
| Completadas | 0 ✅ |
| Pendientes | 1 ⏳ |
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
