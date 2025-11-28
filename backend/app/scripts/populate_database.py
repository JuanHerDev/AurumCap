# scripts/populate_database.py - Improved version with crypto mappings
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.crypto.crypto_models import CryptoProfile, CryptoSymbolMapping, CryptoCategory
from app.models.stocks.stock_models import StockProfile, StockSector, StockIndustry, StockExchange
from app.models.fundamentals.fundamental_models import StockFundamentalsCurrent
from app.models.macro.macro_models import EconomicData, EconomicCalendarCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabasePopulator:
    def __init__(self):
        self.db = SessionLocal()
        
    def __del__(self):
        self.db.close()

    def populate_crypto_symbol_mappings(self):
        """Populate cryptocurrency symbol mappings - CRITICAL FOR PRICE FETCHING"""
        logger.info("Populating cryptocurrency symbol mappings...")
        
        # Common cryptocurrency mappings
        common_cryptos = [
            {'symbol': 'BTC', 'coingecko_id': 'bitcoin', 'name': 'Bitcoin'},
            {'symbol': 'ETH', 'coingecko_id': 'ethereum', 'name': 'Ethereum'},
            {'symbol': 'ADA', 'coingecko_id': 'cardano', 'name': 'Cardano'},
            {'symbol': 'DOT', 'coingecko_id': 'polkadot', 'name': 'Polkadot'},
            {'symbol': 'LINK', 'coingecko_id': 'chainlink', 'name': 'Chainlink'},
            {'symbol': 'LTC', 'coingecko_id': 'litecoin', 'name': 'Litecoin'},
            {'symbol': 'BCH', 'coingecko_id': 'bitcoin-cash', 'name': 'Bitcoin Cash'},
            {'symbol': 'XRP', 'coingecko_id': 'ripple', 'name': 'Ripple'},
            {'symbol': 'SOL', 'coingecko_id': 'solana', 'name': 'Solana'},
            {'symbol': 'AVAX', 'coingecko_id': 'avalanche-2', 'name': 'Avalanche'},
            {'symbol': 'MATIC', 'coingecko_id': 'matic-network', 'name': 'Polygon'},
            {'symbol': 'DOGE', 'coingecko_id': 'dogecoin', 'name': 'Dogecoin'},
            {'symbol': 'ATOM', 'coingecko_id': 'cosmos', 'name': 'Cosmos'},
            {'symbol': 'XLM', 'coingecko_id': 'stellar', 'name': 'Stellar'},
            {'symbol': 'EOS', 'coingecko_id': 'eos', 'name': 'EOS'},
            {'symbol': 'BNB', 'coingecko_id': 'binancecoin', 'name': 'Binance Coin'},
            {'symbol': 'USDT', 'coingecko_id': 'tether', 'name': 'Tether'},
            {'symbol': 'USDC', 'coingecko_id': 'usd-coin', 'name': 'USD Coin'},
            {'symbol': 'DAI', 'coingecko_id': 'dai', 'name': 'Dai'},
            {'symbol': 'UNI', 'coingecko_id': 'uniswap', 'name': 'Uniswap'},
            {'symbol': 'AAVE', 'coingecko_id': 'aave', 'name': 'Aave'},
            {'symbol': 'MKR', 'coingecko_id': 'maker', 'name': 'Maker'},
            {'symbol': 'COMP', 'coingecko_id': 'compound-governance-token', 'name': 'Compound'},
            {'symbol': 'YFI', 'coingecko_id': 'yearn-finance', 'name': 'Yearn Finance'},
            {'symbol': 'SNX', 'coingecko_id': 'havven', 'name': 'Synthetix'},
        ]
        
        added_count = 0
        for crypto in common_cryptos:
            try:
                # Check if mapping already exists
                existing = self.db.query(CryptoSymbolMapping).filter(
                    CryptoSymbolMapping.symbol == crypto['symbol']
                ).first()
                
                if not existing:
                    # Create new mapping
                    symbol_mapping = CryptoSymbolMapping(
                        symbol=crypto['symbol'],
                        coingecko_id=crypto['coingecko_id'],
                        is_active=True,
                        created_at=datetime.now()
                    )
                    self.db.add(symbol_mapping)
                    added_count += 1
                    logger.info(f"✅ Added mapping: {crypto['symbol']} -> {crypto['coingecko_id']}")
                else:
                    # Update existing mapping if needed
                    if existing.coingecko_id != crypto['coingecko_id']:
                        existing.coingecko_id = crypto['coingecko_id']
                        existing.is_active = True
                        logger.info(f"↻ Updated mapping: {crypto['symbol']} -> {crypto['coingecko_id']}")
                    else:
                        logger.debug(f"✓ Mapping exists: {crypto['symbol']} -> {crypto['coingecko_id']}")
                        
            except Exception as e:
                logger.error(f"❌ Error processing {crypto['symbol']}: {e}")
                self.db.rollback()
        
        self.db.commit()
        logger.info(f"🎉 Successfully processed {added_count} new cryptocurrency mappings")
        return added_count

    def populate_crypto_categories(self):
        """Populate basic cryptocurrency categories"""
        logger.info("Populating cryptocurrency categories...")
        
        categories = [
            {
                'category_id': 'defi',
                'name_es': 'Finanzas Descentralizadas',
                'name_en': 'Decentralized Finance',
                'description': 'Protocolos y aplicaciones de finanzas descentralizadas'
            },
            {
                'category_id': 'nft',
                'name_es': 'Tokens No Fungibles', 
                'name_en': 'Non-Fungible Tokens',
                'description': 'Tokens únicos y coleccionables'
            },
            {
                'category_id': 'gaming',
                'name_es': 'Juegos Blockchain',
                'name_en': 'Blockchain Gaming',
                'description': 'Juegos y plataformas de gaming en blockchain'
            },
            {
                'category_id': 'layer-1',
                'name_es': 'Capa 1',
                'name_en': 'Layer 1',
                'description': 'Blockchains de capa base como Ethereum, Solana, etc.'
            },
            {
                'category_id': 'layer-2',
                'name_es': 'Capa 2',
                'name_en': 'Layer 2', 
                'description': 'Soluciones de escalabilidad de capa 2'
            },
            {
                'category_id': 'stablecoin',
                'name_es': 'Monedas Estables',
                'name_en': 'Stablecoins',
                'description': 'Criptomonedas vinculadas a monedas fiduciarias'
            },
            {
                'category_id': 'exchange-token',
                'name_es': 'Tokens de Exchange',
                'name_en': 'Exchange Tokens',
                'description': 'Tokens nativos de exchanges de criptomonedas'
            },
            {
                'category_id': 'oracle',
                'name_es': 'Oráculos',
                'name_en': 'Oracles',
                'description': 'Protocolos de oráculos para datos externos'
            }
        ]
        
        for category_data in categories:
            try:
                category = CryptoCategory(
                    category_id=category_data['category_id'],
                    name_es=category_data['name_es'],
                    name_en=category_data['name_en'],
                    description=category_data['description'],
                    created_at=datetime.now()
                )
                self.db.merge(category)
                logger.info(f"✅ Added category: {category_data['name_es']}")
            except Exception as e:
                logger.error(f"❌ Error processing category {category_data['category_id']}: {e}")
                self.db.rollback()
        
        self.db.commit()
        logger.info("🎉 Successfully populated cryptocurrency categories")

    def populate_stock_sectors(self):
        """Populate stock sectors and industries"""
        logger.info("Populating stock sectors and industries...")
        
        sectors = [
            {
                'sector_id': 'technology',
                'sector_name': 'Technology',
                'description': 'Technology companies including software, hardware, and IT services',
                'typical_pe_ratio': 25.0,
                'typical_dividend_yield': 0.8,
                'typical_roe': 18.0
            },
            {
                'sector_id': 'healthcare', 
                'sector_name': 'Healthcare',
                'description': 'Healthcare providers, pharmaceuticals, and medical devices',
                'typical_pe_ratio': 20.0,
                'typical_dividend_yield': 1.5,
                'typical_roe': 15.0
            },
            {
                'sector_id': 'financial',
                'sector_name': 'Financial Services',
                'description': 'Banks, insurance companies, and financial institutions',
                'typical_pe_ratio': 12.0,
                'typical_dividend_yield': 3.0,
                'typical_roe': 12.0
            },
            {
                'sector_id': 'consumer',
                'sector_name': 'Consumer Goods',
                'description': 'Consumer products, retail, and services',
                'typical_pe_ratio': 18.0,
                'typical_dividend_yield': 2.0,
                'typical_roe': 16.0
            },
            {
                'sector_id': 'industrial',
                'sector_name': 'Industrial',
                'description': 'Manufacturing, construction, and industrial services',
                'typical_pe_ratio': 16.0,
                'typical_dividend_yield': 2.2,
                'typical_roe': 14.0
            }
        ]
        
        for sector_data in sectors:
            try:
                sector = StockSector(
                    sector_id=sector_data['sector_id'],
                    sector_name=sector_data['sector_name'],
                    description=sector_data['description'],
                    typical_pe_ratio=sector_data['typical_pe_ratio'],
                    typical_dividend_yield=sector_data['typical_dividend_yield'],
                    typical_roe=sector_data['typical_roe'],
                    created_at=datetime.now()
                )
                self.db.merge(sector)
                logger.info(f"✅ Added sector: {sector_data['sector_name']}")
            except Exception as e:
                logger.error(f"❌ Error processing sector {sector_data['sector_id']}: {e}")
                self.db.rollback()
        
        self.db.commit()
        logger.info("🎉 Successfully populated stock sectors")

    def populate_stock_exchanges(self):
        """Populate stock exchanges"""
        logger.info("Populating stock exchanges...")
        
        exchanges = [
            {
                'exchange_code': 'NASDAQ',
                'exchange_name': 'NASDAQ Stock Market',
                'country': 'United States',
                'currency': 'USD',
                'opening_time': '09:30:00',
                'closing_time': '16:00:00',
                'timezone': 'America/New_York'
            },
            {
                'exchange_code': 'NYSE',
                'exchange_name': 'New York Stock Exchange', 
                'country': 'United States',
                'currency': 'USD',
                'opening_time': '09:30:00',
                'closing_time': '16:00:00',
                'timezone': 'America/New_York'
            },
            {
                'exchange_code': 'LSE',
                'exchange_name': 'London Stock Exchange',
                'country': 'United Kingdom', 
                'currency': 'GBP',
                'opening_time': '08:00:00',
                'closing_time': '16:30:00',
                'timezone': 'Europe/London'
            }
        ]
        
        for exchange_data in exchanges:
            try:
                exchange = StockExchange(
                    exchange_code=exchange_data['exchange_code'],
                    exchange_name=exchange_data['exchange_name'],
                    country=exchange_data['country'],
                    currency=exchange_data['currency'],
                    opening_time=exchange_data['opening_time'],
                    closing_time=exchange_data['closing_time'],
                    timezone=exchange_data['timezone'],
                    created_at=datetime.now()
                )
                self.db.merge(exchange)
                logger.info(f"✅ Added exchange: {exchange_data['exchange_name']}")
            except Exception as e:
                logger.error(f"❌ Error processing exchange {exchange_data['exchange_code']}: {e}")
                self.db.rollback()
        
        self.db.commit()
        logger.info("🎉 Successfully populated stock exchanges")

    def populate_sample_stock_profiles(self):
        """Populate sample stock profiles for testing"""
        logger.info("Populating sample stock profiles...")
        
        sample_stocks = [
            {
                'symbol': 'AAPL',
                'company_name': 'Apple Inc.',
                'description': 'Consumer electronics, software, and online services',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'country': 'United States',
                'currency': 'USD',
                'exchange': 'NASDAQ',
                'market_cap': 2800000000000,
                'employees': 164000,
                'website': 'https://www.apple.com',
                'logo_url': 'https://logo.clearbit.com/apple.com',
                'ipo_date': '1980-12-12'
            },
            {
                'symbol': 'MSFT',
                'company_name': 'Microsoft Corporation',
                'description': 'Software, services, devices, and solutions',
                'sector': 'Technology', 
                'industry': 'Software',
                'country': 'United States',
                'currency': 'USD',
                'exchange': 'NASDAQ',
                'market_cap': 2100000000000,
                'employees': 221000,
                'website': 'https://www.microsoft.com',
                'logo_url': 'https://logo.clearbit.com/microsoft.com',
                'ipo_date': '1986-03-13'
            },
            {
                'symbol': 'GOOGL',
                'company_name': 'Alphabet Inc.',
                'description': 'Technology company focusing on internet services',
                'sector': 'Technology',
                'industry': 'Internet Services',
                'country': 'United States', 
                'currency': 'USD',
                'exchange': 'NASDAQ',
                'market_cap': 1800000000000,
                'employees': 190234,
                'website': 'https://abc.xyz',
                'logo_url': 'https://logo.clearbit.com/abc.xyz',
                'ipo_date': '2004-08-19'
            }
        ]
        
        for stock_data in sample_stocks:
            try:
                stock_profile = StockProfile(
                    symbol=stock_data['symbol'],
                    company_name=stock_data['company_name'],
                    description=stock_data['description'],
                    sector=stock_data['sector'],
                    industry=stock_data['industry'],
                    country=stock_data['country'],
                    currency=stock_data['currency'],
                    exchange=stock_data['exchange'],
                    market_cap=stock_data['market_cap'],
                    employees=stock_data['employees'],
                    website=stock_data['website'],
                    logo_url=stock_data['logo_url'],
                    ipo_date=datetime.strptime(stock_data['ipo_date'], '%Y-%m-%d').date(),
                    last_updated=datetime.now(),
                    cache_until=datetime.now() + timedelta(days=90)
                )
                self.db.merge(stock_profile)
                logger.info(f"✅ Added stock: {stock_data['symbol']} - {stock_data['company_name']}")
            except Exception as e:
                logger.error(f"❌ Error processing stock {stock_data['symbol']}: {e}")
                self.db.rollback()
        
        self.db.commit()
        logger.info("🎉 Successfully populated sample stock profiles")

    def populate_sample_crypto_profiles(self):
        """Populate sample cryptocurrency profiles using CoinGecko data"""
        logger.info("Populating sample cryptocurrency profiles...")
        
        # We'll create basic profiles - in a real scenario you'd fetch from CoinGecko
        sample_cryptos = [
            {
                'id': 'bitcoin',
                'symbol': 'BTC',
                'name': 'Bitcoin',
                'description_en': 'Bitcoin is a decentralized digital currency that enables peer-to-peer transactions without intermediaries.',
                'description_es': 'Bitcoin es una moneda digital descentralizada que permite transacciones peer-to-peer sin intermediarios.',
                'website': 'https://bitcoin.org',
                'categories': ['layer-1', 'store-of-value'],
                'market_cap_rank': 1,
                'logo_url': 'https://assets.coingecko.com/coins/images/1/large/bitcoin.png'
            },
            {
                'id': 'ethereum', 
                'symbol': 'ETH',
                'name': 'Ethereum',
                'description_en': 'Ethereum is a decentralized, open-source blockchain with smart contract functionality.',
                'description_es': 'Ethereum es una blockchain descentralizada de código abierto con funcionalidad de contratos inteligentes.',
                'website': 'https://ethereum.org',
                'categories': ['layer-1', 'smart-contracts'],
                'market_cap_rank': 2,
                'logo_url': 'https://assets.coingecko.com/coins/images/279/large/ethereum.png'
            }
        ]
        
        for crypto_data in sample_cryptos:
            try:
                crypto_profile = CryptoProfile(
                    id=crypto_data['id'],
                    symbol=crypto_data['symbol'],
                    name=crypto_data['name'],
                    description_en=crypto_data['description_en'],
                    description_es=crypto_data['description_es'],
                    website=crypto_data['website'],
                    categories=crypto_data['categories'],
                    market_cap_rank=crypto_data['market_cap_rank'],
                    logo_url=crypto_data['logo_url'],
                    last_updated=datetime.now(),
                    cache_until=datetime.now() + timedelta(days=30)
                )
                self.db.merge(crypto_profile)
                logger.info(f"✅ Added crypto profile: {crypto_data['symbol']} - {crypto_data['name']}")
            except Exception as e:
                logger.error(f"❌ Error processing crypto {crypto_data['symbol']}: {e}")
                self.db.rollback()
        
        self.db.commit()
        logger.info("🎉 Successfully populated sample cryptocurrency profiles")

    def populate_sample_fundamentals(self):
        """Populate sample stock fundamentals"""
        logger.info("Populating sample stock fundamentals...")
        
        sample_fundamentals = [
            {
                'symbol': 'AAPL',
                'pe_ratio': 28.5,
                'eps': 6.13,
                'dividend_yield': 0.5,
                'market_cap': 2800000000000,
                'revenue': 383000000000,
                'net_income': 97000000000,
                'profit_margin': 25.3,
                'year_high': 182.94,
                'year_low': 124.17,
                'volume_avg': 55000000
            },
            {
                'symbol': 'MSFT',
                'pe_ratio': 32.1, 
                'eps': 9.81,
                'dividend_yield': 0.7,
                'market_cap': 2100000000000,
                'revenue': 211000000000,
                'net_income': 78000000000,
                'profit_margin': 36.9,
                'year_high': 366.78,
                'year_low': 219.35,
                'volume_avg': 25000000
            }
        ]
        
        for fundamental_data in sample_fundamentals:
            try:
                fundamentals = StockFundamentalsCurrent(
                    symbol=fundamental_data['symbol'],
                    pe_ratio=fundamental_data['pe_ratio'],
                    eps=fundamental_data['eps'],
                    dividend_yield=fundamental_data['dividend_yield'],
                    market_cap=fundamental_data['market_cap'],
                    revenue=fundamental_data['revenue'],
                    net_income=fundamental_data['net_income'],
                    profit_margin=fundamental_data['profit_margin'],
                    year_high=fundamental_data['year_high'],
                    year_low=fundamental_data['year_low'],
                    volume_avg=fundamental_data['volume_avg'],
                    last_updated=datetime.now(),
                    cache_until=datetime.now() + timedelta(days=7)
                )
                self.db.merge(fundamentals)
                logger.info(f"✅ Added fundamentals for: {fundamental_data['symbol']}")
            except Exception as e:
                logger.error(f"❌ Error processing fundamentals for {fundamental_data['symbol']}: {e}")
                self.db.rollback()
        
        self.db.commit()
        logger.info("🎉 Successfully populated sample fundamentals")

async def main():
    """Main function to populate the database"""
    logger.info("🚀 Starting database population...")
    
    populator = DatabasePopulator()
    
    try:
        # Execute population in order of dependency
        mappings_count = populator.populate_crypto_symbol_mappings()  # CRITICAL - must be first
        populator.populate_crypto_categories()
        populator.populate_stock_sectors()
        populator.populate_stock_exchanges()
        populator.populate_sample_stock_profiles()
        populator.populate_sample_crypto_profiles()
        populator.populate_sample_fundamentals()
        
        logger.info("🎉 Database population completed successfully!")
        logger.info(f"📊 Added/Updated {mappings_count} cryptocurrency mappings")
        logger.info("💡 Your portfolio should now show real prices for BTC and other cryptocurrencies!")
        
    except Exception as e:
        logger.error(f"❌ Database population failed: {e}")
        raise
    finally:
        # Ensure database connection is closed
        if hasattr(populator, 'db'):
            populator.db.close()

if __name__ == "__main__":
    asyncio.run(main())