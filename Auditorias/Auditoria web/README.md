# Auditoria Web - Script de Seguridad

## Descripcion
Script completo de auditoria de seguridad web con 58 pruebas en 14 bloques.

## Como Ejecutar

```bash
# Desde la raiz del proyecto
python "Auditorias/Auditoria web/web_security_audit.py"

# O especificar URL objetivo
AUDIT_TARGET_URL=http://localhost:5000 python "Auditorias/Auditoria web/web_security_audit.py"
```

## Bloques de Auditoria

| # | Bloque | Pruebas |
|---|--------|---------|
| 1 | Configuracion y Headers | 3 |
| 2 | Inyecciones (SQL, XSS, Command, etc) | 7 |
| 3 | Autenticacion | 5 |
| 4 | Rate Limiting y DoS | 3 |
| 5 | Exposicion de Informacion | 4 |
| 6 | APIs y Logica | 5 |
| 7 | Analisis de Codigo | 5 |
| 8 | CORS y Origenes | 3 |
| 9 | Sesiones y Tokens | 4 |
| 10 | Uploads y Archivos | 3 |
| 11 | SSL/TLS | 3 |
| 12 | Metodos HTTP | 3 |
| 13 | Websockets | 2 |
| 14 | Base de Datos | 8 |

## Reportes Generados

Despues de ejecutar, encontraras:

- `reporte_auditoria.txt` - Reporte legible con todos los hallazgos
- `reporte_auditoria.json` - Formato JSON para analisis programatico

## Severidades

- CRITICO - Accion inmediata requerida
- ALTO - Corregir lo antes posible
- MEDIO - Planificar correccion
- BAJO - Mejora recomendada
- INFO - Informativo
