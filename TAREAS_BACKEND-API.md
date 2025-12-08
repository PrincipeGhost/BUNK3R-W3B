# TAREAS AGENTE 🟡 BACKEND API
**Rama Git:** `feature/backend-api`
**Archivos asignados:** app.py, tracking/database.py, tracking/models.py, tracking/email_service.py, tracking/security.py, tracking/telegram_service.py, init_db.py, seed_data.py, requirements.txt

---

## SECCIÓN 27: ADMIN PANEL AVANZADO (Endpoints Backend)

### FASE 27.10: SOPORTE Y TICKETS (backend) ⏳
**Tiempo:** 3 horas

**Tareas:**
- [ ] Crear modelo SupportTicket en models.py
- [ ] POST /api/admin/tickets - Crear ticket
- [ ] GET /api/admin/tickets - Listar tickets
- [ ] PUT /api/admin/tickets/{id} - Actualizar ticket
- [ ] POST /api/admin/tickets/{id}/reply - Responder ticket

---

### FASE 27.11: MARKETPLACE (backend) ⏳
**Tiempo:** 4 horas

**Tareas:**
- [ ] Crear modelos para marketplace
- [ ] Endpoints CRUD de productos/servicios
- [ ] Endpoints de aprobación
- [ ] Cálculo de comisiones

---

### FASE 27.12: CONFIGURACIÓN SISTEMA (backend) ⏳
**Tiempo:** 3 horas

**Tareas:**
- [ ] Crear modelo SystemConfig
- [ ] GET /api/admin/config - Obtener config
- [ ] PUT /api/admin/config - Actualizar config
- [ ] Validación de valores de configuración

---

### FASE 27.14: BACKUP Y MANTENIMIENTO ⏳
**Tiempo:** 4 horas

**Tareas:**
- [ ] POST /api/admin/backup - Crear backup
- [ ] GET /api/admin/backups - Listar backups
- [ ] POST /api/admin/restore/{id} - Restaurar backup
- [ ] Programación automática de backups

---

### FASE 27.18: SISTEMA DE PUNTUACIÓN DE RIESGO (backend) ⏳ 🟡 ALTA
**Tiempo:** 5 horas

**Tareas:**
- [ ] Modelo RiskScore en models.py
- [ ] Algoritmo de cálculo de riesgo
- [ ] GET /api/admin/users/{id}/risk-score
- [ ] Historial de cambios de score

---

### FASE 27.22: DETECTOR CUENTAS RELACIONADAS (backend) ⏳ 🟡 ALTA
**Tiempo:** 5 horas

**Tareas:**
- [ ] Detectar cuentas con misma IP
- [ ] Detectar cuentas con mismo fingerprint
- [ ] Detectar wallets relacionadas
- [ ] GET /api/admin/users/{id}/related-accounts

---

### FASE 27.25: MONITOREO PATRONES Y ANOMALÍAS (backend) ⏳ 🟡 ALTA
**Tiempo:** 6 horas

**Tareas:**
- [ ] Modelo AnomalyDetection
- [ ] Algoritmo de detección de anomalías
- [ ] Acciones automáticas según tipo
- [ ] GET /api/admin/anomalies

---

## SECCIÓN 30: CORRECCIONES DE AUDITORÍA

### FASE 30.3: HEADERS CSP ⏳ 🟠 MEDIA
**Tiempo:** 1 hora

**Tareas:**
- [ ] Crear middleware @app.after_request
- [ ] Implementar Content-Security-Policy
- [ ] Agregar X-Frame-Options
- [ ] Agregar X-Content-Type-Options

---

### FASE 30.4: LOGGING ESTRUCTURADO ⏳ 🟠 MEDIA
**Tiempo:** 2 horas

**Tareas:**
- [ ] Configurar logging con formato JSON
- [ ] Agregar request_id a logs
- [ ] Logs de errores a archivo separado
- [ ] Rotación de logs

---

## SECCIÓN 31: VERIFICACIÓN DE FUNCIONALIDADES

### FASE 31.4: ESTADÍSTICAS ADMIN VACÍAS (backend) ⏳ 🟡 ALTA
**Tiempo:** 1 hora

**Tareas:**
- [ ] GET /api/admin/stats/overview - Stats generales
- [ ] GET /api/admin/stats/users - Stats usuarios
- [ ] GET /api/admin/stats/transactions - Stats transacciones
- [ ] Datos reales, no mock

---

### FASE 31.7: BACKUP AUTOMÁTICO ⏳ 🟠 MEDIA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Implementar backup programado
- [ ] Retención de backups (últimos 7 días)
- [ ] Backup antes de operaciones críticas
- [ ] Notificación de backup exitoso/fallido

---

### FASE 31.9: RATE LIMITING GLOBAL ⏳ 🟠 MEDIA
**Tiempo:** 2 horas

**Estado:** Parcialmente implementado

**Tareas pendientes:**
- [ ] Verificar rate limiting en todos los endpoints críticos
- [ ] Agregar a endpoints faltantes
- [ ] Configurar por tipo de usuario (premium vs free)

---

### FASE 31.10: MODO MANTENIMIENTO (backend) ⏳ 🟢 BAJA
**Tiempo:** 1 hora

**Tareas:**
- [ ] Crear middleware de mantenimiento
- [ ] POST /api/admin/maintenance/enable
- [ ] POST /api/admin/maintenance/disable
- [ ] Bypass para admins

---

### FASE 31.11: MONITOREO Y ALERTAS ⏳ 🟢 BAJA
**Tiempo:** 3 horas

**Ya implementado:** /api/health endpoint

**Tareas pendientes:**
- [ ] GET /api/admin/system/status con métricas completas
- [ ] Alertas automáticas por Telegram
- [ ] Métricas de base de datos

---


## SECCIÓN 32: LIMPIEZA Y OPTIMIZACIÓN

### FASE 32.3: LIMPIAR DATOS DEMO (backend) ⏳ 🟠 MEDIA
**Tiempo:** 1 hora

**Tareas:**
- [ ] Verificar que demo_2fa_sessions es persistente
- [ ] Limpiar datos de prueba en producción
- [ ] Flag para modo demo

---

## SECCIÓN 33: FEATURES NUEVAS

### FASE 33.1: CHAT PRIVADO (backend) ⏳ 🟠 MEDIA
**Tiempo:** 3 horas

**Tareas:**
- [ ] Crear modelo PrivateMessage en models.py
- [ ] POST /api/messages - Enviar mensaje
- [ ] GET /api/messages/conversations - Listar conversaciones
- [ ] GET /api/messages/{user_id} - Mensajes con usuario
- [ ] Marcar como leído

---

## RESUMEN DE HORAS ESTIMADAS

| Sección | Horas |
|---------|-------|
| 27.x Admin endpoints | 30h |
| 30.x Auditoría | 3h |
| 31.x Verificación | 11h |
| 32.x Limpieza | 1h |
| 33.1 Chat privado | 3h |
| **TOTAL** | **~48 horas** |

---

## ORDEN RECOMENDADO

1. 🟡 **ALTA:** 31.4 → 27.18 → 27.22 → 27.25
2. 🟠 **MEDIA:** 30.3 → 30.4 → 31.7 → 31.9 → 33.1
3. 🟢 **BAJA:** 31.10 → 31.11
