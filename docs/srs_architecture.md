# 1. Software Requirements Specification (SRS)

## RF-01: Configuración de Jurisdicción Fiscal y Moneda Base (Funcional · Must)
El usuario debe poder seleccionar su país de residencia fiscal y moneda de reporte principal (USD o moneda local LATAM), alternando la moneda de visualización sin alterar los registros históricos.

**Criterios de aceptación:**
- Soporte inicial para USD, MXN, COP, BRL, CLP, ARS y PEN.
- El cambio de moneda de visualización recalcula totales en < 250ms.
- Cada portafolio conserva su moneda base contable inmutable tras registrar transacciones.

## RF-02: Aislamiento por Plataforma / Custodio (Multi-Portafolio) (Funcional · Must)
El sistema debe permitir crear portafolios independientes por plataforma o custodio (ej. IBKR, Binance, GBM+, Trii) con su propio inventario de posiciones y benchmark.

**Criterios de aceptación:**
- Un mismo activo (ej. BTC o VOO) puede existir simultáneamente en dos portafolios/plataformas sin fusionar su cantidad ni su costo promedio.
- No se permite eliminar físicamente un portafolio con transacciones asociadas (soft delete).

## RF-03: Registro de Operaciones (BUY, SELL Parcial/Total, DIVIDEND, FEE) (Funcional · Must)
El usuario debe poder registrar compras, ventas parciales o totales, dividendos, depósitos, retiros y comisiones indicando cantidad, precio unitario, divisa y tasa FX aplicada.

**Criterios de aceptación:**
- Validación estricta de quantity > 0 y bloqueo de ventas que excedan la cantidad disponible en ese portafolio específico.
- La tasa FX histórica se autocompleta según fecha pero admite sobrescritura manual de boleta.
- Cada operación genera una entrada auditable con timestamp UTC.

## RF-04: Manejo Determinístico de Ventas Parciales, Ventas Totales, WAC y Recompras (Funcional · Must)
El motor contable debe procesar ventas parciales, ventas totales y recompras posteriores mediante Costo Promedio Ponderado (WAC) y soporte opcional FIFO sin generar residuos decimales ni distorsionar ciclos históricos.

**Criterios de aceptación:**
- Venta Parcial (WAC): reduce qty_held = qty_before - qty_sold y ajusta total_cost_basis proporcionalmente (total_cost_basis * qty_after / qty_before), manteniendo inalterado el wac_unit_cost.
- Venta Total (Full Exit): al vender el 100% de qty_held, la posición cierra exactamente en 0.00000000, el costo base queda en 0, se consolida el P&L realizado definitivo y se cierra el position_cycle_id.
- Recompra tras cierre total: una nueva compra inicia un nuevo position_cycle_id con costo base desde cero, sin contaminarse por operaciones ya cerradas.
- Si el usuario anula o inserta una transacción retroactiva en orden cronológico pasado, el motor recalcula la cadena de ciclos de ese (portfolio_id, asset_id) de principio a fin.

## RF-05: Metas Generales y Específicas por (Activo + Plataforma) (Funcional · Must)
El usuario debe poder crear metas financieras vinculadas a todo su patrimonio consolidado (GLOBAL), a un portafolio completo (PORTFOLIO), o exclusivamente a un activo dentro de una plataforma específica (ASSET_IN_PORTFOLIO).

**Criterios de aceptación:**
- Una meta con scope ASSET_IN_PORTFOLIO apunta exactamente al par (portfolio_id, asset_id), ej. solo BTC en IBKR.
- Los movimientos o compras DCA de BTC en Binance no alteran ni aportan al progreso de la meta vinculada a BTC en IBKR.
- El progreso se calcula como current_value_in_target_currency / target_amount sin transferir ni bloquear fondos reales.

## RF-06: API Read-Only de Contexto Patrimonial para App "Finanzas" (Funcional · Must)
AurumCap debe exponer un endpoint resumido autenticado por API Key de solo lectura (scope external:summary:read) para que la aplicación paralela de Finanzas Personales obtenga una vista general actualizada del portafolio.

**Criterios de aceptación:**
- El usuario puede emitir y revocar API Keys de solo lectura desde su perfil (almacenadas como hash SHA-256).
- La respuesta devuelve patrimonio total consolidado, costo invertido, P&L no realizado, TWR YTD, desglose resumido por plataforma y avance de metas.
- Cualquier petición con API Key hacia endpoints de escritura (POST/PATCH/DELETE) o detalle de transacciones individuales responde 403 Forbidden.

## RF-07: Múltiples Fuentes Cambiarias (Oficial vs Financiero MEP/CCL) (Funcional · Must)
El sistema debe almacenar series diarias de tipo de cambio diferenciando fuente oficial (TRM, FIX, PTAX, BCRA) y cotizaciones financieras implícitas (MEP, CCL).

**Criterios de aceptación:**
- El usuario puede elegir fuente FX preferida por portafolio y aplicar fallback determinístico al último día hábil previo en feriados.

## RF-08: Métricas TWR, MWR (XIRR) y Atribución Precio vs FX (Funcional · Must)
El backend debe calcular Time-Weighted Return (TWR) y Money-Weighted Return (XIRR), separando retorno del activo del efecto de variación cambiaria.

**Criterios de aceptación:**
- Ventanas temporales estándar: 1M, 3M, YTD, 1Y, 3Y, MAX.
- Cálculo incremental mediante snapshots diarios materializados.

## RF-09: Carga Masiva CSV con Detección de Duplicados (Funcional · Should)
Carga de extractos CSV (IBKR, Binance, GBM+, Trii) con previsualización y huella SHA-256 anti-duplicados.

**Criterios de aceptación:**
- Cada fila genera un fingerprint SHA-256 para evitar duplicados al re-subir extractos.
- Procesamiento de hasta 5,000 filas en < 5 segundos.

## RNF-01: Aritmética Decimal Exacta (Sin Punto Flotante Binario) (No Funcional · Must)
Toda cifra monetaria, cantidad fraccionaria (ej. satoshis/BTC o ETFs fraccionados) y tipo de cambio debe procesarse con Decimal en Python y NUMERIC(20,8) en PostgreSQL.

**Criterios de aceptación:**
- Prohibido el uso de float en cálculos de saldos, WAC, ventas parciales/totales o conversiones FX.
- Al vender el 100% de una posición, la validación exacta garantiza saldo 0.00000000 sin errores de redondeo residual.

## RNF-02: Tiempos de Respuesta API P95 y Caché para App Finanzas (No Funcional · Must)
Los endpoints de analítica y el endpoint de contexto externo /external/finanzas/summary deben responder en <= 300ms (P95) apoyados en caché Redis.

**Criterios de aceptación:**
- Respuesta de /external/finanzas/summary cacheada por usuario en Redis (TTL 60s) e invalidada automáticamente al asentar nuevas transacciones.
- Precios de mercado cacheados en Redis con TTL de 5-15 minutos.

## RNF-03: JWT + Argon2id + Aislamiento de Scopes para API Externa (No Funcional · Must)
Tráfico TLS 1.3, contraseñas con Argon2id, tokens JWT cortos (15 min) y API Keys externas prefijadas (aurum_ro_) almacenadas únicamente como hash SHA-256.

**Criterios de aceptación:**
- Protección contra IDOR en todos los recursos.
- Rate limiting dedicado para API Key externa (60 req/min por llave).

## RNF-04: Idempotencia y Trazabilidad Inmutable (No Funcional · Should)
Las mutaciones financieras críticas aceptan Idempotency-Key y registran evento en audit_logs con actor, IP, payload antes/después y timestamp.

**Criterios de aceptación:**
- Reintentos de red en POST /transactions con la misma Idempotency-Key devuelven la respuesta original sin duplicar la venta o compra.

## RNF-05: Migraciones Versionadas y Reversibles con Alembic Async (No Funcional · Must)
Todo cambio de esquema en PostgreSQL 16 (tablas, columnas temporales, restricciones CHECK e índices) debe gestionarse mediante revisiones Alembic determinísticas y reversibles.

**Criterios de aceptación:**
- Prohibido usar Base.metadata.create_all() en producción; el despliegue ejecuta alembic upgrade head antes de iniciar Uvicorn.
- El pipeline CI ejecuta alembic check para bloquear modelos SQLAlchemy desincronizados respecto a migrations/versions/.
- Cada revisión implementa downgrade() explícito siguiendo estrategia Expand-and-Contract sin pérdida de datos históricos.

## Glosario Financiero LATAM

- **Position Cycle (Ciclo de Lote)** (Global (AurumCap Core)): Periodo contable desde la primera compra de un activo en una plataforma hasta su venta total (saldo 0). Al cerrar el ciclo, una recompra futura inicia un ciclo nuevo sin arrastrar el WAC anterior.
- **WAC (Costo Promedio Ponderado)** (MX, CO, CL, PE, Cripto): Método contable donde cada compra actualiza el costo promedio unitario; las ventas parciales reducen el costo total proporcionalmente conservando el mismo costo unitario.
- **CEDEAR / BDR / SIC** (AR, BR, MX): Certificados que cotizan en bolsas locales (BYMA, B3, BMV) representando acciones o ETFs extranjeros con un ratio de conversión específico.
- **Dólar MEP / CCL** (AR): Tipos de cambio financieros implícitos obtenidos mediante compra-venta de bonos o acciones en pesos y dólares.
- **TWR vs MWR (XIRR)** (Global): TWR mide el desempeño puro de la estrategia aislando depósitos/retiros; MWR mide la rentabilidad efectiva ponderada por el tamaño y momento de cada aporte.