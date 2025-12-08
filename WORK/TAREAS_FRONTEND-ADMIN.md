# TAREAS AGENTE 🟢 FRONTEND ADMIN
**Rama Git:** `feature/frontend-admin`
**Archivos asignados:** 
- routes/admin_routes.py (endpoints /api/admin/*)
- static/js/admin.js
- static/js/admin-utils.js (utilidades especificas de admin)
- static/css/admin.css
- templates/admin.html

**Nota sobre utilidades:**
- Usar `AdminUtils` de admin-utils.js para funciones especificas de admin
- Usar `SharedUtils` de shared-utils.js para funciones compartidas (SOLO LECTURA)

---

## SECCION 0: ESTRUCTURA DE BLUEPRINTS (EN PROGRESO)

### FASE 0.1: PREPARACION DE BLUEPRINTS - COMPLETADO
**Tiempo:** 1 hora
**Fecha creacion:** 8 Diciembre 2025
**Ultima actualizacion:** 8 Diciembre 2025

**Estado actual:**
- [x] Blueprint admin_routes.py creado
- [x] Endpoint /api/admin/health activo
- [ ] Migracion de endpoints desde app.py (pendiente, se hara gradualmente)

**NOTA:** Los endpoints de admin siguen funcionando en app.py.
La migracion se realizara de forma gradual para evitar interrupciones.

---

## SECCIÓN 27: ADMIN PANEL AVANZADO (27.10 - 27.25)

### FASE 27.10: SOPORTE Y TICKETS (frontend) ⏳
**Tiempo:** 3 horas

**Tareas:**
- [ ] Crear panel de tickets de soporte
- [ ] Lista de tickets con estado (abierto, en progreso, cerrado)
- [ ] Vista detallada de ticket con historial
- [ ] Formulario de respuesta a tickets
- [ ] Filtros por estado/prioridad/fecha

---

### FASE 27.11: MARKETPLACE (frontend) ⏳
**Tiempo:** 4 horas

**Tareas:**
- [ ] Dashboard de marketplace
- [ ] Gestión de productos/servicios listados
- [ ] Aprobación/rechazo de nuevos listings
- [ ] Estadísticas de ventas
- [ ] Configuración de comisiones

---

### FASE 27.12: CONFIGURACIÓN SISTEMA (frontend) ⏳
**Tiempo:** 3 horas

**Tareas:**
- [ ] Panel de configuración global
- [ ] Toggles para features on/off
- [ ] Configuración de límites (rate limits, tamaños)
- [ ] Gestión de API keys externas
- [ ] Configuración de emails/notificaciones

---

### FASE 27.13: NOTIFICACIONES ADMIN (frontend) ⏳
**Tiempo:** 2 horas

**Tareas:**
- [ ] Centro de notificaciones para admin
- [ ] Alertas de actividad sospechosa
- [ ] Notificaciones de nuevos usuarios
- [ ] Alertas de errores del sistema
- [ ] Configuración de qué notificaciones recibir

---

### FASE 27.16: CENTRO DE VIGILANCIA EN TIEMPO REAL ⏳ 🟢 MEDIA
**Tiempo:** 6 horas

**Tareas:**
- [ ] Dashboard en tiempo real con WebSocket
- [ ] Usuarios online ahora
- [ ] Transacciones en curso
- [ ] Actividad de red
- [ ] Gráficos live

---

### FASE 27.17: PERFIL COMPLETO USUARIO (Vista 360°) ⏳ 🟠 MEDIA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Ficha completa de usuario
- [ ] Historial de actividad
- [ ] Gráfico de conexiones sociales
- [ ] Historial de transacciones
- [ ] Acciones rápidas (ban, verificar, etc.)

---

### FASE 27.18: SISTEMA DE PUNTUACIÓN DE RIESGO ⏳ 🟡 ALTA
**Tiempo:** 5 horas

**Tareas:**
- [ ] Mostrar score de riesgo por usuario
- [ ] Código de colores (verde/amarillo/rojo)
- [ ] Desglose de factores de riesgo
- [ ] Historial de cambios de score
- [ ] Filtrar usuarios por nivel de riesgo

---

### FASE 27.19: MODO SHADOW (Impersonación) ⏳ 🟠 MEDIA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Botón "Ver como este usuario"
- [ ] Banner "Modo Admin - Viendo como @usuario"
- [ ] Log de sesiones de impersonación
- [ ] Tiempo límite visible

---

### FASE 27.20: SISTEMA DE ETIQUETAS ⏳ 🟢 BAJA
**Tiempo:** 3 horas

**Tareas:**
- [ ] Crear/editar etiquetas personalizadas
- [ ] Asignar etiquetas a usuarios
- [ ] Colores personalizables
- [ ] Filtrar por etiqueta

---

### FASE 27.21: COMUNICACIÓN DIRECTA ⏳ 🟠 MEDIA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Enviar notificación a usuario específico
- [ ] Broadcast a todos los usuarios
- [ ] Templates de mensajes
- [ ] Ver tickets de soporte y responder

---

### FASE 27.22: DETECTOR CUENTAS RELACIONADAS ⏳ 🟡 ALTA
**Tiempo:** 5 horas

**Tareas:**
- [ ] Visualización de grafo de relaciones
- [ ] Lista de cuentas potencialmente relacionadas
- [ ] Marcar como "Confirmado" o "Falso positivo"
- [ ] Acciones en lote

---

### FASE 27.23: GESTIÓN VERIFICACIONES ⏳ 🟠 MEDIA
**Tiempo:** 3 horas

**Tareas:**
- [ ] Cola de verificaciones pendientes
- [ ] Ver documentos/pruebas enviadas
- [ ] Aprobar/rechazar con motivo
- [ ] Tipos de verificación

---

### FASE 27.24: REPORTES Y EXPORTACIONES ⏳ 🟢 BAJA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Generador de reportes
- [ ] Exportar a CSV/PDF/Excel
- [ ] Programar reportes automáticos

---

### FASE 27.25: MONITOREO PATRONES Y ANOMALÍAS ⏳ 🟡 ALTA
**Tiempo:** 6 horas

**Tareas:**
- [ ] Dashboard de anomalías
- [ ] Alertas visuales
- [ ] Configuración de umbrales
- [ ] Historial de detecciones

---

## SECCIÓN 31: VERIFICACIÓN DE FUNCIONALIDADES

### FASE 31.4: ESTADÍSTICAS ADMIN VACÍAS (parte admin) ⏳ 🟡 ALTA
**Tiempo:** 1 hora

**Tareas:**
- [ ] Verificar cards de estadísticas en dashboard
- [ ] Conectar con endpoints de backend
- [ ] Mostrar datos reales en gráficos
- [ ] Agregar loading states

---

### FASE 31.10: MODO MANTENIMIENTO (parte admin) ⏳ 🟢 BAJA
**Tiempo:** 1 hora

**Tareas:**
- [ ] Toggle para activar modo mantenimiento
- [ ] Programación de mantenimiento
- [ ] Banner de estado actual

---

## SECCIÓN 32: LIMPIEZA Y OPTIMIZACIÓN

### FASE 32.1: ELIMINAR CONSOLE.LOG (parte admin) ⏳
**Tiempo:** 1 hora

**Tareas:**
- [ ] Reemplazar console.log por Logger en admin.js
- [ ] Verificar que no hay logs en producción

---

### FASE 32.6: VALIDACIÓN INPUTS (parte admin) ⏳
**Tiempo:** 1 hora

**Tareas:**
- [ ] Validar formularios de admin
- [ ] Validar inputs de configuración
- [ ] Mensajes de error claros

---

## RESUMEN DE HORAS ESTIMADAS

| Sección | Horas |
|---------|-------|
| 27.10 Soporte | 3h |
| 27.11 Marketplace | 4h |
| 27.12 Config Sistema | 3h |
| 27.13 Notificaciones | 2h |
| 27.16 Vigilancia RT | 6h |
| 27.17 Perfil 360° | 4h |
| 27.18 Score Riesgo | 5h |
| 27.19 Modo Shadow | 4h |
| 27.20 Etiquetas | 3h |
| 27.21 Comunicación | 4h |
| 27.22 Detector Cuentas | 5h |
| 27.23 Verificaciones | 3h |
| 27.24 Reportes | 4h |
| 27.25 Anomalías | 6h |
| 31.4 Stats vacías | 1h |
| 31.10 Mantenimiento | 1h |
| 32.1 Console.log | 1h |
| 32.6 Validación | 1h |
| **TOTAL** | **~60 horas** |

---

## ORDEN RECOMENDADO

1. 🟡 **ALTA:** 27.18 → 27.22 → 27.25 → 31.4
2. 🟠 **MEDIA:** 27.17 → 27.19 → 27.21 → 27.23
3. 🟢 **BAJA:** 27.16 → 27.20 → 27.24 → 31.10 → 32.1 → 32.6
4. 📦 **BASE:** 27.10 → 27.11 → 27.12 → 27.13
