# 4. Role Matrix (RBAC)

## Roles Definidos

- **Inversor Retail** (`inversor_retail`, MFA: Opcional): Propietario del patrimonio: administra portafolios, registra compras/ventas, crea metas granulares y emite API Keys para su app Finanzas.
- **API Externa "Finanzas"** (`integracion_finanzas`, MFA: Opcional): Credencial de solo lectura (X-API-Key: aurum_ro_*) usada por la app paralela de Finanzas Personales para consultar el resumen patrimonial agregado.
- **Asesor Financiero (RIA)** (`asesor_financiero`, MFA: Sí): Profesional autorizado por mandato para visualizar portafolios y metas de clientes asignados sin capacidad de alterar transacciones.
- **Auditor / Compliance** (`auditor_compliance`, MFA: Sí): Perfil de control con acceso de solo lectura a bitácoras de auditoría, reportes fiscales, transacciones y metas.
- **Administrador Plataforma** (`admin_plataforma`, MFA: Sí): Operaciones con control sobre catálogo maestro de activos, fuentes FX, configuración de sistema y soporte de lectura sobre datos de usuarios.

## Matriz de Permisos

| Permiso | Acción | Inversor Retail | API Externa | Asesor | Auditor | Admin |
|---|---|---|---|---|---|---|
| `portfolio:create` | Crear portafolio / plataforma propia | OWN | DENY | OWN | DENY | FULL |
| `portfolio:read` | Ver holdings y valoración detallada | OWN | DENY | ASSIGNED | READ_ALL | FULL |
| `transaction:write` | Registrar compra o venta (parcial/total) | OWN | DENY | DENY | DENY | DENY |
| `transaction:read` | Consultar libro mayor de operaciones | OWN | DENY | ASSIGNED | READ_ALL | READ_ALL |
| `transaction:delete` | Anular operación y recalcular ciclos WAC/FIFO | OWN | DENY | DENY | DENY | DENY |
| `goal:write` | Crear o editar metas (Globales o Activo+Plataforma) | OWN | DENY | DENY | DENY | DENY |
| `goal:read` | Leer progreso de metas patrimoniales | OWN | DENY | ASSIGNED | READ_ALL | READ_ALL |
| `analytics:read` | Consultar TWR, XIRR y atribución Precio vs FX | OWN | DENY | ASSIGNED | READ_ALL | READ_ALL |
| `external:summary:read` | Consultar resumen agregado (/external/finanzas/summary) | OWN | ALLOW | DENY | DENY | DENY |
| `apikey:manage` | Emitir y revocar API Keys de solo lectura | OWN | DENY | DENY | DENY | FULL |
| `market:read` | Consultar precios y tasas FX | READ_ALL | DENY | READ_ALL | READ_ALL | FULL |
| `audit:read` | Inspeccionar bitácora de auditoría (Audit Logs) | OWN | DENY | DENY | READ_ALL | READ_ALL |

## Leyenda de valores

| Valor | Significado |
|---|---|
| **OWN** | Solo sobre recursos del propio usuario |
| **ASSIGNED** | Solo sobre clientes con mandato activo (`advisor_client_links`) |
| **READ_ALL** | Lectura de cualquier recurso (sin escritura) |
| **FULL** | Lectura + escritura / administración |
| **ALLOW** | Permitido (rol de API Key con scope único) |
| **DENY** | Prohibido |

## Principios de diseño aplicados

1. **Least Privilege**: Ningún rol de soporte (Asesor, Auditor, Admin) puede crear, modificar ni anular transacciones o metas. Solo el Inversor propietario tiene capacidad de escritura contable.
2. **Separación de deberes**: El Administrador puede emitir/revocar API Keys y gestionar catálogos, pero no puede inventar movimientos en el ledger de un usuario.
3. **API Externa aislada**: El rol `integracion_finanzas` solo tiene `external:summary:read`. Cualquier intento de POST/PATCH/DELETE con esa API Key responde 403.
4. **Soporte y compliance**: Admin y Auditor tienen lectura amplia (`READ_ALL`) para poder diagnosticar y auditar sin poder alterar el libro mayor.
