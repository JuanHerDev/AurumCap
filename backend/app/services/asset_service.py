from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.asset import Asset
from app.providers.massive_provider import massive_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider


# Símbolos conocidos de crypto para distinguir sin llamar a la DB
# Se puede expandir — es solo para el routing inicial
KNOWN_CRYPTO_SYMBOLS = {
    "BTC", "ETH", "SOL", "BNB", "USDT", "USDC", "XRP",
    "ADA", "DOGE", "AVAX", "MATIC", "DOT", "LTC", "LINK",
}


async def get_or_create_asset(symbol: str, db: AsyncSession) -> Asset | None:
    """
    Patrón cache-aside sobre la tabla assets:
    1. Buscar en DB → si existe, devolver directo
    2. Si no existe → llamar al provider correcto
    3. Guardar datos estáticos en DB
    4. Devolver el asset

    Los datos estáticos (nombre, exchange, sector, etc.) se guardan una sola vez.
    Los precios NUNCA se guardan aquí — esos viven en price_history.
    """
    symbol = symbol.upper()

    # 1. Buscar en DB
    result = await db.execute(
        select(Asset).where(Asset.symbol == symbol)
    )
    asset = result.scalar_one_or_none()

    if asset:
        return asset

    # 2. No existe — determinar tipo y llamar al provider
    is_crypto = symbol in KNOWN_CRYPTO_SYMBOLS

    if is_crypto:
        return await _create_crypto_asset(symbol, db)
    else:
        # Intentar como stock/ETF primero
        asset = await _create_stock_asset(symbol, db)
        if asset:
            return asset

        # Si Massive no lo encuentra, intentar como crypto
        return await _create_crypto_asset(symbol, db)


async def _create_stock_asset(symbol: str, db: AsyncSession) -> Asset | None:
    """Obtiene metadata de Massive y crea el asset en DB."""
    metadata = await massive_provider.get_asset_metadata(symbol)

    if not metadata:
        return None

    asset = Asset(
        symbol=metadata.symbol,
        name=metadata.name,
        asset_type=metadata.asset_type,
        exchange=metadata.exchange,
        sector=metadata.sector,
        industry=metadata.industry,
        description=metadata.description,
    )
    db.add(asset)
    await db.flush()  # Obtener el id sin cerrar la transacción
    return asset


async def _create_crypto_asset(symbol: str, db: AsyncSession) -> Asset | None:
    """Obtiene metadata de CoinMarketCap y crea el asset en DB."""
    metadata = await coinmarketcap_provider.get_metadata(symbol)

    if not metadata:
        return None

    asset = Asset(
        symbol=metadata.symbol,
        name=metadata.name,
        asset_type="crypto",
        exchange="crypto",
        description=metadata.description,
    )
    db.add(asset)
    await db.flush()
    return asset