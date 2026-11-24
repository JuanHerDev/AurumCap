# 2. Software Architecture Document (SAD)

## Capas y Componentes (FastAPI + React)

### AurumCap React 19 SPA (Cliente)
- **Stack:** Vite · TanStack Query · Zustand · Tailwind CSS
- **Protocolos:** HTTPS / JSON REST + JWT Bearer
- **Responsabilidad:** Interfaz web para gestión de portafolios, registro de compras/ventas parciales y totales, tablero de metas granulares y gestión de API Keys.

### App Externa "Finanzas" (Solo Lectura) (Cliente)
- **Stack:** Cliente HTTP Externo · X-API-Key Header
- **Protocolos:** HTTPS REST + X-API-Key (aurum_ro_*)
- **Responsabilidad:** Proyecto paralelo de finanzas personales que consulta periódicamente el resumen agregado patrimonial y metas para mostrar contexto completo.

### FastAPI Application Server (API Gateway & BFF)
- **Stack:** Python 3.12 · FastAPI · Pydantic v2 · Uvicorn
- **Protocolos:** ASGI Async · SQLAlchemy 2.0 Async
- **Responsabilidad:** Enrutamiento /api/v1, validación Pydantic, autenticación dual (JWT usuario + API Key externa scope external:summary:read) y rate limiting.

### Cost-Basis, Lots & Goals Engine (Dominio & Servicios)
- **Stack:** Python Decimal · State Machine de Ciclos · XIRR
- **Protocolos:** Llamadas de dominio in-process
- **Responsabilidad:** Procesa compras, ventas parciales/totales sin residuos, recompras por ciclo, evaluación de metas aisladas (Global vs Activo+Plataforma), TWR y XIRR.

### Market Data & LATAM FX Adapter (Dominio & Servicios)
- **Stack:** HTTPX Async · Circuit Breaker · Polygon/CoinGecko/Banxico/BCRA
- **Protocolos:** HTTPS External APIs -> Redis Cache
- **Responsabilidad:** Patrón Adapter para cotizaciones bursátiles, cripto 24/7 y tasas FX oficiales/financieras con fallback determinístico.

### Broker CSV Parser & Snapshot Worker (Dominio & Servicios)
- **Stack:** ARQ / Celery + Redis Queue
- **Protocolos:** Redis Broker · Async DB Batching
- **Responsabilidad:** Procesamiento asíncrono de extractos CSV, recálculo de cadena de ciclos tras inserciones retroactivas y snapshots diarios.

### PostgreSQL 16 (Ledger, Goals & Keys) (Datos & Asíncrono)
- **Stack:** PostgreSQL 16 · Alembic · NUMERIC(20,8)
- **Protocolos:** asyncpg TCP Pool
- **Responsabilidad:** Persistencia ACID de portafolios, transacciones con position_cycle_id, metas granulares, API keys hasheadas, precios, tasas FX y audit_logs.

### Redis 7 (Cache, Rate Limit & Cola) (Datos & Asíncrono)
- **Stack:** Redis 7 · TTL Cache · Idempotency
- **Protocolos:** RESP3 TCP
- **Responsabilidad:** Caché de precios (5-15m), caché del resumen /external/finanzas/summary (60s), rate limit y llaves de idempotencia.

## Architecture Decision Records (ADRs)

### ADR-01: Monolito Modular en FastAPI antes que Microservicios [Aceptada]
- **Contexto:** Para el MVP, fragmentar Auth, Ledger, Metas e Integración Externa en microservicios añade latencia y transacciones distribuidas innecesarias.
- **Decisión:** Construir un Monolito Modular en FastAPI separado por capas (domain/, api/v1/, infrastructure/) con worker asíncrono compartiendo el mismo código base.
- **Consecuencias:** Transacciones ACID nativas al validar ventas y actualizar snapshots/caché en una sola operación.

### ADR-02: Aritmética Decimal en Python + NUMERIC(20,8) en PostgreSQL [Aceptada]
- **Contexto:** En criptoactivos (8 decimales de BTC) y monedas LATAM de alta denominación (COP, ARS, CLP), float produce residuos como 0.00000001 tras una venta total.
- **Decisión:** Usar Decimal de Python en toda la lógica contable y NUMERIC(20,8) en PostgreSQL.
- **Consecuencias:** Cierres exactos a 0.00000000 en ventas totales y cero descuadres en conciliación.

### ADR-03: Aislamiento de Costo Base por (portfolio_id, asset_id) y Ciclos de Lote [Aceptada]
- **Contexto:** Mezclar el costo promedio de un mismo activo entre plataformas distintas (Binance vs IBKR) o arrastrar el WAC después de una venta total corrompe las métricas y confunde las metas.
- **Decisión:** Cada transacción pertenece a un (portfolio_id, asset_id) y se agrupa en un position_cycle_id incremental que se cierra al llegar la cantidad a 0 y se reinicia en la siguiente compra.
- **Consecuencias:** Soporta limpiamente ventas parciales, salidas totales, recompras y metas aisladas por plataforma.

### ADR-04: Metas Desacopladas por Scope (GLOBAL | PORTFOLIO | ASSET_IN_PORTFOLIO) [Aceptada]
- **Contexto:** El inversor necesita asignar un activo en una plataforma a una meta específica (ej. BTC en IBKR para un viaje) sin tocar el mismo activo en otra plataforma (BTC en Binance para DCA largo plazo).
- **Decisión:** Modelar investment_goals con scope_type polimórfico referenciando opcionalmente portfolio_id y asset_id en vez de mover títulos entre cuentas contables.
- **Consecuencias:** Cálculo en tiempo real sin duplicar transacciones ni afectar la contabilidad real del custodio.

### ADR-05: API Key Hasheada con Scope Único external:summary:read para App "Finanzas" [Aceptada]
- **Contexto:** Tu aplicación paralela de finanzas personales ("Finanzas") necesita consultar el contexto general de inversiones sin implementar flujos complejos OAuth2 ni exponer permisos de escritura.
- **Decisión:** Implementar tokens PAT personales (prefijo aurum_ro_) almacenados como SHA-256 en external_api_keys, habilitados únicamente en GET /api/v1/external/finanzas/summary con caché Redis de 60s.
- **Consecuencias:** Integración en menos de 20 líneas en la app Finanzas, latencia baja y superficie de ataque mínima.

### ADR-06: Gobernanza de Esquema con Alembic Async y Estrategia Expand-and-Contract [Aceptada]
- **Contexto:** Un libro mayor financiero en producción con restricciones CHECK estrictas y columnas temporales (valid_from/valid_to) no puede depender de sincronizaciones manuales ni destructivas.
- **Decisión:** Configurar Alembic en modo async con SQLAlchemy 2.0 (asyncpg), nombrado determinístico de constraints (naming_convention), validación CI con alembic check y migraciones en dos fases (Expand-and-Contract).
- **Consecuencias:** Despliegues sin downtime, rollback controlado mediante alembic downgrade -1 y trazabilidad exacta entre código Python y PostgreSQL 16.

## Estructura del Monorepo
```text
aurumcap/
├── backend/
│   ├── alembic.ini                    # Configuración central Alembic (script_location)
│   ├── app/
│   │   ├── main.py                    # Lifespan, CORS, OpenAPI, middlewares
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic Settings (DB, Redis, JWT, Providers)
│   │   │   ├── security.py            # Argon2id, JWT, API Key SHA-256 & RBAC guards
│   │   │   └── decimal_utils.py       # Helpers de precisión Decimal (8 decimales)
│   │   ├── api/v1/
│   │   │   ├── router.py              # Registro central /api/v1
│   │   │   ├── auth.py                # /auth/register, /login, /api-keys
│   │   │   ├── portfolios.py          # CRUD portafolios/plataformas
│   │   │   ├── transactions.py        # Compras, ventas parciales/totales, CSV
│   │   │   ├── goals.py               # Metas globales y por (activo + plataforma)
│   │   │   ├── external_finanzas.py   # GET /external/finanzas/summary (Read-Only)
│   │   │   ├── market_data.py         # Activos US/LATAM/Cripto y tasas FX
│   │   │   └── analytics.py           # TWR, XIRR y atribución FX
│   │   ├── domain/
│   │   │   └── services/
│   │   │       ├── lot_accounting.py  # Motor WAC/FIFO, ventas parciales/totales y ciclos
│   │   │       ├── goal_evaluator.py  # Cálculo aislado por scope de meta
│   │   │       ├── performance.py     # TWR y XIRR (Newton-Raphson)
│   │   │       └── fx_converter.py    # Conversión multi-moneda con fallback hábil
│   │   ├── infrastructure/
│   │   │   ├── db/
│   │   │   │   ├── base.py            # DeclarativeBase + naming_convention + TemporalMixin
│   │   │   │   ├── session.py         # AsyncEngine (asyncpg) & sessionmaker
│   │   │   │   ├── models/            # Modelos ORM 3FN (users, platforms, portfolios...)
│   │   │   │   └── migrations/
│   │   │   │       ├── env.py         # Runner asyncpg para alembic upgrade/check
│   │   │   │       ├── script.py.mako # Plantilla estandarizada upgrade/downgrade
│   │   │   │       └── versions/
│   │   │   │           ├── 0001_3fn_core_and_temporal.py
│   │   │   │           ├── 0002_lot_cycles_and_goals.py
│   │   │   │           └── 0003_external_api_keys_and_audit.py
│   │   │   ├── providers/             # Adapters Yahoo/Polygon/CoinGecko/Banxico/BCRA
│   │   │   └── workers/               # Jobs ARQ/Celery (EOD prices, snapshots)
│   │   └── schemas/                   # Contratos Pydantic v2
│   └── tests/                         # Pytest: lotes WAC, metas aisladas y migrations check
└── frontend/
    ├── src/
    │   ├── api/                       # Cliente tipado OpenAPI
    │   ├── features/                  # portfolios, ledger, goals, api-keys, analytics
    │   └── components/
```