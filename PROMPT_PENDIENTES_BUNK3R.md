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
| Sección actual | - |
| Total secciones | 0 |
| Completadas | 0 ✅ |
| Pendientes | 0 ⏳ |
| En progreso | 0 🔄 |
| Crítico | 0 🟢 |

---

## RESUMEN EJECUTIVO

Todas las secciones anteriores han sido completadas y archivadas.

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

### 5. ⚠️ ACTUALIZACIÓN INMEDIATA OBLIGATORIA ⚠️
**Al completar CUALQUIER sección, el agente DEBE actualizar ESTE archivo de inmediato:**

```
UBICACIÓN: PROMPT_PENDIENTES_BUNK3R.md

PASOS OBLIGATORIOS:
1. Cambiar estado de ⏳ a ✅ en la sección completada
2. Actualizar el encabezado de la sección (agregar ✅)
3. Cambiar "Estado: PENDIENTE" a "Estado: COMPLETADO"
4. Agregar fecha de completado
5. Actualizar RESUMEN EJECUTIVO con lo que se hizo
6. Actualizar contadores en ESTADO GENERAL DEL PROYECTO
7. Marcar tareas individuales como [x] completadas
```

### 6. Normas de Seguridad
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

*No hay secciones pendientes actualmente. Usa el menú de inicio para agregar nuevas tareas.*

---
