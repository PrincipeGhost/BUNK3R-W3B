# TAREAS - feature/blockchain-services

---

## IDENTIFICACIÓN DEL AGENTE

```
╔═══════════════════════════════════════════════════════════════════╗
║  🔴 RAMA: feature/blockchain-services                             ║
╠═══════════════════════════════════════════════════════════════════╣
║  Archivo de tareas: TAREAS_BLOCKCHAIN-SERVICES.md                 ║
║  Comando para activar: 6 o BLOCKCHAIN                             ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## ARCHIVOS QUE PUEDO EDITAR (EXCLUSIVOS)

| Archivo | Función |
|---------|---------|
| `tracking/b3c_service.py` | Token B3C en TON |
| `tracking/wallet_pool_service.py` | Pool de wallets |
| `tracking/deposit_scheduler.py` | Detección de depósitos |
| `tracking/smspool_service.py` | API números virtuales |
| `tracking/cloudinary_service.py` | Subida de media |
| `tracking/encryption.py` | Encriptación contenido |

---

## ARCHIVOS PROHIBIDOS (NUNCA TOCAR)

```
❌ app.py
❌ tracking/database.py
❌ tracking/models.py
❌ tracking/security.py
❌ static/js/*.js
❌ static/css/*.css
❌ templates/*.html
❌ PROMPT_PENDIENTES_BUNK3R.md
❌ replit.md
❌ Cualquier archivo de otro agente
```

---

## REGLA DE ACTUALIZACIÓN

```
✅ YO ACTUALIZO ESTE ARCHIVO (TAREAS_BLOCKCHAIN-SERVICES.md)
❌ NO TOCO PROMPT_PENDIENTES_BUNK3R.md
❌ NO TOCO archivos de otros agentes
```

Al completar una tarea:
1. Cambiar `[ ]` → `[x]` en ESTE archivo
2. Hacer commit solo de mis archivos de código
3. Crear PR a main

---

## TAREAS COMPLETADAS ✅

### FASE 27.4: WALLETS Y BLOCKCHAIN ✅
- [x] Hot Wallet service
- [x] Wallets de Depósito generation
- [x] Pool de Wallets management
- [x] Consolidación automática
- [x] Detección de depósitos (deposit_scheduler)

### FASE 27.6: NÚMEROS VIRTUALES ✅
- [x] Integración SMSPool API
- [x] Compra de números
- [x] Recepción de SMS
- [x] Balance checking

### Servicios de Media ✅
- [x] Cloudinary upload
- [x] Encriptación de contenido

---

## TAREAS PENDIENTES ⏳

### Optimización Pool de Wallets ⏳
- [ ] Mejorar algoritmo de consolidación
- [ ] Agregar retry en fallos de red
- [ ] Mejorar logs de errores
- [ ] Optimizar polling de depósitos

### Integración TON Avanzada ⏳
- [ ] Soporte para Jettons (tokens)
- [ ] Transacciones batch
- [ ] Mejor manejo de fees dinámicos

### SMSPool Mejoras ⏳
- [ ] Cache de precios por servicio
- [ ] Reintento automático si falla
- [ ] Más proveedores de SMS

### Sección 29: INTEGRACIONES EXTERNAS ⏳
- [ ] API Telegram (notificaciones owner)
- [ ] Webhook para eventos críticos
- [ ] Integración con exchange (precio TON/USD)

### Sección 30: SEGURIDAD BLOCKCHAIN ⏳
- [ ] Rate limiting por wallet
- [ ] Detección de transacciones sospechosas
- [ ] Alerta de wallets comprometidas

---

## PUNTO DE GUARDADO

**Fecha:** 08/12/2025 01:30
**Última tarea trabajada:** Pool de wallets funcionando
**Estado:** Esperando instrucciones

### Próximos pasos
1. Optimización del pool de wallets
2. Mejorar manejo de errores

### Notas
- Este archivo es exclusivo de la rama feature/blockchain-services
- Solo este agente puede editarlo

