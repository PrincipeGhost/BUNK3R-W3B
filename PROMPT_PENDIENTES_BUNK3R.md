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
| Completadas | 4 ✅ (27.1 Dashboard, 27.2 Usuarios 95%, 27.3 Transacciones, 27.4 Wallets) |
| Pendientes | Secciones 27.5 en adelante ⏳ |
| En progreso | Ninguna 🔄 |
| Crítico | 0 🔴 |

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
## FASE 27.1: DASHBOARD PRINCIPAL ✅
## ═══════════════════════════════════════

**Pantalla de inicio del admin con resumen de TODO**

### 27.1.1 - Métricas en Tiempo Real (Cards superiores)
- [x] Total de usuarios registrados
- [x] Usuarios activos HOY
- [x] Total B3C en circulación
- [x] Balance Hot Wallet (TON)
- [x] Transacciones últimas 24h
- [x] Ingresos del día (comisiones)

### 27.1.2 - Gráficos del Dashboard
- [x] Gráfico de usuarios nuevos (últimos 30 días)
- [x] Gráfico de transacciones (últimos 7 días)
- [x] Gráfico de ingresos por comisiones
- [x] Gráfico de uso por sección de la app

### 27.1.3 - Actividad Reciente (Feed en vivo)
- [x] Últimas 10 transacciones
- [x] Últimos 5 usuarios registrados
- [x] Últimas alertas del sistema
- [x] Auto-refresh cada 30 segundos

### 27.1.4 - Alertas Críticas
- [x] Banner rojo si hay errores del sistema
- [x] Alerta si hot wallet tiene bajo balance
- [x] Alerta de retiros pendientes de aprobar
- [x] Alerta de reportes de contenido sin revisar

---

## ═══════════════════════════════════════
## FASE 27.2: GESTIÓN DE USUARIOS 🔄 (95% Completada)
## ═══════════════════════════════════════

### 27.2.1 - Lista de Usuarios
- [x] Tabla paginada con TODOS los usuarios
- [x] Columnas: ID, Username, Nombre, Email, Fecha registro
- [x] Columnas: Última conexión, IP, País, Dispositivo
- [x] Columnas: Balance B3C, Estado (activo/baneado), Verificado
- [x] Búsqueda por username, ID, IP
- [x] Filtros: Estado, País, Fecha de registro
- [x] Ordenar por cualquier columna
- [x] Exportar a CSV

### 27.2.2 - Detalle de Usuario (al hacer clic)
- [x] Información completa del perfil
- [x] Historial de IPs usadas
- [x] Dispositivos conectados
- [x] Historial de sesiones (Activity Log)
- [x] Todas las transacciones del usuario
- [x] Publicaciones del usuario
- [x] Compras de números virtuales
- [x] Notas del admin sobre el usuario

### 27.2.3 - Acciones sobre Usuario
- [x] Banear/Suspender (temporal o permanente)
- [x] Desbanear
- [x] Cerrar todas las sesiones activas
- [x] Ajustar balance B3C manualmente (con razón)
- [x] Enviar notificación al usuario
- [x] Agregar nota interna
- [ ] Ver como este usuario (impersonar) - Pendiente por seguridad

### 27.2.4 - Detección de Fraude
- [x] Alertas de múltiples cuentas (misma IP)
- [x] Alertas de cambios de IP frecuentes
- [x] Alertas de actividad sospechosa
- [x] Lista de IPs bloqueadas
- [x] Agregar IP a blacklist

---

## ═══════════════════════════════════════
## FASE 27.3: TRANSACCIONES Y FINANZAS ✅
## ═══════════════════════════════════════

### 27.3.1 - Dashboard Financiero
- [x] Total B3C vendidos (histórico)
- [x] Total TON recibidos
- [x] Total comisiones ganadas
- [x] Gráfico de ingresos diarios
- [x] Gráfico de volumen de transacciones
- [x] Comparativa mes actual vs anterior

### 27.3.2 - Lista de Transacciones
- [x] Tabla con TODAS las transacciones
- [x] Tipos: Compra B3C, Venta B3C, Transferencia P2P, Retiro
- [x] Columnas: ID, Usuario, Tipo, Monto, Estado, Fecha, TX Hash
- [x] Filtros: Tipo, Estado, Fecha, Usuario
- [x] Búsqueda por TX hash o ID
- [x] Ver detalle de cada transacción
- [x] Link a TonScan para transacciones blockchain

### 27.3.3 - Compras de B3C
- [x] Lista de todas las compras
- [x] Estado: Pendiente, Confirmada, Fallida, Expirada
- [x] Acreditar manualmente si es necesario
- [x] Ver wallet de depósito usada
- [x] Ver transacción en blockchain

### 27.3.4 - Retiros
- [x] Lista de solicitudes de retiro
- [x] Estados: Pendiente, Aprobado, Procesado, Rechazado
- [x] Aprobar retiro (requiere 2FA)
- [x] Rechazar retiro (con razón)
- [x] Marcar como procesado
- [x] Ver historial de retiros procesados

### 27.3.5 - Transferencias P2P
- [x] Lista de transferencias entre usuarios
- [x] Ver emisor y receptor
- [x] Detectar transferencias sospechosas
- [ ] Revertir transferencia (si es necesario) - Pendiente por seguridad

### 27.3.6 - Estadísticas por Período
- [x] Selector de rango de fechas
- [x] Estadísticas del período seleccionado
- [x] Exportar reporte a CSV/PDF

---

## ═══════════════════════════════════════
## FASE 27.4: WALLETS Y BLOCKCHAIN ✅
## ═══════════════════════════════════════

### 27.4.1 - Hot Wallet
- [x] Balance actual en TON (tiempo real)
- [x] Dirección de la hot wallet
- [x] Botón para ver en TonScan
- [x] Historial de transacciones entrantes/salientes
- [x] Alerta si balance bajo (configurable)

### 27.4.2 - Wallets de Depósito
- [x] Lista de todas las wallets generadas
- [x] Estado: Disponible, Asignada, Usada, Consolidada
- [x] Balance de cada wallet
- [x] Usuario asignado (si aplica)
- [x] Consolidar fondos manualmente (individual)
- [x] Consolidar todas las wallets con balance
- [x] Filtro por estado
- [x] Link a TonScan por wallet

### 27.4.3 - Pool de Wallets
- [x] Estadísticas del pool
- [x] Wallets disponibles vs usadas
- [x] Generar más wallets (llenar pool)
- [x] Configurar tamaño mínimo del pool
- [x] Configurar umbral de auto-rellenado
- [x] Configurar umbral de balance bajo

### 27.4.4 - Historial Blockchain
- [x] Todas las transacciones on-chain
- [x] Consolidaciones realizadas
- [x] Retiros enviados
- [x] Estado de confirmaciones
- [x] Tabs para filtrar por tipo
- [x] Link a TonScan por transacción

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
## FASE 27.16: CENTRO DE VIGILANCIA EN TIEMPO REAL ⏳
## ═══════════════════════════════════════

**Pantalla para ver qué están haciendo los usuarios AHORA MISMO**

### 27.16.1 - Usuarios Conectados Ahora
- [ ] Lista de usuarios online en este momento
- [ ] Indicador verde "En línea" / amarillo "Inactivo" / gris "Desconectado"
- [ ] Tiempo que llevan conectados
- [ ] Última acción realizada
- [ ] Click para ver perfil completo
- [ ] Contador total de usuarios online

### 27.16.2 - Feed de Actividad en Vivo
- [ ] Stream en tiempo real de TODAS las acciones
- [ ] Tipos: Login, Logout, Publicación, Compra, Venta, Mensaje, etc.
- [ ] Timestamp de cada acción
- [ ] Usuario que realizó la acción
- [ ] Filtrar por tipo de acción
- [ ] Filtrar por usuario específico
- [ ] Pausar/Reanudar feed
- [ ] Auto-scroll o manual

### 27.16.3 - Mapa de Usuarios (Opcional)
- [ ] Mapa mundial con ubicación de usuarios conectados
- [ ] Puntos en países donde hay usuarios
- [ ] Hover muestra cantidad por país
- [ ] Click en país filtra lista

### 27.16.4 - Alertas en Tiempo Real
- [ ] Popup cuando ocurre algo crítico
- [ ] Nuevo usuario registrado
- [ ] Compra grande (>X TON)
- [ ] Múltiples logins fallidos
- [ ] Usuario reportado
- [ ] Sonido opcional para alertas

---

## ═══════════════════════════════════════
## FASE 27.17: PERFIL COMPLETO DEL USUARIO (VISTA 360°) ⏳
## ═══════════════════════════════════════

**Al hacer clic en un usuario, ver ABSOLUTAMENTE TODO sobre él**

### 27.17.1 - Header del Perfil Admin
- [ ] Avatar grande del usuario
- [ ] Username y nombre completo
- [ ] Badges: Verificado, Baneado, VIP, Sospechoso
- [ ] Fecha de registro
- [ ] Última conexión (hace X minutos/horas)
- [ ] Estado actual: Online/Offline
- [ ] Botones de acción rápida (Banear, Mensaje, Impersonar)

### 27.17.2 - Resumen Ejecutivo
- [ ] Card con estadísticas clave del usuario:
  - Total gastado en B3C
  - Total publicaciones
  - Total seguidores/seguidos
  - Nivel de actividad (Alto/Medio/Bajo)
  - Score de riesgo (ver FASE 27.18)
  - Días desde registro
  - Días desde última actividad

### 27.17.3 - Timeline de Actividad Completa
- [ ] TODAS las acciones del usuario en orden cronológico
- [ ] Infinito scroll o paginación
- [ ] Iconos por tipo de acción
- [ ] Filtrar por: Fecha, Tipo de acción
- [ ] Buscar en actividad
- [ ] Exportar timeline completo

### 27.17.4 - Información de Cuenta
- [ ] Telegram ID
- [ ] Username de Telegram
- [ ] Email (si existe)
- [ ] Teléfono (si existe)
- [ ] Bio del perfil
- [ ] Website
- [ ] Fecha de nacimiento
- [ ] Género

### 27.17.5 - Información de Acceso
- [ ] Historial COMPLETO de IPs usadas (con fechas)
- [ ] País/Ciudad de cada IP (geolocalización)
- [ ] Dispositivos usados (con User-Agent parseado)
- [ ] Navegadores usados
- [ ] Sistema operativo
- [ ] Lista de sesiones activas ahora
- [ ] Historial de sesiones pasadas

### 27.17.6 - Información de Wallet
- [ ] Wallet principal conectada (completa)
- [ ] Wallet de respaldo (si existe)
- [ ] Balance actual en B3C
- [ ] Balance en TON vinculado
- [ ] Link a TonScan para ver wallet
- [ ] Historial de wallets conectadas/desconectadas

### 27.17.7 - Información de Seguridad
- [ ] 2FA activado: Sí/No
- [ ] Fecha de activación 2FA
- [ ] Dispositivos de confianza
- [ ] Intentos de login fallidos recientes
- [ ] Alertas de seguridad del usuario
- [ ] Score de seguridad

### 27.17.8 - Transacciones del Usuario
- [ ] Tabla con TODAS las transacciones
- [ ] Tipos: Compras, Ventas, Transferencias enviadas/recibidas, Retiros
- [ ] Montos, fechas, estados
- [ ] Total gastado histórico
- [ ] Total recibido histórico
- [ ] Gráfico de actividad financiera

### 27.17.9 - Contenido del Usuario
- [ ] Grid de todas sus publicaciones
- [ ] Preview de cada publicación
- [ ] Likes, comentarios, shares de cada una
- [ ] Stories subidas
- [ ] Contenido eliminado (si se guarda)
- [ ] Comentarios que ha dejado en otras publicaciones

### 27.17.10 - Interacciones Sociales
- [ ] Lista de seguidores (con links)
- [ ] Lista de seguidos (con links)
- [ ] Usuarios que más interactúa
- [ ] Mensajes enviados/recibidos (cantidad, no contenido)
- [ ] Usuarios bloqueados por él
- [ ] Usuarios que lo bloquearon

### 27.17.11 - Compras y Servicios Usados
- [ ] Números virtuales comprados
- [ ] Bots utilizados
- [ ] Compras en marketplace
- [ ] Ventas en marketplace
- [ ] Total gastado en cada servicio

### 27.17.12 - Notas y Etiquetas del Admin
- [ ] Notas internas sobre el usuario
- [ ] Agregar nueva nota (con fecha y admin que la escribió)
- [ ] Etiquetas asignadas (ver FASE 27.20)
- [ ] Historial de acciones admin sobre este usuario
- [ ] Historial de baneos/advertencias

---

## ═══════════════════════════════════════
## FASE 27.18: SISTEMA DE PUNTUACIÓN DE RIESGO ⏳
## ═══════════════════════════════════════

**Sistema automático para detectar usuarios problemáticos**

### 27.18.1 - Score de Riesgo (0-100)
- [ ] Algoritmo que calcula puntuación automática
- [ ] Factores que SUMAN riesgo:
  - Múltiples IPs en poco tiempo (+15)
  - Cambio frecuente de wallet (+20)
  - Contenido reportado (+10 por reporte)
  - Transacciones sospechosas (+25)
  - Cuenta nueva con alta actividad (+10)
  - IP en lista de proxies/VPN (+15)
  - Patrones de bot/automatización (+30)
  - Login desde países de alto riesgo (+10)
  - Intentos de login fallidos (+5 cada uno)

### 27.18.2 - Factores que RESTAN riesgo
- [ ] 2FA activado (-20)
- [ ] Cuenta verificada (-15)
- [ ] Antigüedad de cuenta (-5 por año)
- [ ] Historial limpio (-10)
- [ ] Transacciones exitosas (-1 por cada 10)

### 27.18.3 - Niveles de Riesgo
- [ ] 0-20: 🟢 Bajo (verde)
- [ ] 21-40: 🟡 Moderado (amarillo)
- [ ] 41-60: 🟠 Elevado (naranja)
- [ ] 61-80: 🔴 Alto (rojo)
- [ ] 81-100: ⚫ Crítico (negro)

### 27.18.4 - Dashboard de Riesgo
- [ ] Lista de usuarios ordenados por score de riesgo
- [ ] Alertas automáticas para score > 60
- [ ] Filtrar por nivel de riesgo
- [ ] Ver detalle de por qué tiene ese score
- [ ] Acción rápida: Revisar / Banear / Ignorar

### 27.18.5 - Configuración del Sistema de Riesgo
- [ ] Ajustar peso de cada factor
- [ ] Definir umbrales de alerta
- [ ] Activar/desactivar factores específicos
- [ ] Acciones automáticas por nivel (ej: banear si > 90)

---

## ═══════════════════════════════════════
## FASE 27.19: MODO SHADOW (IMPERSONACIÓN AVANZADA) ⏳
## ═══════════════════════════════════════

**Ver la app EXACTAMENTE como la ve el usuario**

### 27.19.1 - Activar Modo Shadow
- [ ] Botón "Ver como este usuario" en perfil
- [ ] Requiere 2FA para activar
- [ ] Se registra en logs de admin
- [ ] Tiempo límite de sesión shadow (30 min)

### 27.19.2 - Vista Shadow
- [ ] Ver la app completa como si fueras el usuario
- [ ] Ver su feed personalizado
- [ ] Ver sus mensajes (solo lectura)
- [ ] Ver sus transacciones
- [ ] Ver su perfil como él lo ve
- [ ] Banner visible "Modo Shadow: @usuario" 

### 27.19.3 - Limitaciones de Seguridad
- [ ] NO puede realizar acciones (solo lectura)
- [ ] NO puede enviar mensajes
- [ ] NO puede hacer transacciones
- [ ] NO puede cambiar configuración del usuario
- [ ] TODO queda registrado en logs

### 27.19.4 - Uso para Debugging
- [ ] Ver exactamente lo que reporta el usuario
- [ ] Reproducir bugs que solo él ve
- [ ] Verificar que los permisos funcionan bien
- [ ] Botón "Reportar bug desde vista shadow"

---

## ═══════════════════════════════════════
## FASE 27.20: SISTEMA DE ETIQUETAS Y CLASIFICACIÓN ⏳
## ═══════════════════════════════════════

**Organizar y clasificar usuarios con etiquetas personalizadas**

### 27.20.1 - Etiquetas Predefinidas
- [ ] 🐋 Ballena (gasta mucho)
- [ ] ⭐ VIP
- [ ] 🔍 En revisión
- [ ] ⚠️ Advertido
- [ ] 🚨 Sospechoso
- [ ] 🤖 Posible bot
- [ ] 👑 Influencer
- [ ] 🆕 Nuevo
- [ ] 💎 Premium
- [ ] 🔒 Cuenta segura

### 27.20.2 - Etiquetas Personalizadas
- [ ] Crear nuevas etiquetas
- [ ] Definir color de la etiqueta
- [ ] Definir icono/emoji
- [ ] Descripción de la etiqueta
- [ ] Eliminar etiquetas no usadas

### 27.20.3 - Asignar Etiquetas
- [ ] Asignar múltiples etiquetas a un usuario
- [ ] Desde el perfil del usuario
- [ ] Desde la lista de usuarios (selección múltiple)
- [ ] Etiquetas automáticas (basadas en reglas)

### 27.20.4 - Filtrar por Etiquetas
- [ ] En lista de usuarios, filtrar por etiqueta
- [ ] Combinación de etiquetas (AND/OR)
- [ ] Ver solo usuarios con X etiqueta
- [ ] Estadísticas por etiqueta

### 27.20.5 - Reglas Automáticas de Etiquetado
- [ ] Si gasta > X B3C → Etiqueta "Ballena"
- [ ] Si tiene > X seguidores → Etiqueta "Influencer"
- [ ] Si score riesgo > 60 → Etiqueta "Sospechoso"
- [ ] Configurar reglas personalizadas

---

## ═══════════════════════════════════════
## FASE 27.21: COMUNICACIÓN DIRECTA CON USUARIOS ⏳
## ═══════════════════════════════════════

**Enviar mensajes y notificaciones directas a usuarios**

### 27.21.1 - Mensaje Individual
- [ ] Enviar mensaje directo a un usuario
- [ ] Aparece en sus notificaciones como "Mensaje del equipo BUNK3R"
- [ ] Template de mensajes predefinidos
- [ ] Mensaje personalizado
- [ ] Adjuntar imagen (opcional)

### 27.21.2 - Mensaje Masivo
- [ ] Enviar a TODOS los usuarios
- [ ] Enviar a usuarios filtrados (por país, etiqueta, etc.)
- [ ] Programar envío
- [ ] Vista previa antes de enviar
- [ ] Confirmar cantidad de destinatarios

### 27.21.3 - Tipos de Mensaje
- [ ] Informativo (icono azul)
- [ ] Advertencia (icono amarillo)
- [ ] Urgente (icono rojo)
- [ ] Promocional (icono dorado)
- [ ] Actualización (icono verde)

### 27.21.4 - Historial de Mensajes
- [ ] Log de todos los mensajes enviados
- [ ] Quién envió, a quién, cuándo
- [ ] Estadísticas de lectura (si se implementa)
- [ ] Buscar en historial

### 27.21.5 - Notificaciones Telegram
- [ ] Enviar notificación via bot de Telegram
- [ ] Solo si el usuario tiene bot vinculado
- [ ] Para mensajes urgentes
- [ ] Respeta configuración del usuario

---

## ═══════════════════════════════════════
## FASE 27.22: DETECTOR DE CUENTAS RELACIONADAS ⏳
## ═══════════════════════════════════════

**Encontrar multicuentas y cuentas vinculadas**

### 27.22.1 - Detección por IP
- [ ] Usuarios que comparten la misma IP
- [ ] Lista agrupada por IP
- [ ] Alerta automática si > 2 cuentas por IP
- [ ] Marcar IPs de lugares públicos (cafés, universidades)

### 27.22.2 - Detección por Dispositivo
- [ ] Usuarios con el mismo device fingerprint
- [ ] Mismo User-Agent exacto
- [ ] Mismo tamaño de pantalla + idioma + zona horaria

### 27.22.3 - Detección por Wallet
- [ ] Usuarios que usaron la misma wallet
- [ ] Wallets que transfirieron entre sí frecuentemente
- [ ] Patrón de "wallet intermedia"

### 27.22.4 - Detección por Comportamiento
- [ ] Usuarios que se siguen mutuamente inmediatamente
- [ ] Mismo patrón de horarios de conexión
- [ ] Mismas palabras/frases en bio o publicaciones
- [ ] Nombres similares (variaciones)

### 27.22.5 - Vista de Relaciones
- [ ] Gráfico visual de conexiones entre usuarios
- [ ] Nodos = usuarios, líneas = relación
- [ ] Color de línea según tipo de relación
- [ ] Click en nodo para ver perfil

### 27.22.6 - Acciones sobre Multicuentas
- [ ] Marcar como "cuentas relacionadas"
- [ ] Banear todas las cuentas relacionadas
- [ ] Permitir (marcar como válido, ej: familia)
- [ ] Fusionar cuentas (transferir datos a una)

---

## ═══════════════════════════════════════
## FASE 27.23: GESTIÓN DE VERIFICACIONES ⏳
## ═══════════════════════════════════════

**Aprobar o rechazar solicitudes de verificación de usuarios**

### 27.23.1 - Cola de Verificaciones
- [ ] Lista de solicitudes pendientes
- [ ] Ordenar por fecha de solicitud
- [ ] Filtrar por tipo de verificación
- [ ] Contador de pendientes

### 27.23.2 - Detalle de Solicitud
- [ ] Información del usuario solicitante
- [ ] Documentos subidos (si aplica)
- [ ] Razón de la solicitud
- [ ] Historial del usuario
- [ ] Score de riesgo

### 27.23.3 - Tipos de Verificación
- [ ] Verificación básica (email/teléfono)
- [ ] Verificación de identidad (documento)
- [ ] Verificación de creador (influencer)
- [ ] Verificación de negocio

### 27.23.4 - Acciones
- [ ] Aprobar verificación
- [ ] Rechazar con razón
- [ ] Pedir más información
- [ ] Escalar a otro admin

### 27.23.5 - Historial de Verificaciones
- [ ] Todas las verificaciones procesadas
- [ ] Aprobadas vs rechazadas
- [ ] Estadísticas
- [ ] Tiempo promedio de respuesta

---

## ═══════════════════════════════════════
## FASE 27.24: REPORTES Y EXPORTACIONES AVANZADAS ⏳
## ═══════════════════════════════════════

**Generar reportes detallados para análisis**

### 27.24.1 - Reportes de Usuarios
- [ ] Reporte de usuarios activos
- [ ] Reporte de usuarios inactivos (no login en X días)
- [ ] Reporte de usuarios nuevos por período
- [ ] Reporte de usuarios por país
- [ ] Reporte de usuarios por nivel de riesgo

### 27.24.2 - Reportes Financieros
- [ ] Ingresos por período (día/semana/mes)
- [ ] Desglose por tipo de transacción
- [ ] Top usuarios por volumen
- [ ] Comparativa entre períodos
- [ ] Proyecciones

### 27.24.3 - Reportes de Contenido
- [ ] Publicaciones por período
- [ ] Contenido reportado vs moderado
- [ ] Usuarios más activos creando contenido
- [ ] Hashtags trending

### 27.24.4 - Reportes de Seguridad
- [ ] Intentos de acceso fallidos
- [ ] IPs bloqueadas
- [ ] Alertas de seguridad
- [ ] Acciones admin realizadas

### 27.24.5 - Formatos de Exportación
- [ ] CSV (Excel compatible)
- [ ] PDF con gráficos
- [ ] JSON (para sistemas externos)
- [ ] Programar reportes automáticos (email)

### 27.24.6 - Dashboard de Reportes
- [ ] Selector de tipo de reporte
- [ ] Selector de rango de fechas
- [ ] Filtros adicionales
- [ ] Vista previa antes de exportar
- [ ] Historial de reportes generados

---

## ═══════════════════════════════════════
## FASE 27.25: MONITOREO DE PATRONES Y ANOMALÍAS ⏳
## ═══════════════════════════════════════

**Detectar comportamientos anómalos automáticamente**

### 27.25.1 - Patrones de Transacción
- [ ] Alerta si usuario hace X transacciones en Y minutos
- [ ] Alerta si monto total supera umbral en período
- [ ] Patrón de "lavado" (múltiples transferencias pequeñas)
- [ ] Transacciones a horas inusuales

### 27.25.2 - Patrones de Acceso
- [ ] Login desde nuevo país
- [ ] Cambio de dispositivo frecuente
- [ ] Sesiones simultáneas desde diferentes lugares
- [ ] Velocidad de cambio de IP imposible (ej: España a Japón en 5 min)

### 27.25.3 - Patrones de Contenido
- [ ] Spam (muchas publicaciones en poco tiempo)
- [ ] Contenido repetitivo
- [ ] Links sospechosos
- [ ] Palabras clave de alerta

### 27.25.4 - Patrones de Interacción
- [ ] Seguimiento masivo (follow/unfollow)
- [ ] Likes masivos automatizados
- [ ] Comentarios repetitivos
- [ ] Comportamiento de bot

### 27.25.5 - Configuración de Alertas
- [ ] Definir umbrales para cada patrón
- [ ] Activar/desactivar detección
- [ ] Acciones automáticas (alertar, banear, limitar)
- [ ] Whitelist de usuarios excluidos

### 27.25.6 - Dashboard de Anomalías
- [ ] Lista de anomalías detectadas hoy
- [ ] Clasificar por severidad
- [ ] Marcar como revisada
- [ ] Tomar acción o descartar
- [ ] Estadísticas de anomalías por tipo

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
├── 👁️ VIGILANCIA (NUEVO)
│   ├── En Tiempo Real
│   ├── Feed de Actividad
│   ├── Mapa de Usuarios
│   └── Alertas
├── Usuarios
│   ├── Lista Completa
│   ├── Perfiles 360°
│   ├── Baneados
│   ├── Sesiones Activas
│   ├── Por Riesgo
│   ├── Por Etiqueta
│   └── Multicuentas
├── 🎭 Modo Shadow
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
├── 🏷️ Etiquetas
│   ├── Gestionar Etiquetas
│   └── Reglas Automáticas
├── ⚠️ Riesgo
│   ├── Dashboard Riesgo
│   ├── Configurar Factores
│   └── Alertas Activas
├── 📨 Comunicación
│   ├── Enviar Mensaje
│   ├── Mensajes Masivos
│   └── Historial
├── ✅ Verificaciones
│   ├── Pendientes
│   └── Historial
├── Logs
│   ├── Acciones Admin
│   ├── Errores
│   ├── Logins
│   └── Anomalías
├── 📊 Reportes
│   ├── Generar Reporte
│   ├── Programados
│   └── Historial
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

### Prioridad 1 - Control de Usuarios (CRÍTICO)
1. **FASE 27.1** - Dashboard Principal (base del panel)
2. **FASE 27.2** - Gestión de Usuarios (crítico para seguridad)
3. **FASE 27.17** - Perfil 360° del Usuario (vista completa)
4. **FASE 27.16** - Centro de Vigilancia en Tiempo Real
5. **FASE 27.18** - Sistema de Puntuación de Riesgo
6. **FASE 27.19** - Modo Shadow (Impersonación)
7. **FASE 27.15** - Acceso y Sesiones

### Prioridad 2 - Finanzas y Transacciones
8. **FASE 27.3** - Transacciones y Finanzas
9. **FASE 27.4** - Wallets y Blockchain

### Prioridad 3 - Organización y Comunicación
10. **FASE 27.20** - Sistema de Etiquetas
11. **FASE 27.21** - Comunicación Directa
12. **FASE 27.22** - Detector de Multicuentas
13. **FASE 27.23** - Gestión de Verificaciones

### Prioridad 4 - Logs y Seguridad
14. **FASE 27.8** - Logs y Auditoría
15. **FASE 27.25** - Monitoreo de Anomalías
16. **FASE 27.24** - Reportes Avanzados

### Prioridad 5 - Contenido y Servicios
17. **FASE 27.5** - Contenido y Publicaciones
18. **FASE 27.6** - Números Virtuales
19. **FASE 27.7** - Gestión de Bots
20. **FASE 27.11** - Marketplace

### Prioridad 6 - Extras
21. **FASE 27.9** - Analytics
22. **FASE 27.10** - Soporte y Tickets
23. **FASE 27.12** - Configuración
24. **FASE 27.13** - Notificaciones Admin
25. **FASE 27.14** - Backup y Mantenimiento

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

## ════════════════════════════════════════════════════════════════
## SECCIÓN 30: FIXES DE SEGURIDAD Y VULNERABILIDADES 🔴
## ════════════════════════════════════════════════════════════════

**Prioridad:** 🔴 CRÍTICA  
**Agregado:** 6 Diciembre 2025  
**Estado:** EN PROGRESO 🔄

---

### OBJETIVO PRINCIPAL:
Resolver todas las vulnerabilidades de seguridad detectadas en el análisis del proyecto, organizadas por severidad para asegurar la integridad y protección de los usuarios y sus fondos.

---

## ═══════════════════════════════════════
## FASE 30.1: VULNERABILIDADES CRÍTICAS 🔴
## ═══════════════════════════════════════

### 30.1.1 - Eliminar/Proteger Modo Demo ✅
**Problema:** El header `X-Demo-Mode: true` otorga acceso de OWNER sin validación.
**Riesgo:** Cualquier atacante puede obtener privilegios de administrador.
**Ubicación:** `app.py` líneas 549, 601, 3125

**Solución:**
- [x] Eliminar modo demo en producción
- [x] Si se mantiene, solo permitir en desarrollo (verificar `IS_PRODUCTION`)
- [x] Agregar logging cuando se intente usar en producción

---

### 30.1.2 - Implementar Protección CSRF ⏳
**Problema:** No hay tokens CSRF en formularios/endpoints.
**Riesgo:** Ataques Cross-Site Request Forgery en operaciones financieras.
**Ubicación:** `app.py` - todos los endpoints POST/PUT/DELETE

**Solución:**
- [ ] Implementar tokens CSRF para operaciones críticas
- [ ] Validar origen de requests (Origin/Referer headers)
- [ ] Agregar header `SameSite` a cookies

---

### 30.1.3 - Proteger Endpoints Públicos de B3C ⏳
**Problema:** Endpoints de precio/cálculo son públicos sin rate limiting estricto.
**Riesgo:** Scraping de precios, análisis de patrones, DoS.
**Ubicación:** `/api/b3c/price`, `/api/b3c/network`, `/api/b3c/calculate/*`

**Solución:**
- [ ] Agregar rate limiting más estricto (10/min por IP)
- [ ] Considerar autenticación opcional
- [ ] Agregar headers de cache para reducir carga

---

## ═══════════════════════════════════════
## FASE 30.2: VULNERABILIDADES ALTAS 🟠
## ═══════════════════════════════════════

### 30.2.1 - Corregir SQL Injection Potencial ⏳
**Problema:** Construcción de SQL con f-strings en lugar de queries parametrizadas.
**Riesgo:** Inyección SQL, pérdida de datos, acceso no autorizado.
**Ubicación:** `tracking/database.py` - función `generate_route_history_events`

**Solución:**
- [ ] Revisar todas las funciones con SQL
- [ ] Reemplazar f-strings por queries parametrizadas (%s)
- [ ] Agregar tests de seguridad

---

### 30.2.2 - Agregar SERIALIZABLE a Compra de Bots ⏳
**Problema:** La función de compra de bots no previene race conditions.
**Riesgo:** Doble gasto, usuarios obtienen bots gratis.
**Ubicación:** `tracking/database.py` líneas 1455-1506

**Solución:**
- [ ] Agregar `conn.set_session(isolation_level='SERIALIZABLE')`
- [ ] Usar `SELECT ... FOR UPDATE` en balance check
- [ ] Agregar rollback explícito en errores

---

### 30.2.3 - Validar Wallet en register_backup_wallet ⏳
**Problema:** No se valida formato de wallet antes de guardar.
**Riesgo:** Wallets inválidas guardadas, errores en retiros.
**Ubicación:** `app.py` endpoint `/api/security/wallet/backup`

**Solución:**
- [ ] Usar `validate_ton_address()` antes de guardar
- [ ] Rechazar wallets con formato inválido
- [ ] Agregar tests unitarios

---

### 30.2.4 - Mejorar Manejo de Excepciones ⏳
**Problema:** Muchos `except Exception` devuelven `str(e)` exponiendo detalles internos.
**Riesgo:** Exposición de información sensible a atacantes.
**Ubicación:** Múltiples archivos

**Solución:**
- [ ] Usar `sanitize_error()` consistentemente
- [ ] No exponer stack traces al usuario
- [ ] Logging detallado interno, mensaje genérico externo

---

## ═══════════════════════════════════════
## FASE 30.3: VULNERABILIDADES MEDIAS 🟡
## ═══════════════════════════════════════

### 30.3.1 - Agregar Headers de Seguridad ⏳
**Problema:** Faltan headers de seguridad HTTP estándar.
**Riesgo:** XSS, clickjacking, MITM attacks.
**Ubicación:** `app.py` - respuestas HTTP

**Solución:**
- [ ] Agregar `X-Content-Type-Options: nosniff`
- [ ] Agregar `X-Frame-Options: DENY` (o SAMEORIGIN si necesario)
- [ ] Agregar `Strict-Transport-Security` en producción
- [ ] Agregar `Content-Security-Policy` básico
- [ ] Agregar `X-XSS-Protection: 1; mode=block`

---

### 30.3.2 - Rate Limiting Consistente ⏳
**Problema:** Algunos endpoints financieros no tienen rate limiting.
**Riesgo:** Abuso de API, DoS en endpoints críticos.
**Ubicación:** Varios endpoints en `app.py`

**Solución:**
- [ ] Revisar todos los endpoints y agregar rate limiting donde falte
- [ ] Endpoints financieros: máximo 10-30 req/min
- [ ] Endpoints de lectura: máximo 60-100 req/min

---

### 30.3.3 - Corregir Errores de Tipado (LSP) ⏳
**Problema:** 311 errores de tipado detectados por el linter.
**Riesgo:** Bugs difíciles de detectar en runtime.
**Ubicación:** `app.py` (302), `tracking/security.py` (9)

**Solución:**
- [ ] Agregar type hints correctos a funciones
- [ ] Corregir returns de `None` donde se espera otro tipo
- [ ] Usar Optional[] donde aplique

---

### 30.3.4 - Proteger Health Endpoint ⏳
**Problema:** `/api/health` expone estado de la base de datos.
**Riesgo:** Información útil para atacantes sobre disponibilidad.
**Ubicación:** `app.py` líneas 655-681

**Solución:**
- [ ] Limitar información expuesta
- [ ] Considerar autenticación básica o IP whitelist
- [ ] Solo exponer `ready: true/false`

---

## ═══════════════════════════════════════
## FASE 30.4: MEJORAS DE SEGURIDAD 🟢
## ═══════════════════════════════════════

### 30.4.1 - Sistema de Logs de Auditoría ⏳
- [ ] Registrar todas las acciones de admin
- [ ] Registrar cambios de configuración
- [ ] Registrar intentos de acceso fallidos
- [ ] Tabla `admin_audit_log` con timestamps

### 30.4.2 - Límites Acumulados Diarios ⏳
- [ ] Implementar límite diario de retiros por usuario
- [ ] Alertar al admin si se supera umbral
- [ ] Permitir override manual por admin

### 30.4.3 - Alertas de Seguridad en Tiempo Real ⏳
- [ ] Notificación Telegram a owner cuando:
  - Múltiples intentos de login fallidos
  - Retiro grande (>X TON)
  - Cambio de wallet primaria
  - Acceso desde nueva IP/país

### 30.4.4 - Verificación Adicional para Retiros Grandes ⏳
- [ ] Requerir confirmación 2FA para retiros >100 TON
- [ ] Delay de 24h para retiros >500 TON (con opción de cancelar)
- [ ] Notificación obligatoria al usuario

---

## CRITERIOS DE ACEPTACIÓN GENERAL:

- [ ] Todos los fixes críticos implementados
- [ ] Tests manuales de cada corrección
- [ ] Sin regresiones en funcionalidades existentes
- [ ] Logs verificados sin errores
- [ ] Documentación actualizada

---
