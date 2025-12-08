# TAREAS - feature/backend-api

---

## IDENTIFICACIÓN DEL AGENTE

```
╔═══════════════════════════════════════════════════════════════════╗
║  🟡 RAMA: feature/backend-api                                     ║
╠═══════════════════════════════════════════════════════════════════╣
║  Archivo de tareas: TAREAS_BACKEND-API.md                         ║
║  Comando para activar: 4 o BACKEND                                ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## ARCHIVOS QUE PUEDO EDITAR (EXCLUSIVOS)

| Archivo | Función |
|---------|---------|
| `app.py` | Endpoints API y rutas |
| `tracking/database.py` | Operaciones BD |
| `tracking/models.py` | Modelos de datos |
| `tracking/email_service.py` | Servicio de emails |
| `tracking/security.py` | Seguridad y 2FA |
| `init_db.py` | Inicialización BD |
| `requirements.txt` | Dependencias Python |

---

## ARCHIVOS PROHIBIDOS (NUNCA TOCAR)

```
❌ static/js/*.js
❌ static/css/*.css
❌ templates/*.html
❌ tracking/b3c_service.py
❌ tracking/wallet_pool_service.py
❌ tracking/deposit_scheduler.py
❌ tracking/smspool_service.py
❌ PROMPT_PENDIENTES_BUNK3R.md
❌ replit.md
❌ Cualquier archivo de otro agente
```

---

## REGLA DE ACTUALIZACIÓN

```
✅ YO ACTUALIZO ESTE ARCHIVO (TAREAS_BACKEND-API.md)
❌ NO TOCO PROMPT_PENDIENTES_BUNK3R.md
❌ NO TOCO archivos de otros agentes
```

Al completar una tarea:
1. Cambiar `[ ]` → `[x]` en ESTE archivo
2. Hacer commit solo de mis archivos de código
3. Crear PR a main

---

## TAREAS COMPLETADAS ✅

### FASE 27.2: GESTIÓN DE USUARIOS (Backend) ✅
- [x] Endpoints para lista de usuarios
- [x] Endpoint detalle de usuario
- [x] Endpoints acciones sobre usuario (ban, unban, etc.)
- [x] Detección de fraude

### FASE 27.3: TRANSACCIONES Y FINANZAS (Backend) ✅
- [x] Endpoints dashboard financiero
- [x] Endpoints lista transacciones
- [x] Endpoints compras B3C
- [x] Endpoints retiros
- [x] Endpoints transferencias P2P

### FASE 27.5: CONTENIDO Y PUBLICACIONES (Backend) ✅
- [x] Endpoints moderación de contenido
- [x] Endpoints reportes
- [x] Endpoints hashtags

### FASE 27.7: GESTIÓN DE BOTS (Backend) ✅
- [x] Endpoints lista bots
- [x] Endpoints estadísticas
- [x] Endpoints configuración

### FASE 27.8: LOGS Y AUDITORÍA (Backend) ✅
- [x] Endpoints logs admin
- [x] Endpoints logs errores
- [x] Endpoints logs login
- [x] Endpoints exportación

### FASE 27.9: ANALYTICS (Backend) ✅
- [x] Endpoints métricas usuarios
- [x] Endpoints uso de app
- [x] Endpoints conversión

---

## TAREAS PENDIENTES ⏳

### FASE 27.10: SOPORTE Y TICKETS (Backend) ⏳
- [ ] Modelo Ticket en database.py
- [ ] POST /api/admin/tickets - Crear ticket
- [ ] GET /api/admin/tickets - Lista tickets
- [ ] GET /api/admin/tickets/<id> - Detalle ticket
- [ ] PUT /api/admin/tickets/<id> - Actualizar ticket
- [ ] POST /api/admin/tickets/<id>/reply - Responder
- [ ] GET /api/admin/faqs - Lista FAQs
- [ ] POST /api/admin/faqs - Crear FAQ
- [ ] POST /api/admin/notifications/broadcast - Mensaje masivo

### FASE 27.11: MARKETPLACE (Backend) ⏳
- [ ] Modelo Listing en database.py
- [ ] Modelo Dispute en database.py
- [ ] Endpoints CRUD listings
- [ ] Endpoints disputas

### FASE 27.12: CONFIGURACIÓN DEL SISTEMA (Backend) ⏳
- [ ] GET /api/admin/config - Obtener configuración
- [ ] PUT /api/admin/config - Actualizar configuración
- [ ] POST /api/admin/maintenance - Modo mantenimiento
- [ ] GET /api/admin/system-status - Estado del sistema

### FASE 27.14: BACKUP Y MANTENIMIENTO (Backend) ⏳
- [ ] POST /api/admin/backup - Crear backup
- [ ] GET /api/admin/backups - Lista backups
- [ ] GET /api/admin/server-status - Estado servidor
- [ ] POST /api/admin/cache/clear - Limpiar cache

---

## PUNTO DE GUARDADO

**Fecha:** 08/12/2025 01:30
**Última tarea trabajada:** Sección 27.9 endpoints completados
**Estado:** Esperando instrucciones

### Próximos pasos
1. Sección 27.10 - Endpoints de Tickets
2. Modelo Ticket en database.py

### Notas
- Este archivo es exclusivo de la rama feature/backend-api
- Solo este agente puede editarlo

