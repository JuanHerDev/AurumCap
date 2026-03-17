"""
AurumCap — Seed script
Pobla la DB con activos reales desde los providers,
un usuario de prueba y holdings de ejemplo.

Uso:
    cd backend
    python -m scripts.seed
"""

import asyncio
import sys
import os

# Asegurar que el path incluye el backend/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app.db.base

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.models.holdings import Holdings
from app.services.asset_service import get_or_create_asset
import bcrypt


# --- Configuración del seed ---


TEST_USER = {
    "email": "test@aurumcap.com",
    "password": "aurumcap123",
    "full_name": "Test User",
}

# symbol → (quantity, avg_price)
TEST_HOLDINGS = {
    "BTC":  (0.5,   45000.00),
    "AAPL": (10.0,  175.00),
    "TSLA": (5.0,   220.00),
    "AMZN": (3.0,   185.00),
    "QQQ":  (8.0,   430.00),
    "NNE":  (50.0,  15.00),
}


# --- Helpers ---

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def seed_assets(db) -> dict[str, int]:
    """Crea o recupera todos los assets necesarios. Devuelve {symbol: asset_id}."""
    print("\n📦 Seeding assets...")
    asset_ids = {}

    for symbol in TEST_HOLDINGS.keys():
        print(f"  → {symbol}...", end=" ")
        asset = await get_or_create_asset(symbol, db)

        if asset:
            asset_ids[symbol] = asset.id
            print(f"✓ (id={asset.id}, type={asset.asset_type})")
        else:
            print(f"✗ No se pudo obtener metadata para {symbol}")

    return asset_ids


async def seed_user(db) -> int:
    """Crea el usuario de prueba si no existe. Devuelve user_id."""
    print("\n👤 Seeding user...")

    result = await db.execute(
        select(User).where(User.email == TEST_USER["email"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  → Usuario ya existe (id={existing.id}), saltando...")
        return existing.id

    user = User(
        email=TEST_USER["email"],
        password_hash=_hash_password(TEST_USER["password"]),
        full_name=TEST_USER["full_name"],
    )
    db.add(user)
    await db.flush()
    print(f"  → Creado: {TEST_USER['email']} (id={user.id})")
    return user.id


async def seed_holdings(db, user_id: int, asset_ids: dict[str, int]):
    """Crea holdings para el usuario de prueba."""
    print("\n💼 Seeding holdings...")

    for symbol, (quantity, avg_price) in TEST_HOLDINGS.items():
        asset_id = asset_ids.get(symbol)
        if not asset_id:
            print(f"  → {symbol} ✗ sin asset_id, saltando...")
            continue

        # Verificar si ya existe el holding
        result = await db.execute(
            select(Holdings).where(
                Holdings.user_id == user_id,
                Holdings.asset_id == asset_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  → {symbol} ya existe, saltando...")
            continue

        holding = Holdings(
            user_id=user_id,
            asset_id=asset_id,
            quantity=quantity,
            avg_price=avg_price,
        )
        db.add(holding)
        print(f"  → {symbol}: {quantity} @ ${avg_price} ✓")


async def run_seed():
    print("🌱 AurumCap Seed Script")
    print("=" * 40)

    async with AsyncSessionLocal() as db:
        try:
            # 1. Assets
            asset_ids = await seed_assets(db)

            # 2. Usuario
            user_id = await seed_user(db)

            # 3. Holdings
            await seed_holdings(db, user_id, asset_ids)

            # 4. Commit todo junto
            await db.commit()

            print("\n" + "=" * 40)
            print("✅ Seed completado exitosamente")
            print(f"   Usuario: {TEST_USER['email']}")
            print(f"   Password: {TEST_USER['password']}")
            print(f"   Holdings: {len(asset_ids)} activos")

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())