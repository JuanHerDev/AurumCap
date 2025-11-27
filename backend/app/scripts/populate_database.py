# scripts/populate_database.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.historic import (
    CryptoProfile, CryptoSymbolMapping, CryptoCategory,
    StockProfile, StockSector, StockIndustry, StockExchange,
    StockFundamentalsCurrent, EconomicData, EconomicCalendarCache
)
from services import (
    get_crypto_profile, get_crypto_categories,
    get_stock_profile, get_stock_fundamentals,
    get_economic_calendar
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePopulator:
    def __init__(self):
        self.db = SessionLocal()
        
    def __del__(self):
        self.db.close()

    async def populate_crypto_profiles(self, symbols: List[str]):
        """Poblar perfiles de criptomonedas"""
        logger.info(f"Populating crypto profiles for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                profile_data = await get_crypto_profile(symbol)
                if not profile_data:
                    logger.warning(f"No profile data for {symbol}")
                    continue

                # Verificar si ya existe
                existing = self.db.query(CryptoProfile).filter_by(id=profile_data.id).first()
                if existing:
                    # Actualizar existente
                    existing.symbol = profile_data.symbol
                    existing.name = profile_data.name
                    existing.description_es = profile_data.description_es
                    existing.description_en = profile_data.description_en
                    existing.website = profile_data.website
                    existing.whitepaper_url = profile_data.whitepaper_url
                    existing.github_url = profile_data.github_url
                    existing.categories = profile_data.categories
                    existing.market_cap_rank = profile_data.market_cap_rank
                    existing.logo_url = profile_data.logo_url
                    existing.tags = profile_data.tags
                    existing.last_updated = datetime.now()
                    existing.cache_until = datetime.now() + timedelta(days=30)
                else:
                    # Crear nuevo
                    crypto_profile = CryptoProfile(
                        id=profile_data.id,
                        symbol=profile_data.symbol,
                        name=profile_data.name,
                        description_es=profile_data.description_es,
                        description_en=profile_data.description_en,
                        website=profile_data.website,
                        whitepaper_url=profile_data.whitepaper_url,
                        github_url=profile_data.github_url,
                        categories=profile_data.categories,
                        market_cap_rank=profile_data.market_cap_rank,
                        logo_url=profile_data.logo_url,
                        tags=profile_data.tags,
                        last_updated=datetime.now(),
                        cache_until=datetime.now() + timedelta(days=30)
                    )
                    self.db.add(crypto_profile)

                # Actualizar mapeo de símbolos
                symbol_mapping = self.db.query(CryptoSymbolMapping).filter_by(symbol=symbol.upper()).first()
                if not symbol_mapping:
                    symbol_mapping = CryptoSymbolMapping(
                        symbol=symbol.upper(),
                        coingecko_id=profile_data.id,
                        is_active=True,
                        created_at=datetime.now()
                    )
                    self.db.add(symbol_mapping)

                self.db.commit()
                logger.info(f"✅ Updated crypto profile for {symbol}")

                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                self.db.rollback()

    async def populate_crypto_categories(self):
        """Poblar categorías de criptomonedas"""
        logger.info("Populating crypto categories...")
        
        categories = await get_crypto_categories()
        for category_data in categories:
            try:
                category = CryptoCategory(
                    category_id=category_data['category_id'],
                    name_es=category_data['name'],
                    name_en=category_data['name'],  # Same for now
                    description=f"Category for {category_data['name']}",
                    created_at=datetime.now()
                )
                self.db.merge(category)
                self.db.commit()
            except Exception as e:
                logger.error(f"Error processing category {category_data['category_id']}: {e}")
                self.db.rollback()

    async def populate_stock_profiles(self, symbols: List[str]):
        """Poblar perfiles de stocks"""
        logger.info(f"Populating stock profiles for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                profile_data = await get_stock_profile(symbol)
                if not profile_data:
                    logger.warning(f"No profile data for {symbol}")
                    continue

                existing = self.db.query(StockProfile).filter_by(symbol=symbol.upper()).first()
                if existing:
                    # Actualizar existente
                    existing.company_name = profile_data.company_name
                    existing.sector = profile_data.sector
                    existing.industry = profile_data.industry
                    existing.country = profile_data.country
                    existing.currency = profile_data.currency
                    existing.exchange = profile_data.exchange
                    existing.market_cap = profile_data.market_cap
                    existing.employees = profile_data.employees
                    existing.website = profile_data.website
                    existing.logo_url = profile_data.logo_url
                    existing.ipo_date = profile_data.ipo_date
                    existing.last_updated = datetime.now()
                    existing.cache_until = datetime.now() + timedelta(days=90)
                else:
                    # Crear nuevo
                    stock_profile = StockProfile(
                        symbol=symbol.upper(),
                        company_name=profile_data.company_name,
                        description=profile_data.description,
                        sector=profile_data.sector,
                        industry=profile_data.industry,
                        country=profile_data.country,
                        currency=profile_data.currency,
                        exchange=profile_data.exchange,
                        market_cap=profile_data.market_cap,
                        employees=profile_data.employees,
                        website=profile_data.website,
                        logo_url=profile_data.logo_url,
                        ipo_date=profile_data.ipo_date,
                        last_updated=datetime.now(),
                        cache_until=datetime.now() + timedelta(days=90)
                    )
                    self.db.add(stock_profile)

                self.db.commit()
                logger.info(f"✅ Updated stock profile for {symbol}")

                # Rate limiting
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing stock {symbol}: {e}")
                self.db.rollback()

    async def populate_stock_fundamentals(self, symbols: List[str]):
        """Poblar fundamentales de stocks"""
        logger.info(f"Populating stock fundamentals for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                fundamentals_data = await get_stock_fundamentals(symbol)
                if not fundamentals_data:
                    logger.warning(f"No fundamentals data for {symbol}")
                    continue

                existing = self.db.query(StockFundamentalsCurrent).filter_by(symbol=symbol.upper()).first()
                if existing:
                    # Actualizar existente
                    existing.pe_ratio = fundamentals_data.pe_ratio
                    existing.eps = fundamentals_data.eps
                    existing.dividend_yield = fundamentals_data.dividend_yield
                    existing.market_cap = fundamentals_data.market_cap
                    existing.revenue = fundamentals_data.revenue
                    existing.net_income = fundamentals_data.net_income
                    existing.profit_margin = fundamentals_data.profit_margin
                    existing.total_assets = fundamentals_data.total_assets
                    existing.total_liabilities = fundamentals_data.total_liabilities
                    existing.cash = fundamentals_data.cash
                    existing.year_high = fundamentals_data.year_high
                    existing.year_low = fundamentals_data.year_low
                    existing.volume_avg = fundamentals_data.volume_avg
                    existing.last_earnings_date = fundamentals_data.last_earnings_date
                    existing.next_earnings_date = fundamentals_data.next_earnings_date
                    existing.fiscal_year_end = fundamentals_data.fiscal_year_end
                    existing.last_updated = datetime.now()
                    existing.cache_until = datetime.now() + timedelta(days=7)
                else:
                    # Crear nuevo
                    fundamentals = StockFundamentalsCurrent(
                        symbol=symbol.upper(),
                        pe_ratio=fundamentals_data.pe_ratio,
                        eps=fundamentals_data.eps,
                        dividend_yield=fundamentals_data.dividend_yield,
                        market_cap=fundamentals_data.market_cap,
                        revenue=fundamentals_data.revenue,
                        net_income=fundamentals_data.net_income,
                        profit_margin=fundamentals_data.profit_margin,
                        total_assets=fundamentals_data.total_assets,
                        total_liabilities=fundamentals_data.total_liabilities,
                        cash=fundamentals_data.cash,
                        year_high=fundamentals_data.year_high,
                        year_low=fundamentals_data.year_low,
                        volume_avg=fundamentals_data.volume_avg,
                        last_earnings_date=fundamentals_data.last_earnings_date,
                        next_earnings_date=fundamentals_data.next_earnings_date,
                        fiscal_year_end=fundamentals_data.fiscal_year_end,
                        last_updated=datetime.now(),
                        cache_until=datetime.now() + timedelta(days=7)
                    )
                    self.db.add(fundamentals)

                self.db.commit()
                logger.info(f"✅ Updated fundamentals for {symbol}")

                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing fundamentals for {symbol}: {e}")
                self.db.rollback()

    async def populate_economic_data(self):
        """Poblar datos económicos"""
        logger.info("Populating economic data...")
        
        try:
            events = await get_economic_calendar()
            for event in events:
                try:
                    cache_entry = EconomicCalendarCache(
                        event_id=event.event_id,
                        event_name=event.event_name,
                        country=event.country,
                        importance=event.importance,
                        event_date=event.event_date,
                        actual_value=float(event.actual_value) if event.actual_value else None,
                        forecast_value=float(event.forecast_value) if event.forecast_value else None,
                        previous_value=float(event.previous_value) if event.previous_value else None,
                        last_updated=datetime.now(),
                        cache_strategy="past_events" if event.event_date < datetime.now() else "upcoming"
                    )
                    self.db.merge(cache_entry)
                    self.db.commit()
                except Exception as e:
                    logger.error(f"Error processing economic event {event.event_id}: {e}")
                    self.db.rollback()
                    
            logger.info(f"✅ Updated {len(events)} economic events")
            
        except Exception as e:
            logger.error(f"Error populating economic data: {e}")

async def main():
    """Función principal para poblar la base de datos"""
    populator = DatabasePopulator()
    
    # Símbolos de ejemplo - puedes expandir esta lista
    crypto_symbols = ["btc", "eth", "ada", "dot", "sol", "matic", "avax", "link", "uni", "aave"]
    stock_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC"]
    
    # Ejecutar pobladores
    await populator.populate_crypto_categories()
    await populator.populate_crypto_profiles(crypto_symbols)
    await populator.populate_stock_profiles(stock_symbols)
    await populator.populate_stock_fundamentals(stock_symbols)
    await populator.populate_economic_data()
    
    logger.info("🎉 Database population completed!")

if __name__ == "__main__":
    asyncio.run(main())