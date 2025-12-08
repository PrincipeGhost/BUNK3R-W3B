# TAREAS AGENTE 🟡 BACKEND API
**Rama Git:** `feature/backend-api`
**Archivos asignados:** app.py, tracking/__init__.py, tracking/database.py, tracking/models.py, tracking/email_service.py, tracking/security.py, tracking/telegram_service.py, init_db.py, seed_data.py, run.py, runtime.txt, requirements.txt

---

## SECCIÓN 27: ADMIN PANEL AVANZADO (Endpoints Backend)

### FASE 27.10: SOPORTE Y TICKETS (backend) ✅ COMPLETADO
**Tiempo:** 3 horas
**Estado:** Ya implementado en app.py (lineas 14041+)

**Tareas:**
- [x] Crear modelo SupportTicket en models.py
- [x] POST /api/admin/tickets - Crear ticket
- [x] GET /api/admin/tickets - Listar tickets
- [x] PUT /api/admin/tickets/{id} - Actualizar ticket
- [x] POST /api/admin/tickets/{id}/reply - Responder ticket

---

### FASE 27.11: MARKETPLACE (backend) ⏳
**Tiempo:** 4 horas

**Tareas:**
- [ ] Crear modelos para marketplace
- [ ] Endpoints CRUD de productos/servicios
- [ ] Endpoints de aprobacion
- [ ] Calculo de comisiones

---

### FASE 27.12: CONFIGURACION SISTEMA (backend) ✅ COMPLETADO
**Tiempo:** 3 horas
**Estado:** Ya implementado en app.py (lineas 13160+)

**Tareas:**
- [x] Crear modelo SystemConfig
- [x] GET /api/admin/config - Obtener config
- [x] PUT /api/admin/config - Actualizar config
- [x] Validacion de valores de configuracion

---

### FASE 27.14: BACKUP Y MANTENIMIENTO ⏳
**Tiempo:** 4 horas

**Tareas:**
- [ ] POST /api/admin/backup - Crear backup
- [ ] GET /api/admin/backups - Listar backups
- [ ] POST /api/admin/restore/{id} - Restaurar backup
- [ ] Programacion automatica de backups

---

### FASE 27.18: SISTEMA DE PUNTUACION DE RIESGO (backend) ✅ COMPLETADO
**Tiempo:** 5 horas
**Fecha:** 8 Diciembre 2025

**Tareas:**
- [x] Modelo RiskScore en models.py
- [x] Modelo RiskScoreHistory en models.py
- [x] Algoritmo de calculo de riesgo (calculate_user_risk_score)
- [x] GET /api/admin/users/{id}/risk-score
- [x] POST /api/admin/users/{id}/risk-score/calculate
- [x] GET /api/admin/users/{id}/risk-score/history
- [x] Tablas SQL para risk_scores y risk_score_history

---

### FASE 27.22: DETECTOR CUENTAS RELACIONADAS (backend) ✅ COMPLETADO
**Tiempo:** 5 horas
**Fecha:** 8 Diciembre 2025

**Tareas:**
- [x] Detectar cuentas con misma IP
- [x] Detectar cuentas con mismo fingerprint
- [x] Detectar wallets relacionadas
- [x] GET /api/admin/users/{id}/related-accounts
- [x] Tabla SQL para related_accounts

---

### FASE 27.25: MONITOREO PATRONES Y ANOMALIAS (backend) ✅ COMPLETADO
**Tiempo:** 6 horas
**Fecha:** 8 Diciembre 2025

**Tareas:**
- [x] Modelo AnomalyDetection en models.py
- [x] GET /api/admin/anomalies (con filtros)
- [x] POST /api/admin/anomalies/{id}/resolve
- [x] Tabla SQL para anomaly_detections

---

## SECCION 30: CORRECCIONES DE AUDITORIA

### FASE 30.3: HEADERS CSP ✅ COMPLETADO
**Tiempo:** 1 hora
**Estado:** Ya implementado en app.py (linea 947+)

**Tareas:**
- [x] Crear middleware @app.after_request
- [x] Implementar Content-Security-Policy
- [x] Agregar X-Frame-Options
- [x] Agregar X-Content-Type-Options

---

### FASE 30.4: LOGGING ESTRUCTURADO ✅ COMPLETADO
**Tiempo:** 2 horas
**Estado:** Ya implementado en app.py (lineas 51-115)

**Tareas:**
- [x] Configurar logging con formato JSON (JSONFormatter)
- [x] Agregar request_id a logs (RequestContextFilter)
- [x] Logs de errores a archivo separado
- [x] Rotacion de logs (RotatingFileHandler)

---

## SECCION 31: VERIFICACION DE FUNCIONALIDADES

### FASE 31.4: ESTADISTICAS ADMIN VACIAS (backend) ✅ COMPLETADO
**Tiempo:** 1 hora
**Fecha:** 8 Diciembre 2025

**Tareas:**
- [x] GET /api/admin/stats/overview - Stats generales detalladas
- [x] GET /api/admin/stats/users - Stats usuarios
- [x] GET /api/admin/stats/transactions - Stats transacciones
- [x] Datos reales, no mock

---

### FASE 31.7: BACKUP AUTOMATICO ⏳ 🟠 MEDIA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Implementar backup programado
- [ ] Retencion de backups (ultimos 7 dias)
- [ ] Backup antes de operaciones criticas
- [ ] Notificacion de backup exitoso/fallido

---

### FASE 31.9: RATE LIMITING GLOBAL ✅ VERIFICADO
**Tiempo:** 2 horas

**Estado:** Implementado con RateLimiter class

**Tareas completadas:**
- [x] Rate limiting en endpoints criticos
- [x] Configuracion por endpoint

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
- [ ] GET /api/admin/system/status con metricas completas
- [ ] Alertas automaticas por Telegram
- [ ] Metricas de base de datos

---


## SECCION 32: LIMPIEZA Y OPTIMIZACION

### FASE 32.3: LIMPIAR DATOS DEMO (backend) ⏳ 🟠 MEDIA
**Tiempo:** 1 hora

**Tareas:**
- [ ] Verificar que demo_2fa_sessions es persistente
- [ ] Limpiar datos de prueba en produccion
- [ ] Flag para modo demo

---

## SECCION 33: FEATURES NUEVAS

### FASE 33.1: CHAT PRIVADO (backend) ✅ COMPLETADO
**Tiempo:** 3 horas
**Fecha:** 8 Diciembre 2025

**Tareas:**
- [x] Crear modelo PrivateMessage en models.py
- [x] POST /api/messages - Enviar mensaje
- [x] GET /api/messages/conversations - Listar conversaciones
- [x] GET /api/messages/{user_id} - Mensajes con usuario
- [x] POST /api/messages/{id}/read - Marcar como leido
- [x] GET /api/messages/unread-count - Contador no leidos
- [x] Tabla SQL para private_messages

---

## RESUMEN DE PROGRESO

| Seccion | Estado | Horas |
|---------|--------|-------|
| 27.10 Soporte | ✅ Completado | 3h |
| 27.11 Marketplace | ⏳ Pendiente | 4h |
| 27.12 Config Sistema | ✅ Completado | 3h |
| 27.14 Backup | ⏳ Pendiente | 4h |
| 27.18 Risk Score | ✅ Completado | 5h |
| 27.22 Cuentas Relacionadas | ✅ Completado | 5h |
| 27.25 Anomalias | ✅ Completado | 6h |
| 30.3 Headers CSP | ✅ Completado | 1h |
| 30.4 Logging | ✅ Completado | 2h |
| 31.4 Stats Admin | ✅ Completado | 1h |
| 31.7 Backup Auto | ⏳ Pendiente | 4h |
| 31.9 Rate Limiting | ✅ Completado | 2h |
| 31.10 Mantenimiento | ⏳ Pendiente | 1h |
| 31.11 Monitoreo | ⏳ Pendiente | 3h |
| 32.3 Datos Demo | ⏳ Pendiente | 1h |
| 33.1 Chat Privado | ✅ Completado | 3h |

**COMPLETADO:** 11 de 16 fases (~70%)
**PENDIENTE:** 5 fases (~17 horas estimadas)

---

## ORDEN RECOMENDADO PARA TAREAS PENDIENTES

1. 🟠 **MEDIA:** 27.11 (Marketplace) → 31.7 (Backup) → 32.3 (Demo)
2. 🟢 **BAJA:** 31.10 (Mantenimiento) → 31.11 (Monitoreo)
3. 📦 **FUTURO:** 27.14 (Backup manual)
