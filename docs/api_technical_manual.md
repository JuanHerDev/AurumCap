# 3. API Technical Manual (FastAPI /api/v1)

## POST /api/v1/auth/register
Registrar usuario inversor o asesor con país fiscal y moneda base — Permiso: `public`

```python
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    country_code: Literal["MX", "CO", "BR", "CL", "AR", "PE"]
    preferred_display_currency: Literal["USD", "MXN", "COP", "BRL", "CLP", "ARS", "PEN"]
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "rt_9f82a1b4c3d0...",
  "token_type": "bearer",
  "expires_in": 900
}
```

## POST /api/v1/auth/login
Autenticar usuario con email y contraseña; emite par access + refresh token — Permiso: `public`

```python
class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "rt_9f82a1b4c3d0...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "usr_01J9ZAA12B",
    "email": "inversor@ejemplo.com",
    "full_name": "Ana García",
    "role": "inversor_retail",
    "country_code": "MX",
    "display_currency": "MXN"
  }
}
```

**Notas de seguridad:**
- Contraseña verificada con Argon2id (nunca en texto plano).
- Access token JWT de vida corta (15 min / 900 s).
- Refresh token opaco, rotativo y almacenado hasheado (SHA-256) en servidor.
- Rate limit dedicado: 10 intentos / 15 min por IP + email (mitigación brute-force).

## POST /api/v1/auth/refresh
Renovar access token usando un refresh token válido; rota el refresh token — Permiso: `public` (requiere refresh token)

```python
class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=32, max_length=256)
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "rt_c3d09f82a1b4...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Notas de seguridad:**
- El refresh token anterior queda invalidado (rotación obligatoria).
- Si el refresh token ya fue usado o está revocado → 401 Unauthorized.
- No se emite nuevo refresh si el usuario está `SUSPENDED` o `CLOSED`.

## POST /api/v1/auth/logout
Revocar el refresh token actual (y opcionalmente todos los del usuario) — Permiso: autenticado (JWT)

```python
class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None
    all_sessions: bool = False
```

```json
{
  "detail": "Sesión cerrada correctamente",
  "sessions_revoked": 1
}
```

**Notas de seguridad:**
- Si `all_sessions=true`, se revocan todos los refresh tokens del usuario (logout global).
- El access token actual sigue válido hasta su expiración natural (15 min); el cliente debe descartarlo.

## GET /api/v1/auth/me
Obtener perfil del usuario autenticado (claims del JWT + datos de cuenta) — Permiso: autenticado (JWT)

```python
class UserMeResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: Literal["inversor_retail", "asesor_financiero", "auditor_compliance", "admin_plataforma"]
    country_code: Literal["MX", "CO", "BR", "CL", "AR", "PE"]
    display_currency: CurrencyCode
    status: Literal["ACTIVE", "SUSPENDED", "CLOSED"]
```

```json
{
  "id": "usr_01J9ZAA12B",
  "email": "inversor@ejemplo.com",
  "full_name": "Ana García",
  "role": "inversor_retail",
  "country_code": "MX",
  "display_currency": "MXN",
  "status": "ACTIVE"
}
```

## GET /api/v1/portfolios
Listar portafolios por plataforma/custodio con valoración y costo base aislado — Permiso: `portfolio:read`

```python
class PortfolioSummary(BaseModel):
    id: UUID
    name: str
    broker_name: str
    base_currency: CurrencyCode
    total_value: Decimal
    total_cost_basis: Decimal
    unrealized_pnl: Decimal
```

```json
{
  "display_currency": "USD",
  "items": [
    {
      "id": "pf_ibkr_01",
      "name": "IBKR Inversiones",
      "broker_name": "Interactive Brokers",
      "base_currency": "USD",
      "total_value": "24500.00",
      "total_cost_basis": "19800.00",
      "unrealized_pnl": "4700.00"
    },
    {
      "id": "pf_binance_01",
      "name": "Binance Cold DCA",
      "broker_name": "Binance",
      "base_currency": "USD",
      "total_value": "31200.00",
      "total_cost_basis": "21000.00",
      "unrealized_pnl": "10200.00"
    }
  ]
}
```

## POST /api/v1/portfolios
Crear portafolio / plataforma independiente (ej. IBKR, Binance, GBM+) — Permiso: `portfolio:create`

```python
class PortfolioCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    base_currency: CurrencyCode
    broker_name: str = Field(max_length=60)
    benchmark_ticker: str = Field(default="SPY", max_length=20)
    accounting_method: Literal["WAC", "FIFO"] = "WAC"
```

```json
{
  "id": "pf_ibkr_01",
  "name": "IBKR Inversiones",
  "base_currency": "USD",
  "broker_name": "Interactive Brokers",
  "accounting_method": "WAC"
}
```

## POST /api/v1/portfolios/{portfolio_id}/transactions
Asentar BUY o SELL (parcial/total) con cálculo automático de WAC, ciclo de lote y P&L — Permiso: `transaction:write`

```python
class TransactionCreateRequest(BaseModel):
    asset_ticker: Optional[str] = Field(None, max_length=24)
    type: Literal["BUY", "SELL", "DIVIDEND", "DEPOSIT", "WITHDRAWAL", "FEE"]
    sell_mode: Optional[Literal["PARTIAL", "FULL"]] = None
    executed_at: datetime
    quantity: Decimal = Field(gt=Decimal("0"))
    unit_price: Decimal = Field(ge=Decimal("0"))
    fee_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    tax_withheld: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    trade_currency: CurrencyCode
    fx_rate_to_base: Optional[Decimal] = Field(None, gt=Decimal("0"))
```

```json
{
  "id": "tx_01J9XAA31B",
  "portfolio_id": "pf_ibkr_01",
  "asset_ticker": "BTC",
  "type": "SELL",
  "sale_scope": "PARTIAL",
  "position_cycle_id": 1,
  "remaining_quantity": "0.25000000",
  "wac_unit_cost_after": "64500.00000000",
  "realized_pnl_base": "4111.20000000",
  "cycle_closed": false
}
```

## GET /api/v1/portfolios/{portfolio_id}/transactions
Consultar libro mayor paginado con filtros por ticker, ciclo de lote y tipo — Permiso: `transaction:read`

```python
class TransactionFilterParams(BaseModel):
    ticker: Optional[str] = None
    type: Optional[TransactionType] = None
    position_cycle_id: Optional[int] = None
    limit: int = Field(default=20, ge=1, le=100)
```

```json
{
  "total": 18,
  "items": [
    {
      "id": "tx_01J9XAA31B",
      "executed_at": "2026-11-22T14:00:00Z",
      "asset_ticker": "BTC",
      "type": "SELL",
      "sale_scope": "PARTIAL",
      "position_cycle_id": 1,
      "quantity": "0.15000000",
      "realized_pnl_base": "4111.20000000"
    }
  ]
}
```

## DELETE /api/v1/portfolios/{portfolio_id}/transactions/{tx_id}
Anular operación errónea y recalcular cadena completa de lotes WAC/FIFO — Permiso: `transaction:delete`

```python
class RecomputeStatusResponse(BaseModel):
    deleted_transaction_id: UUID
    recalculation_status: Literal["COMPLETED", "QUEUED"]
    recalculated_cycles: int
```

```json
{
  "deleted_transaction_id": "tx_01J9XAA31B",
  "recalculation_status": "COMPLETED",
  "recalculated_cycles": 2
}
```

## POST /api/v1/goals
Crear meta general (GLOBAL) o específica por activo en plataforma (ASSET_IN_PORTFOLIO) — Permiso: `goal:write`

```python
class GoalCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    scope_type: Literal["GLOBAL", "PORTFOLIO", "ASSET_IN_PORTFOLIO"]
    portfolio_id: Optional[UUID] = None
    asset_ticker: Optional[str] = None
    target_amount: Decimal = Field(gt=Decimal("0"))
    target_currency: CurrencyCode
    target_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_scope_references(self):
        if self.scope_type == "ASSET_IN_PORTFOLIO" and (not self.portfolio_id or not self.asset_ticker):
            raise ValueError("ASSET_IN_PORTFOLIO requiere portfolio_id y asset_ticker")
        return self
```

```json
{
  "id": "goal_viaje_jp",
  "name": "Fondo Viaje Japón 2027",
  "scope_type": "ASSET_IN_PORTFOLIO",
  "linked_platform": "Interactive Brokers",
  "linked_asset_ticker": "BTC",
  "excluded_note": "Excluye tenencias de BTC en otras plataformas (ej. Binance)",
  "current_amount": "9200.00",
  "target_amount": "15000.00",
  "progress_pct": "61.33"
}
```

## GET /api/v1/goals
Listar metas patrimoniales con progreso calculado de forma aislada por scope — Permiso: `goal:read`

```python
class GoalProgressItem(BaseModel):
    id: UUID
    name: str
    scope_type: Literal["GLOBAL", "PORTFOLIO", "ASSET_IN_PORTFOLIO"]
    linked_platform: Optional[str] = None
    linked_asset_ticker: Optional[str] = None
    current_amount: Decimal
    target_amount: Decimal
    progress_pct: Decimal
```

```json
{
  "items": [
    {
      "id": "goal_global_retiro",
      "name": "Patrimonio Total Retiro",
      "scope_type": "GLOBAL",
      "current_amount": "55700.00",
      "target_amount": "150000.00",
      "progress_pct": "37.13"
    },
    {
      "id": "goal_viaje_jp",
      "name": "Fondo Viaje Japón 2027",
      "scope_type": "ASSET_IN_PORTFOLIO",
      "linked_platform": "Interactive Brokers",
      "linked_asset_ticker": "BTC",
      "current_amount": "9200.00",
      "target_amount": "15000.00",
      "progress_pct": "61.33"
    }
  ]
}
```

## POST /api/v1/api-keys
Emitir API Key de solo lectura (aurum_ro_*) para la app paralela "Finanzas" — Permiso: `apikey:manage`

```python
class ApiKeyCreateRequest(BaseModel):
    label: str = Field(min_length=3, max_length=80)
    scopes: list[Literal["external:summary:read"]] = ["external:summary:read"]
    expires_in_days: Optional[int] = Field(default=365, ge=1, le=730)
```

```json
{
  "id": "key_01J9Z112AA",
  "label": "App Finanzas Personales - Producción",
  "plain_api_key": "aurum_ro_8f42b9c1e0a74d3391f2a8b7c6d5e4f3",
  "key_prefix": "aurum_ro_8f42",
  "scopes": ["external:summary:read"],
  "notice": "Guarda esta llave ahora; solo se almacena el hash SHA-256 en AurumCap."
}
```

## GET /api/v1/external/finanzas/summary
Vista agregada de solo lectura para presentar contexto patrimonial en la app "Finanzas" — Permiso: `external:summary:read`

```python
class FinanzasExternalSummaryResponse(BaseModel):
    as_of: datetime
    display_currency: CurrencyCode
    net_worth: NetWorthSnapshot
    platforms: list[PlatformAllocationSummary]
    goals_summary: list[GoalSummaryCompact]
```

```json
{
  "as_of": "2026-11-22T18:15:00Z",
  "display_currency": "MXN",
  "net_worth": {
    "total_value": "1122076.50",
    "total_cost_basis": "821916.00",
    "unrealized_pnl": "300160.50",
    "unrealized_pnl_pct": "36.52",
    "twr_ytd_pct": "18.40"
  },
  "platforms": [
    { "broker_name": "Binance", "value": "628524.00", "weight_pct": "56.01" },
    { "broker_name": "Interactive Brokers", "value": "493552.50", "weight_pct": "43.99" }
  ],
  "goals_summary": [
    { "name": "Patrimonio Total Retiro", "scope_type": "GLOBAL", "progress_pct": "37.13" },
    { "name": "Fondo Viaje Japón 2027", "scope_type": "ASSET_IN_PORTFOLIO", "progress_pct": "61.33" }
  ]
}
```

## POST /api/v1/portfolios/{portfolio_id}/imports/csv
Cargar extracto CSV de broker/exchange con vista previa e idempotencia SHA-256 — Permiso: `transaction:write`

```python
class CsvImportResponse(BaseModel):
    import_batch_id: UUID
    dry_run: bool
    rows_parsed: int
    rows_duplicate_skipped: int
    rows_invalid: int
```

```json
{
  "import_batch_id": "imp_01J9XCC901",
  "dry_run": true,
  "rows_parsed": 18,
  "rows_duplicate_skipped": 4,
  "rows_invalid": 0
}
```

## GET /api/v1/fx-rates/latest
Consultar tipos de cambio vigentes y series históricas por par y fuente LATAM — Permiso: `market:read`

```python
class FxRateItem(BaseModel):
    quote: CurrencyCode
    source: str
    rate: Decimal
    rate_date: date
```

```json
{
  "base": "USD",
  "as_of": "2026-11-22",
  "rates": [
    { "quote": "MXN", "source": "FIX_BANXICO", "rate": "20.1450" },
    { "quote": "COP", "source": "TRM", "rate": "4382.1000" },
    { "quote": "ARS", "source": "MEP", "rate": "1142.5000" }
  ]
}
```

## GET /api/v1/portfolios/{portfolio_id}/analytics/overview
Obtener holdings vigentes por ciclo de lote, TWR, XIRR y atribución Precio vs FX — Permiso: `analytics:read`

```python
class PortfolioAnalyticsResponse(BaseModel):
    portfolio_id: UUID
    display_currency: CurrencyCode
    period: Literal["1M", "3M", "YTD", "1Y", "3Y", "MAX"]
    metrics: PerformanceMetrics
```

```json
{
  "portfolio_id": "pf_ibkr_01",
  "display_currency": "USD",
  "period": "YTD",
  "metrics": {
    "total_value": "24500.00",
    "twr_pct": "14.82",
    "xirr_pct": "16.10",
    "asset_return_pct": "14.82",
    "fx_attribution_pct": "0.00"
  }
}
```