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
| Sección actual | SECCIÓN 17 |
| Total secciones | 17 |
| Completadas | 14 ✅ |
| Pendientes | 1 ⏳ |
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

### 5. Normas de Análisis
- Revisar estructura de carpetas
- Detectar archivos o código muerto
- Proponer mejoras de arquitectura
- Evaluar rendimiento
- Identificar redundancias

### 6. Normas de Interacción
- Pedir confirmación para cambios críticos
- Explicar claramente cada modificación
- No omitir detalles técnicos
- Proponer alternativas cuando existan

### 7. Normas de Seguridad
**NO HACER:**
- Eliminar archivos sin confirmación
- Cambios destructivos sin aprobación
- Exponer datos sensibles

**OBLIGATORIO:**
- Respaldo antes de cambios mayores
- Validar entradas del usuario
- Mantener integridad del proyecto

### 8. Actualización Continua
- Leer siempre replit.md antes de empezar
- Mantener sincronizados: código, documentación, progreso
- Corregir inconsistencias
- Registrar cada avance

### 9. Detección de Vulnerabilidades
Revisar cada cambio para detectar:
- Inyección SQL/XSS/CSRF
- Exposición de datos
- Accesos sin autorización
- Código inseguro o deprecated
- Dependencias vulnerables

### 10. Protocolo de Vulnerabilidad Detectada
Si se detecta vulnerabilidad → **DETENER TODO**

1. Explicar en chat:
   - Qué es la vulnerabilidad
   - Qué daño podría causar
   - Cómo se previene

2. Corregir inmediatamente

3. Registrar en replit.md:
```
### Seguridad / Auditoría
- Vulnerabilidad: [...]
- Riesgos: [...]
- Corrección: [...]
- Fecha: [...]
```

4. Reanalizar funciones relacionadas

---

## SECCIONES DE TRABAJO

### Leyenda de Estados:
| Símbolo | Significado |
|---------|-------------|
| ✅ | Completado |
| 🔄 | En progreso |
| ⏳ | Pendiente |
| ❌ | Bloqueado/Error |

---

### SECCIÓN 17: AUDITORÍA COMPLETA DE PAGOS Y RETIROS B3C ⏳
**Prioridad:** CRÍTICA  
**Agregado:** 5 Diciembre 2025  
**Origen:** Error TON_CONNECT_SDK_ERROR detectado por usuario
**Estado:** PENDIENTE

---

#### ERROR DETECTADO:
```
Error: [TON_CONNECT_SDK_ERROR] z
SendTransactionRequest validation failed:
Invalid 'payload' in message at index 0
```

**Ubicación:** Función `buildTextCommentPayload()` en `static/js/app.js`
**Causa raíz:** El payload se construye de forma incorrecta para TON Connect SDK

---

#### PROMPT MAESTRO - INVESTIGACIÓN PROFUNDA

**OBJETIVO:** Investigar a fondo, probar todos los botones y funciones del sistema de pagos/retiros B3C. Verificar que la imagen del error esté resuelta. Encontrar y corregir todos los puntos de quiebre. Que los pagos y retiros funcionen de forma REAL en blockchain TON.

---

##### FASE 17.1: Diagnóstico del Error de Payload ⏳

**Análisis requerido:**
- [ ] 17.1.1 Revisar función `buildTextCommentPayload()` líneas 4318-4338
  - El payload actual usa formato incorrecto
  - TON Connect espera Cell serializado en Base64 (BOC)
  - El código actual crea un array con prefijo de 4 bytes zeros + texto
  
- [ ] 17.1.2 Investigar formato correcto de payload TON Connect
  - Usar web_search para documentación oficial
  - El comment en TON debe ser una Cell con opcode 0 + texto
  - Verificar si necesitamos librería @ton/ton o @ton/core
  
- [ ] 17.1.3 Corregir `buildTextCommentPayload()`
  - Opción A: Usar stateInit/body vacío y solo enviar TON sin comment
  - Opción B: Construir Cell correctamente con librería @ton/ton
  - Opción C: Usar formato raw sin Cell (solo para mensajes simples)

**Código actual problemático:**
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
        return btoa(binary); // Base64 pero no es BOC válido
    } catch (e) {
        console.error('Error building comment payload:', e);
        return undefined;
    }
}
```

**Solución propuesta:**
```javascript
buildTextCommentPayload(comment) {
    if (!comment) return undefined;
    try {
        // TON comment format: 0x00000000 (4 bytes) + UTF-8 text
        const encoder = new TextEncoder();
        const commentBytes = encoder.encode(comment);
        const payload = new Uint8Array(4 + commentBytes.length);
        // Opcode 0 para comentarios de texto (little-endian)
        new DataView(payload.buffer).setUint32(0, 0, true);
        payload.set(commentBytes, 4);
        // Convertir a base64 de forma segura
        return btoa(String.fromCharCode.apply(null, payload));
    } catch (e) {
        console.error('Error building comment payload:', e);
        return undefined;
    }
}
```

---

##### FASE 17.2: Verificar Flujo Completo de Compra B3C ⏳

**Botones a probar:**
- [ ] 17.2.1 Botón "0.5 TON" (Prueba)
- [ ] 17.2.2 Botón "1 TON"
- [ ] 17.2.3 Botón "5 TON" (Popular)
- [ ] 17.2.4 Botón "10 TON"
- [ ] 17.2.5 Botón "20 TON"
- [ ] 17.2.6 Input personalizado con monto custom

**Para cada botón verificar:**
1. ¿Se abre el modal de TON Connect?
2. ¿Aparece la transacción pre-configurada en la wallet?
3. ¿El monto es correcto?
4. ¿La wallet destino es correcta (hotWallet)?
5. ¿El comentario/memo se incluye?
6. ¿La transacción se envía sin errores?
7. ¿Se verifica automáticamente después del pago?
8. ¿Se acreditan los B3C al balance?

**Puntos de quiebre identificados:**
- [ ] `buildTextCommentPayload()` - Payload inválido
- [ ] `tonConnectUI.sendTransaction()` - Puede fallar si wallet no conectada
- [ ] `/api/b3c/buy/create` - Si no retorna hotWallet
- [ ] `/api/b3c/buy/{id}/verify` - Timeout o verificación fallida
- [ ] Conexión de wallet - Si usuario cancela

---

##### FASE 17.3: Verificar Flujo de Retiros B3C ⏳

**Endpoints a verificar:**
- [ ] 17.3.1 `POST /api/b3c/withdraw` - Crear solicitud de retiro
  - Validar que se descuente del balance interno
  - Validar que se cree registro en base de datos
  - Validar que se notifique al admin

- [ ] 17.3.2 `GET /api/b3c/withdraw/{id}/status` - Consultar estado
  - Estados: pending, processing, completed, rejected
  - Mostrar hash de transacción cuando completado

- [ ] 17.3.3 `GET /api/admin/b3c/withdrawals` - Admin ve pendientes
  - Listar todos los retiros por estado
  - Mostrar información de usuario y monto

- [ ] 17.3.4 `POST /api/admin/b3c/withdrawals/{id}/process` - Admin procesa
  - Acción: complete o reject
  - Incluir txHash para completados
  - Actualizar estado en base de datos

**Frontend a verificar:**
- [ ] UI de solicitud de retiro en wallet
- [ ] Input para wallet destino
- [ ] Validación de dirección TON
- [ ] Confirmación antes de enviar
- [ ] Feedback visual de estado

---

##### FASE 17.4: Verificar Depositos de B3C ⏳

- [ ] 17.4.1 Función de depósito (usuario envía B3C a la app)
  - ¿Existe endpoint?
  - ¿Cómo se detectan depósitos entrantes?
  - ¿Se actualiza balance automáticamente?

---

##### FASE 17.5: Verificar Transferencias B3C entre Usuarios ⏳

- [ ] 17.5.1 Funcionalidad "Transferir" en UI
  - ¿Endpoint existe?
  - ¿Se valida destinatario?
  - ¿Se actualiza balance de ambos?

---

##### FASE 17.6: Revisar buildJettonTransferPayload() ⏳

**Código actual problemático:**
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

**Problema:** Este formato JSON NO es válido para transferencias Jetton.
Las transferencias Jetton requieren una Cell serializada con estructura específica.

**Solución:** Usar librería @ton/ton o construir Cell manualmente:
- [ ] 17.6.1 Investigar formato correcto de Jetton Transfer
- [ ] 17.6.2 Implementar construcción de Cell correcta
- [ ] 17.6.3 Probar con transacción real

---

##### FASE 17.7: Logs y Monitoreo ⏳

- [ ] 17.7.1 Agregar logs detallados en cada paso de transacción
- [ ] 17.7.2 Capturar y mostrar errores específicos al usuario
- [ ] 17.7.3 Implementar retry automático para verificaciones
- [ ] 17.7.4 Agregar timeouts apropiados

---

##### FASE 17.8: Testing End-to-End ⏳

- [ ] 17.8.1 Probar compra B3C con wallet Telegram real
- [ ] 17.8.2 Verificar que B3C se acreditan
- [ ] 17.8.3 Probar retiro de B3C
- [ ] 17.8.4 Verificar que admin puede procesar
- [ ] 17.8.5 Verificar que tokens llegan a wallet del usuario

---

#### CRITERIOS DE ACEPTACIÓN SECCIÓN 17

Para marcar como COMPLETADA, se debe verificar:

- [ ] Error TON_CONNECT_SDK_ERROR resuelto
- [ ] Compras B3C funcionan sin errores
- [ ] Todos los botones de compra funcionan
- [ ] Retiros se procesan correctamente
- [ ] Balance se actualiza en tiempo real
- [ ] No hay errores en consola del navegador
- [ ] No hay errores en logs del servidor
- [ ] Transacciones aparecen en historial
- [ ] Usuario ve confirmación visual clara

---

### SECCIONES ARCHIVADAS (COMPLETADAS)

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
| 1 | 05/12/2025 | Configuración inicial del sistema de pendientes | Creado archivo PROMPT_PENDIENTES con estructura completa | ✅ |
| 2 | 05/12/2025 | Crear token BUNK3RCO1N real en blockchain | Creada SECCIÓN 15 - Token creado en MAINNET | ✅ |
| 3 | 05/12/2025 | Botones de pago directo y wallets reales | Creada SECCIÓN 16 - TON Connect pagos directos + Admin retiros | ✅ |
| 4 | 05/12/2025 | Investigar error TON_CONNECT_SDK_ERROR y auditar todo el sistema de pagos | Creada SECCIÓN 17 - Auditoría completa de pagos y retiros | ⏳ |

---

## INSTRUCCIONES DE CONTINUACIÓN AUTOMÁTICA

Cuando el usuario diga "continúa", el agente DEBE:
1. Leer este archivo completo
2. Identificar la siguiente sección pendiente (⏳)
3. Informar: "Comenzando sección [X]: [Nombre]"
4. Ejecutar todas las tareas de esa sección
5. Verificar funcionamiento
6. Actualizar este archivo (marcar ✅, agregar notas)
7. Actualizar replit.md
8. Informar: "Completada sección [X]. ¿Continúo con la siguiente?"

---

## ➕ INSTRUCCIONES PARA NUEVO PROMPT

Cuando el usuario agregue una nueva tarea:
1. Analizar el prompt del usuario
2. Determinar si es nueva sección o tarea dentro de sección existente
3. Agregar al archivo en el lugar correcto
4. Registrar en historial de prompts
5. Preguntar: "¿Ejecuto ahora o continúo con las secciones pendientes?"

---

## INSTRUCCIONES PARA VER PROGRESO

Cuando el usuario pida ver progreso, mostrar:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROGRESO DEL PROYECTO: BUNK3R-W3B
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Completadas: 15/17 secciones (88%)
⏳ Pendiente: Sección 17 - Auditoría de Pagos
Última actividad: 5 Dic 2025 - Error TON_CONNECT detectado
¿Qué quieres hacer?
1️⃣ Continuar trabajo
2️⃣ Ver detalle de sección específica
3️⃣ Agregar nueva tarea
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## NOTAS IMPORTANTES

- Este archivo es la **fuente de verdad** del proyecto
- El agente **SIEMPRE** debe leerlo al iniciar
- Cualquier cambio importante debe quedar registrado aquí
- El usuario puede modificar prioridades en cualquier momento
- Las reglas base son **OBLIGATORIAS** y **PERMANENTES**

---

## RESUMEN FINAL

### SECCIÓN ACTIVA:
- ⏳ **Sección 17** - Auditoría Completa de Pagos y Retiros B3C (0%)

### PROGRESO: 15/17 secciones (88%)

**Próximo paso:** Ejecutar SECCIÓN 17 para corregir el error de payload y verificar todo el sistema de pagos.
