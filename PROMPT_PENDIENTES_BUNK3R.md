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
| Última actualización | 5 Diciembre 2025 |
| Sección actual | SECCIÓN 17-20 |
| Total secciones | 20 |
| Completadas | 14 ✅ |
| Pendientes | 4 ⏳ |
| En progreso | 0 |

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

**OBLIGATORIO:**
- Respaldo antes de cambios mayores
- Validar entradas del usuario
- Mantener integridad del proyecto

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
## SECCIÓN 17: AUDITORÍA COMPLETA DE PAGOS Y RETIROS B3C ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** CRÍTICA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Error TON_CONNECT_SDK_ERROR detectado por usuario
**Estado:** PENDIENTE

---

### ERROR DETECTADO:
```
Error: [TON_CONNECT_SDK_ERROR] z
SendTransactionRequest validation failed:
Invalid 'payload' in message at index 0
```

**Ubicación:** Función `buildTextCommentPayload()` en `static/js/app.js` (líneas 4318-4338)
**Causa raíz:** El payload se construye de forma incorrecta para TON Connect SDK

---

### PROMPT MAESTRO 17: SISTEMA DE PAGOS TON CONNECT

**OBJETIVO:** Corregir el error de payload y hacer que TODOS los pagos funcionen correctamente.

---

#### FASE 17.1: Corregir buildTextCommentPayload() ⏳

**Código actual problemático (líneas 4318-4338):**
```javascript
buildTextCommentPayload(comment) {
    if (!comment) return undefined;
    try {
        const textBytes = new TextEncoder().encode(comment);
        const payload = new Uint8Array(textBytes.length + 4);
        payload[0] = 0; // Opcode incorrecto
        payload[1] = 0;
        payload[2] = 0;
        payload[3] = 0;
        payload.set(textBytes, 4);
        let binary = '';
        for (let i = 0; i < payload.length; i++) {
            binary += String.fromCharCode(payload[i]);
        }
        return btoa(binary); // NO ES BOC VÁLIDO
    } catch (e) {
        console.error('Error building comment payload:', e);
        return undefined;
    }
}
```

**PROBLEMA:** TON Connect espera un Cell serializado (BOC), no un array de bytes en base64.

**TAREAS:**
- [ ] 17.1.1 Investigar formato correcto de payload para TON Connect
- [ ] 17.1.2 Opción A: Enviar transacción SIN payload (solo monto y destino)
- [ ] 17.1.3 Opción B: Usar librería @ton/ton para construir Cell correctamente
- [ ] 17.1.4 Probar que el modal de wallet se abra sin errores
- [ ] 17.1.5 Verificar que la transacción se envíe correctamente

**SOLUCIÓN PROPUESTA (sin payload):**
```javascript
const transaction = {
    validUntil: Math.floor(Date.now() / 1000) + 600,
    messages: [
        {
            address: response.hotWallet,
            amount: amountNano
            // SIN payload - usar verificación por monto/timing
        }
    ]
};
```

---

#### FASE 17.2: Probar TODOS los Botones de Compra B3C ⏳

**Botones a probar uno por uno:**
- [ ] 17.2.1 Botón "0.5 TON" (Prueba)
- [ ] 17.2.2 Botón "1 TON"
- [ ] 17.2.3 Botón "5 TON" (Popular)
- [ ] 17.2.4 Botón "10 TON"
- [ ] 17.2.5 Botón "20 TON"
- [ ] 17.2.6 Input personalizado (monto custom)

**Checklist por cada botón:**
1. ¿Se muestra toast "Preparando compra..."?
2. ¿Se abre modal de TON Connect/Wallet?
3. ¿El monto mostrado es correcto?
4. ¿La wallet destino es la correcta (hotWallet)?
5. ¿No hay error de payload?
6. ¿Se puede confirmar la transacción?
7. ¿Se verifica automáticamente después?
8. ¿Se acreditan los B3C al balance?

---

#### FASE 17.3: Verificar Sistema de Retiros ⏳

**Endpoints a verificar:**
- [ ] 17.3.1 `POST /api/b3c/withdraw` - Crear solicitud
- [ ] 17.3.2 `GET /api/b3c/withdraw/{id}/status` - Estado
- [ ] 17.3.3 `GET /api/admin/b3c/withdrawals` - Lista admin
- [ ] 17.3.4 `POST /api/admin/b3c/withdrawals/{id}/process` - Procesar

**UI a verificar:**
- [ ] 17.3.5 Modal de retiro se abre correctamente
- [ ] 17.3.6 Input de wallet destino funciona
- [ ] 17.3.7 Validación de dirección TON
- [ ] 17.3.8 Confirmación antes de enviar
- [ ] 17.3.9 Feedback de estado (pending, completed)

---

#### FASE 17.4: Verificar buildJettonTransferPayload() ⏳

**Código problemático (líneas 5897-5906):**
```javascript
buildJettonTransferPayload(destination, amount, comment) {
    return btoa(JSON.stringify({
        op: 0xf8a7ea5,
        queryId: Date.now(),
        amount: amount,
        destination: destination,
        responseDestination: destination,
        forwardAmount: '1',
        forwardPayload: comment
    }));
}
```

**PROBLEMA:** JSON stringificado NO es un formato válido para Jetton Transfer.

**TAREAS:**
- [ ] 17.4.1 Determinar si esta función se usa activamente
- [ ] 17.4.2 Si se usa, implementar Cell construction correcta
- [ ] 17.4.3 Si no se usa, marcar como deprecated o eliminar

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 17:
- [ ] Error TON_CONNECT_SDK_ERROR eliminado
- [ ] Todos los botones de compra funcionan
- [ ] No hay errores en consola del navegador
- [ ] Transacciones se envían correctamente
- [ ] Balance se actualiza después de compra

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 18: AUDITORÍA DE NÚMEROS VIRTUALES ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** ALTA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Usuario reporta "sin servicio" y botón atrás cierra app
**Estado:** PENDIENTE

---

### ERRORES DETECTADOS:

**Error 1: Botón "Atrás" cierra toda la app**
- **Ubicación:** `static/js/virtual-numbers.js` líneas 624-630
- **Código problemático:**
```javascript
function goBack() {
    if (tg) {
        tg.close(); // CIERRA TODA LA MINI APP!
    } else {
        window.location.href = '/';
    }
}
```

**Error 2: "Sin servicio" al cargar países/servicios**
- **Posible causa:** API key de SMSPool no configurada
- **Ubicación:** `tracking/smspool_service.py` líneas 19-22
```python
self.api_key = api_key or os.environ.get('SMSPOOL_API_KEY')
if not self.api_key:
    logger.warning("SMSPOOL_API_KEY not configured")
```

---

### PROMPT MAESTRO 18: NÚMEROS VIRTUALES COMPLETO

**OBJETIVO:** Hacer que toda la sección de números virtuales funcione perfectamente.

---

#### FASE 18.1: Corregir Botón "Atrás" ⏳

**TAREAS:**
- [ ] 18.1.1 Modificar `goBack()` para navegar en lugar de cerrar
- [ ] 18.1.2 Implementar navegación a pantalla principal
- [ ] 18.1.3 Probar en ambiente Telegram y fuera de Telegram

**SOLUCIÓN PROPUESTA:**
```javascript
function goBack() {
    // Navegar a la pantalla principal en lugar de cerrar
    window.location.href = '/';
}
```

---

#### FASE 18.2: Verificar Carga de Países ⏳

**Endpoint:** `/api/vn/countries?provider=smspool`

**TAREAS:**
- [ ] 18.2.1 Verificar que SMSPOOL_API_KEY esté configurada
- [ ] 18.2.2 Probar endpoint en navegador/consola
- [ ] 18.2.3 Verificar respuesta JSON válida
- [ ] 18.2.4 Verificar que se renderizan los países
- [ ] 18.2.5 Verificar banderas y nombres correctos

**Checklist de respuesta esperada:**
```json
{
  "success": true,
  "countries": [
    {"id": "1", "name": "United States", "flag": "🇺🇸"},
    {"id": "7", "name": "Russia", "flag": "🇷🇺"},
    ...
  ]
}
```

---

#### FASE 18.3: Verificar Carga de Servicios ⏳

**Endpoint:** `/api/vn/services?provider=smspool&country={countryId}`

**TAREAS:**
- [ ] 18.3.1 Seleccionar un país
- [ ] 18.3.2 Verificar que servicios se carguen
- [ ] 18.3.3 Verificar precios correctos en BUNK3RCO1N
- [ ] 18.3.4 Verificar iconos de servicios
- [ ] 18.3.5 Verificar que botones de servicio funcionen

**Servicios esperados:**
- WhatsApp, Telegram, Instagram, Facebook, TikTok
- Google, Gmail, Microsoft, Apple
- Netflix, Spotify, Discord, Steam
- PayPal, Binance, Coinbase
- Uber, Tinder, etc.

---

#### FASE 18.4: Verificar Compra de Número ⏳

**Endpoint:** `POST /api/vn/purchase`

**TAREAS:**
- [ ] 18.4.1 Seleccionar país + servicio
- [ ] 18.4.2 Verificar que balance sea suficiente
- [ ] 18.4.3 Hacer clic en "Comprar"
- [ ] 18.4.4 Verificar que se descuente del balance
- [ ] 18.4.5 Verificar que aparezca número asignado
- [ ] 18.4.6 Verificar indicador "Esperando SMS..."

---

#### FASE 18.5: Verificar Recepción de SMS ⏳

**Endpoint:** `/api/vn/check/{orderId}`

**TAREAS:**
- [ ] 18.5.1 Verificar polling automático funciona
- [ ] 18.5.2 Verificar backoff exponencial (2s→4s→8s...)
- [ ] 18.5.3 Verificar botón "Verificar" manual
- [ ] 18.5.4 Verificar que código SMS se muestre
- [ ] 18.5.5 Verificar botón "Copiar" funciona

---

#### FASE 18.6: Verificar Cancelación ⏳

**Endpoint:** `POST /api/vn/cancel/{orderId}`

**TAREAS:**
- [ ] 18.6.1 Verificar confirmación antes de cancelar
- [ ] 18.6.2 Verificar reembolso parcial
- [ ] 18.6.3 Verificar que balance se actualice
- [ ] 18.6.4 Verificar que orden desaparezca de activos

---

#### FASE 18.7: Verificar Historial ⏳

**Endpoint:** `/api/vn/history`

**TAREAS:**
- [ ] 18.7.1 Verificar que historial cargue
- [ ] 18.7.2 Verificar filtro por estado
- [ ] 18.7.3 Verificar filtro por servicio
- [ ] 18.7.4 Verificar filtro por fecha
- [ ] 18.7.5 Verificar información correcta en cada item

---

#### FASE 18.8: Verificar UI/UX Completo ⏳

**TAREAS:**
- [ ] 18.8.1 Pestañas funcionan (Comprar, Activos, Historial)
- [ ] 18.8.2 Búsqueda de países funciona
- [ ] 18.8.3 Búsqueda de servicios funciona
- [ ] 18.8.4 Skeleton loaders mientras carga
- [ ] 18.8.5 Toasts de éxito/error aparecen
- [ ] 18.8.6 Loading overlay durante operaciones

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 18:
- [ ] Botón "Atrás" navega correctamente (no cierra app)
- [ ] Países se cargan con banderas
- [ ] Servicios se cargan con precios
- [ ] Compra de número funciona
- [ ] SMS se recibe y muestra
- [ ] Cancelación funciona con reembolso
- [ ] Historial muestra todas las órdenes
- [ ] No hay errores en consola

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 19: TRANSFERENCIAS DE B3C ENTRE USUARIOS ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** ALTA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Funcionalidad crítica para economía interna
**Estado:** PENDIENTE

---

### PROMPT MAESTRO 19: TRANSFERENCIAS ENTRE USUARIOS

**OBJETIVO:** Implementar y verificar sistema completo de transferencias P2P.

---

#### FASE 19.1: Verificar/Crear Endpoint de Transferencia ⏳

**Endpoint esperado:** `POST /api/b3c/transfer`

**TAREAS:**
- [ ] 19.1.1 Buscar si existe endpoint de transferencia
- [ ] 19.1.2 Si no existe, crear endpoint:
```python
@app.route('/api/b3c/transfer', methods=['POST'])
def transfer_b3c():
    # Validar usuario origen
    # Validar usuario destino (por username o wallet)
    # Validar monto suficiente
    # Descontar de origen
    # Acreditar a destino
    # Registrar transacción
    # Notificar a ambos usuarios
```

- [ ] 19.1.3 Implementar validaciones:
  - Monto mínimo
  - Monto máximo
  - Usuario destino existe
  - Balance suficiente
  - No auto-transferencia

---

#### FASE 19.2: UI de Transferencia ⏳

**TAREAS:**
- [ ] 19.2.1 Verificar botón "Transferir" en wallet
- [ ] 19.2.2 Modal de transferencia con:
  - Input de destinatario (username o wallet)
  - Input de monto
  - Preview de comisión (si aplica)
  - Botón confirmar
  - Botón cancelar

- [ ] 19.2.3 Validaciones en frontend:
  - Formato de username/wallet
  - Monto numérico positivo
  - Balance suficiente

---

#### FASE 19.3: Búsqueda de Usuario Destino ⏳

**TAREAS:**
- [ ] 19.3.1 Endpoint para buscar usuario: `/api/users/search?q={query}`
- [ ] 19.3.2 Autocompletado mientras escribe
- [ ] 19.3.3 Mostrar avatar y username del destinatario
- [ ] 19.3.4 Confirmar usuario correcto antes de enviar

---

#### FASE 19.4: Historial de Transferencias ⏳

**TAREAS:**
- [ ] 19.4.1 Mostrar transferencias en historial de transacciones
- [ ] 19.4.2 Distinguir "Enviado a @usuario" vs "Recibido de @usuario"
- [ ] 19.4.3 Filtrar por tipo: envíos, recibidos

---

#### FASE 19.5: Notificaciones ⏳

**TAREAS:**
- [ ] 19.5.1 Notificación al receptor: "Has recibido X B3C de @usuario"
- [ ] 19.5.2 Notificación al emisor: "Transferencia exitosa a @usuario"
- [ ] 19.5.3 Push notification si está habilitado

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 19:
- [ ] Botón "Transferir" funciona
- [ ] Se puede buscar usuario destino
- [ ] Transferencia se ejecuta correctamente
- [ ] Balances se actualizan en tiempo real
- [ ] Historial muestra transferencias
- [ ] Notificaciones funcionan

---

## ════════════════════════════════════════════════════════════════
## SECCIÓN 20: CONEXIÓN DE WALLET Y SINCRONIZACIÓN ⏳
## ════════════════════════════════════════════════════════════════

**Prioridad:** ALTA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Funcionalidad base para todo el sistema de pagos
**Estado:** PENDIENTE

---

### PROMPT MAESTRO 20: WALLET CONNECT Y SYNC

**OBJETIVO:** Verificar que toda la conexión de wallet funcione perfectamente.

---

#### FASE 20.1: Verificar TON Connect Initialization ⏳

**Ubicación:** `static/js/app.js` líneas 3587-3624

**TAREAS:**
- [ ] 20.1.1 Verificar que tonconnect-manifest.json esté accesible
- [ ] 20.1.2 Verificar que TonConnectUI se inicialice
- [ ] 20.1.3 Verificar `onStatusChange` callback
- [ ] 20.1.4 Verificar reconexión automática de wallet guardada

---

#### FASE 20.2: Verificar Botón "Conectar Wallet" ⏳

**TAREAS:**
- [ ] 20.2.1 Verificar que botón sea visible cuando no hay wallet
- [ ] 20.2.2 Verificar que se abra modal de TON Connect
- [ ] 20.2.3 Verificar opciones: Telegram Wallet, Tonkeeper, etc.
- [ ] 20.2.4 Verificar que al conectar, se guarde la wallet

---

#### FASE 20.3: Verificar Sincronización con Servidor ⏳

**Endpoint:** `POST /api/wallet/address`

**TAREAS:**
- [ ] 20.3.1 Al conectar wallet, se sincroniza con servidor
- [ ] 20.3.2 Wallet se guarda en base de datos
- [ ] 20.3.3 Al reconectar, se verifica que sea la misma wallet
- [ ] 20.3.4 Si es wallet diferente, manejar conflicto

---

#### FASE 20.4: Verificar Desconexión de Wallet ⏳

**TAREAS:**
- [ ] 20.4.1 Botón "Desconectar" funciona
- [ ] 20.4.2 Se limpia estado local
- [ ] 20.4.3 UI se actualiza (mostrar "Conectar Wallet")
- [ ] 20.4.4 Se notifica al servidor

---

#### FASE 20.5: Verificar UI de Wallet ⏳

**TAREAS:**
- [ ] 20.5.1 Balance B3C se muestra correctamente
- [ ] 20.5.2 Dirección de wallet truncada visible
- [ ] 20.5.3 Botón copiar dirección funciona
- [ ] 20.5.4 Historial de transacciones carga
- [ ] 20.5.5 Botones: Depositar, Retirar, Transferir funcionan

---

#### FASE 20.6: Verificar Dispositivos Confiables ⏳

**TAREAS:**
- [ ] 20.6.1 Sistema de dispositivos confiables
- [ ] 20.6.2 Agregar dispositivo actual como confiable
- [ ] 20.6.3 Verificar dispositivo antes de transacciones
- [ ] 20.6.4 UI de gestión de dispositivos

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 20:
- [ ] TON Connect se inicializa sin errores
- [ ] Conexión de wallet funciona con todas las opciones
- [ ] Wallet se sincroniza con servidor
- [ ] Desconexión funciona correctamente
- [ ] UI muestra estado correcto de wallet
- [ ] Dispositivos confiables funcionan

---

## SECCIONES ARCHIVADAS (COMPLETADAS)

Las siguientes secciones han sido completadas y archivadas:

- ✅ **Sección 1** - Publicaciones (100%)
- ✅ **Sección 2** - Navegación/UI (100%)
- ✅ **Sección 3** - Wallet/BUNK3RCOIN (100%)
- ✅ **Sección 4** - Base de datos (100%)
- ✅ **Sección 5** - Perfiles de usuario (100%)
- ✅ **Sección 6** - Comentarios (100%)
- ✅ **Sección 7** - Notificaciones (100%)
- ✅ **Sección 9** - Marketplace y Bots (100%)
- ✅ **Sección 10** - Números virtuales (100%)
- ✅ **Sección 11** - Responsive/Móvil (100%)
- ✅ **Sección 12** - Memory leaks (100%)
- ✅ **Sección 13** - Race conditions (100%)
- ✅ **Sección 14** - Código duplicado (100%)
- ✅ **Sección 15** - Token BUNK3RCO1N Real en Blockchain (100%)
- ✅ **Sección 16** - Pagos Directos y Wallets Reales (100%)

---

## HISTORIAL DE PROMPTS

| # | Fecha | Prompt del Usuario | Acción Tomada | Estado |
|---|-------|-------------------|---------------|--------|
| 1 | 05/12/2025 | Configuración inicial | Creado archivo PROMPT_PENDIENTES | ✅ |
| 2 | 05/12/2025 | Token BUNK3RCO1N real | SECCIÓN 15 - Token MAINNET | ✅ |
| 3 | 05/12/2025 | Botones de pago directo | SECCIÓN 16 - TON Connect | ✅ |
| 4 | 05/12/2025 | Error TON_CONNECT_SDK_ERROR | SECCIÓN 17 - Auditoría pagos | ⏳ |
| 5 | 05/12/2025 | Números virtuales sin servicio + botón atrás | SECCIÓN 18 - Auditoría VN | ⏳ |
| 6 | 05/12/2025 | Transferencias entre usuarios | SECCIÓN 19 - Transferencias P2P | ⏳ |
| 7 | 05/12/2025 | Conexión wallet completa | SECCIÓN 20 - Wallet Connect | ⏳ |

---

## INSTRUCCIONES DE CONTINUACIÓN AUTOMÁTICA

Cuando el usuario diga "continúa", el agente DEBE:
1. Leer este archivo completo
2. Identificar la siguiente sección pendiente (⏳)
3. Informar: "Comenzando sección [X]: [Nombre]"
4. Ejecutar TODAS las tareas de esa sección
5. Probar como usuario real
6. Verificar logs y consola
7. Actualizar este archivo (marcar ✅)
8. Actualizar replit.md
9. Informar: "Completada sección [X]. ¿Continúo con la siguiente?"

---

## ORDEN DE EJECUCIÓN RECOMENDADO

1. **SECCIÓN 17** - Corregir error de payload TON Connect (CRÍTICO)
2. **SECCIÓN 20** - Verificar conexión de wallet (BASE)
3. **SECCIÓN 18** - Arreglar números virtuales 
4. **SECCIÓN 19** - Implementar transferencias P2P

---

## RESUMEN FINAL

### SECCIONES ACTIVAS:
- ⏳ **Sección 17** - Auditoría de Pagos B3C (0%) - CRÍTICO
- ⏳ **Sección 18** - Auditoría Números Virtuales (0%)
- ⏳ **Sección 19** - Transferencias entre Usuarios (0%)
- ⏳ **Sección 20** - Conexión de Wallet (0%)

### PROGRESO: 15/20 secciones (75%)

**Próximo paso:** Ejecutar SECCIÓN 17 para corregir el error de payload TON Connect.
