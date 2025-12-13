# Auditoria Web Console - Script de Seguridad Masivo

## Descripcion
Script de auditoria enfocado en vulnerabilidades detectables desde la consola del navegador (DevTools).
Contiene 100+ pruebas en 20 bloques.

## Como Ejecutar

```bash
python "Auditorias/Auditoria-Web-Console/console_security_audit.py"

# Con URL personalizada
AUDIT_TARGET_URL=http://localhost:5000 python "Auditorias/Auditoria-Web-Console/console_security_audit.py"
```

## Bloques de Auditoria

| # | Bloque | Descripcion |
|---|--------|-------------|
| 1 | Errores de JavaScript | Stack traces, excepciones expuestas |
| 2 | Variables Globales | Datos sensibles en window.* |
| 3 | LocalStorage/SessionStorage | Tokens y credenciales en storage |
| 4 | Cookies | Flags de seguridad faltantes |
| 5 | Network Requests | Endpoints y credenciales en red |
| 6 | Headers de Respuesta | Headers de seguridad faltantes |
| 7 | Codigo JavaScript | API keys y secretos en JS |
| 8 | Source Maps | Codigo fuente expuesto |
| 9 | HTML/DOM | Comentarios y datos sensibles |
| 10 | WebSockets | Conexiones inseguras |
| 11 | Service Workers | Cache de datos sensibles |
| 12 | APIs del Navegador | Permisos y accesos |
| 13 | PostMessage | Comunicacion entre ventanas |
| 14 | Fetch/XHR | Interceptacion de requests |
| 15 | Third Party Scripts | CDN sin SRI, trackers |
| 16 | Prototype Pollution | Vulnerabilidades de JS |
| 17 | DOM Clobbering | IDs peligrosos |
| 18 | Event Handlers | Handlers inline inseguros |
| 19 | Fuzzing Endpoints | Rutas ocultas en JS |
| 20 | Fingerprinting | Leaks de informacion |

## Reportes Generados

- `reporte_console_audit.txt` - Reporte legible
- `reporte_console_audit.json` - Formato JSON

## Severidades

- CRITICO - Accion inmediata
- ALTO - Corregir pronto
- MEDIO - Planificar
- BAJO - Mejora recomendada
- INFO - Informativo
