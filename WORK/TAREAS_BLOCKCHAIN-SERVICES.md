# TAREAS AGENTE 🔴 BLOCKCHAIN & SERVICIOS EXTERNOS
**Rama Git:** `feature/blockchain-services`
**Archivos asignados:** 
- routes/blockchain_routes.py (endpoints /api/b3c/*, /api/wallet/*)
- tracking/b3c_service.py, tracking/wallet_pool_service.py
- tracking/deposit_scheduler.py, tracking/smspool_service.py
- tracking/legitsms_service.py, tracking/cloudinary_service.py, tracking/encryption.py

---

## SECCION 0: MIGRACION DE RUTAS (PRIORITARIO)

### FASE 0.1: MIGRAR ENDPOINTS BLOCKCHAIN A routes/blockchain_routes.py 🔴 CRITICA
**Tiempo:** 4 horas
**Fecha creacion:** 8 Diciembre 2025

**Contexto:**
Migrar todos los endpoints de B3C y wallets desde app.py a routes/blockchain_routes.py
para separar responsabilidades y evitar conflictos entre agentes.

**Endpoints a migrar (lineas aproximadas en app.py):**
- /api/b3c/* (3594-4815) - Compra, venta, balance, transacciones, depositos
- /api/wallet/* (3403-3569, 5195) - Conexion wallet, balance, creditos

**Tareas:**
- [ ] Leer app.py y ubicar todos los endpoints de b3c/wallet
- [ ] Copiar endpoints a routes/blockchain_routes.py
- [ ] Cambiar @app.route por @blockchain_bp.route
- [ ] Importar dependencias (db_manager, wallet_pool_service, b3c_service)
- [ ] Registrar blueprint en app.py
- [ ] Probar que todos los endpoints funcionan
- [ ] Eliminar endpoints originales de app.py

**Criterios de aceptacion:**
- [ ] Todos los endpoints /api/b3c/* responden correctamente
- [ ] Todos los endpoints /api/wallet/* responden correctamente
- [ ] No hay errores en logs

---

## SECCIÓN 29: CONFIGURACIÓN USUARIO

### FASE 29.7: SECCIÓN WALLET (blockchain) ⏳ 🔴 CRÍTICA
**Tiempo:** 2 horas

**Tareas:**
- [ ] Verificar integración TON Connect
- [ ] Validar direcciones de wallet
- [ ] Whitelist de direcciones de retiro
- [ ] Confirmación 2FA para retiros grandes

---

## SECCIÓN 30: CORRECCIONES DE AUDITORÍA

### FASE 30.5: ENCRIPTACIÓN ⏳ 🟠 MEDIA
**Tiempo:** 2 horas

**Tareas:**
- [ ] Verificar encriptación de contenido sensible
- [ ] Auditar uso de PBKDF2
- [ ] Verificar que keys no están hardcodeadas
- [ ] Documentar flujo de encriptación

---

## SECCIÓN 31: VERIFICACIÓN DE FUNCIONALIDADES

### FASE 31.8: NOTIFICACIONES TELEGRAM ⏳ 🟠 MEDIA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Verificar bot de Telegram configurado
- [ ] Notificaciones de depósitos detectados
- [ ] Notificaciones de transacciones grandes
- [ ] Alertas de errores críticos
- [ ] Configurar canales de notificación

---

### FASE 31.12: CLOUDINARY FALLBACK ✅ VERIFICADO
**Estado:** Completado 7 Diciembre 2025

**Ya implementado:**
- [x] Verifica self.configured antes de operaciones
- [x] Retorna error claro si no configurado
- [x] Manejo de excepciones en todas las funciones

---

## SECCIÓN 32: LIMPIEZA Y OPTIMIZACIÓN

### FASE 32.2: IMPLEMENTAR LEGIT SMS API ⏳ 🟡 ALTA
**Tiempo:** 4 horas

**Problema actual:**
```python
# app.py línea 10631
return jsonify({'success': False, 'error': 'Legit SMS not yet implemented'}), 501
```

**Tareas:**
- [ ] Investigar API de Legit SMS
- [ ] Crear servicio tracking/legitsms_service.py
- [ ] Implementar endpoints:
  - [ ] Obtener lista de países
  - [ ] Obtener servicios disponibles
  - [ ] Comprar número
  - [ ] Verificar estado del SMS
  - [ ] Cancelar orden
- [ ] Integrar con sistema de números virtuales
- [ ] Agregar fallback a SMSPool

---

## SECCIÓN 34: COMPONENTES AVANZADOS

### FASE 34.A: BÚSQUEDA EN VIVO ⏳
**Tiempo:** 6 horas

**Tareas:**
- [ ] Integrar Serper API para búsqueda web
- [ ] Implementar Playwright para scraping
- [ ] Cache de resultados de búsqueda
- [ ] Rate limiting de búsquedas

---

### FASE 34.B: MEMORIA VECTORIAL ⏳
**Tiempo:** 8 horas

**Tareas:**
- [ ] Integrar ChromaDB
- [ ] Generar embeddings de código
- [ ] Búsqueda semántica de contexto
- [ ] Persistencia de memoria entre sesiones

---

## OPTIMIZACIÓN POOL DE WALLETS

### FASE WALLETS.1: OPTIMIZACIÓN POOL ⏳ 🟡 ALTA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Mejorar algoritmo de selección de wallet
- [ ] Implementar rotación automática
- [ ] Monitoreo de balance mínimo
- [ ] Alertas de wallets con bajo balance
- [ ] Limpieza de wallets no usadas

---

### FASE WALLETS.2: SEGURIDAD WALLETS ⏳ 🔴 CRÍTICA
**Tiempo:** 3 horas

**Tareas:**
- [ ] Auditar almacenamiento de private keys
- [ ] Verificar encriptación de seeds
- [ ] Implementar multi-sig donde aplique
- [ ] Logging de todas las transacciones

---

## INTEGRACIÓN TON AVANZADA

### FASE TON.1: TRANSACCIONES ⏳ 🟡 ALTA
**Tiempo:** 5 horas

**Tareas:**
- [ ] Verificar todos los endpoints de transacciones
- [ ] Implementar confirmación de transacciones
- [ ] Manejo de transacciones fallidas
- [ ] Reintentos automáticos

---

### FASE TON.2: SMART CONTRACTS ⏳ 🟠 MEDIA
**Tiempo:** 6 horas

**Tareas:**
- [ ] Verificar contrato B3C
- [ ] Implementar funciones de contrato
- [ ] Eventos de contrato
- [ ] Monitoreo de estado

---

## SECCIÓN 30: SEGURIDAD BLOCKCHAIN

### FASE 30.BLOCKCHAIN: AUDITORÍA SEGURIDAD ⏳ 🔴 CRÍTICA
**Tiempo:** 4 horas

**Tareas:**
- [ ] Auditar todas las llamadas a TON API
- [ ] Verificar validación de direcciones
- [ ] Verificar montos antes de enviar
- [ ] Implementar límites de transacción
- [ ] Logs de auditoría de todas las operaciones

---

## RESUMEN DE HORAS ESTIMADAS

| Sección | Horas |
|---------|-------|
| 29.7 Wallet Config | 2h |
| 30.5 Encriptación | 2h |
| 31.8 Telegram | 4h |
| 32.2 Legit SMS | 4h |
| 34.A Búsqueda | 6h |
| 34.B Memoria | 8h |
| Wallets Pool | 7h |
| TON Avanzado | 11h |
| Seguridad | 4h |
| **TOTAL** | **~48 horas** |

---

## ORDEN RECOMENDADO

1. 🔴 **CRÍTICO:** 29.7 → WALLETS.2 → 30.BLOCKCHAIN
2. 🟡 **ALTA:** 32.2 → WALLETS.1 → TON.1
3. 🟠 **MEDIA:** 31.8 → 30.5 → TON.2
4. 🟢 **BAJA:** 34.A → 34.B
