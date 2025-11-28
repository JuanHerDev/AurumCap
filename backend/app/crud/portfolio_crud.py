from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
from decimal import Decimal

# MODELS IMPORTS
from app.models.investment import Investment
from app.models.platform import Platform
from app.models.user import User
from app.models.crypto.crypto_models import CryptoProfile
from app.models.stocks.stock_models import StockProfile
from app.models.fundamentals.fundamental_models import StockFundamentalsCurrent
from app.models.trading.trading_models import Trade, Position

# SERVICES IMPORTS
from app.services.crypto.factory import CryptoServiceFactory

logger = logging.getLogger(__name__)

class PortfolioCRUD:
    def __init__(self, db: Session):
        self.db = db
        self.crypto_service = CryptoServiceFactory.create_crypto_service(db)

    def _get_current_price(self, symbol: str, asset_type: str) -> Optional[float]:
        """Get current price from appropriate API"""
        try:
            if asset_type == 'crypto':
                price_data = self.crypto_service.get_current_price(symbol)
                if price_data and price_data.get('price'):
                    return float(price_data['price'])
                else:
                    # Fallback: check database cache
                    crypto_profile = self.db.query(CryptoProfile).filter(
                        CryptoProfile.symbol == symbol.upper()
                    ).first()
                    return None
                    
            elif asset_type == 'stock':
                # TODO: Integrate with TwelveData API
                # Mock data for now
                mock_prices = {
                    'AAPL': 180.0, 'TSLA': 250.0, 'MSFT': 330.0, 
                    'GOOGL': 140.0, 'AMZN': 150.0, 'META': 320.0
                }
                return mock_prices.get(symbol.upper())
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return None
    
    # INVESTMENT OPERATIONS
    def create_investment(self, user_id: int, symbol: str, asset_type: str, 
                         platform_id: int = None, quantity: float = 0,
                         invested_amount: float = 0, purchase_price: float = 0,
                         currency: str = "USD", notes: str = None) -> Investment:
        """Create a new investment"""
        investment = Investment(
            user_id=user_id,
            symbol=symbol.upper(),
            asset_type=asset_type,
            platform_id=platform_id,
            quantity=quantity,
            invested_amount=invested_amount,
            purchase_price=purchase_price,
            currency=currency,
            notes=notes,
            transaction_date=datetime.now()
        )
        
        self.db.add(investment)
        self.db.commit()
        self.db.refresh(investment)
        return investment
    
    def get_user_investments(self, user_id: int) -> List[Investment]:
        """Get all investments for a user with platform info"""
        return self.db.query(Investment)\
            .options(joinedload(Investment.platform))\
            .filter(Investment.user_id == user_id)\
            .order_by(desc(Investment.created_at))\
            .all()
    
    def get_investment_by_id(self, investment_id: int, user_id: int = None) -> Optional[Investment]:
        """Get specific investment with optional user validation"""
        query = self.db.query(Investment)\
            .options(joinedload(Investment.platform))\
            .filter(Investment.id == investment_id)
        
        if user_id:
            query = query.filter(Investment.user_id == user_id)
            
        return query.first()
    
    def update_investment(self, investment_id: int, user_id: int, **kwargs) -> Optional[Investment]:
        """Update investment details"""
        investment = self.get_investment_by_id(investment_id, user_id)
        if investment:
            for key, value in kwargs.items():
                if hasattr(investment, key) and key not in ['id', 'user_id', 'created_at']:
                    setattr(investment, key, value)
            investment.updated_at = datetime.now()
            self.db.commit()
            self.db.refresh(investment)
        return investment
    
    def delete_investment(self, investment_id: int, user_id: int) -> bool:
        """Delete an investment"""
        investment = self.get_investment_by_id(investment_id, user_id)
        if investment:
            self.db.delete(investment)
            self.db.commit()
            return True
        return False
    
    # PORTFOLIO SUMMARY OPERATIONS
    def get_portfolio_summary(self, user_id: int) -> Dict[str, Any]:
        """Get complete portfolio summary with ROI calculations"""
        try:
            investments = self.get_user_investments(user_id)
            
            total_invested = 0.0
            total_current_value = 0.0
            investments_data = []
            
            for investment in investments:
                # Calculate current value and ROI
                current_price = self._get_current_price(investment.symbol, investment.asset_type)
                current_value = float(investment.quantity) * current_price if current_price else 0.0
                invested = float(investment.invested_amount) if investment.invested_amount else 0.0
                
                # Calculate ROI
                roi = ((current_value - invested) / invested * 100) if invested > 0 else 0.0
                profit_loss = current_value - invested
                
                # Get asset profile for category information
                asset_profile = self._get_asset_profile(investment.symbol, investment.asset_type)
                
                total_invested += invested
                total_current_value += current_value
                
                investments_data.append({
                    'id': investment.id,
                    'symbol': investment.symbol,
                    'asset_name': investment.asset_name,
                    'asset_type': investment.asset_type,
                    'quantity': float(investment.quantity),
                    'invested_amount': invested,
                    'purchase_price': float(investment.purchase_price) if investment.purchase_price else 0.0,
                    'current_price': current_price,
                    'current_value': current_value,
                    'roi': roi,
                    'profit_loss': profit_loss,
                    'platform': investment.platform.display_name if investment.platform else 'Unknown',
                    'category': asset_profile.get('sector') or asset_profile.get('categories', [])[0] if asset_profile.get('categories') else 'Unknown',
                    'currency': investment.currency,
                    'transaction_date': investment.transaction_date
                })
            
            # Calculate totals
            total_profit_loss = total_current_value - total_invested
            total_roi = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0.0
            
            return {
                'total_invested': total_invested,
                'total_current_value': total_current_value,
                'total_roi': total_roi,
                'total_profit_loss': total_profit_loss,
                'investments': investments_data,
                'investment_count': len(investments),
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary for user {user_id}: {str(e)}")
            return {
                'total_invested': 0,
                'total_current_value': 0,
                'total_roi': 0,
                'total_profit_loss': 0,
                'investments': [],
                'investment_count': 0,
                'last_updated': datetime.now()
            }
    
    def get_investment_detail(self, investment_id: int, user_id: int) -> Dict[str, Any]:
        """Get detailed investment information for modal view"""
        investment = self.get_investment_by_id(investment_id, user_id)
        if not investment:
            return None
        
        # Get current price and market data
        current_price = self._get_current_price(investment.symbol, investment.asset_type)
        current_value = float(investment.quantity) * current_price if current_price else 0
        invested = float(investment.invested_amount) if investment.invested_amount else 0
        roi = ((current_value - invested) / invested * 100) if invested > 0 else 0
        
        # Get asset profile information
        asset_profile = self._get_asset_profile(investment.symbol, investment.asset_type)
        
        # Get related news
        related_news = self._get_related_news(investment.symbol, investment.asset_type)
        
        # Get market data
        market_data = self._get_market_data(investment.symbol, investment.asset_type)
        
        return {
            'investment': investment,
            'current_price': current_price,
            'current_value': current_value,
            'roi': roi,
            'profit_loss': current_value - invested,
            'asset_profile': asset_profile,
            'market_data': market_data,
            'related_news': related_news
        }
    
    def get_investment_cards_data(self, user_id: int) -> List[Dict[str, Any]]:
        """Get formatted data specifically for investment cards in frontend"""
        portfolio_summary = self.get_portfolio_summary(user_id)
        return portfolio_summary.get('investments', [])
    
    def get_investment_modal_data(self, investment_id: int, user_id: int) -> Dict[str, Any]:
        """Get detailed data for investment modal"""
        return self.get_investment_detail(investment_id, user_id)
    
    # TRANSACTION OPERATIONS
    def add_transaction(self, investment_id: int, transaction_type: str, 
                       quantity: float, price: float, fees: float = 0,
                       platform_id: int = None, notes: str = None) -> Trade:
        """Add a transaction (buy/sell) and update investment totals"""
        
        total_amount = quantity * price
        
        transaction = Trade(
            investment_id=investment_id,
            symbol="",  # Will be set from investment
            asset_type="",  # Will be set from investment
            position_type='long',  # Default
            trade_action=transaction_type,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            fees=fees,
            platform=platform_id,
            reason=notes,
            trade_date=datetime.now()
        )
        
        # Update investment totals
        investment = self.get_investment_by_id(investment_id)
        if investment:
            transaction.symbol = investment.symbol
            transaction.asset_type = investment.asset_type
            
            if transaction_type == 'buy':
                new_quantity = float(investment.quantity) + quantity
                new_invested = float(investment.invested_amount) + total_amount
                new_avg_price = new_invested / new_quantity if new_quantity > 0 else 0
                
                investment.quantity = new_quantity
                investment.invested_amount = new_invested
                investment.purchase_price = new_avg_price
                
            elif transaction_type == 'sell':
                new_quantity = float(investment.quantity) - quantity
                # Reduce invested amount proportionally
                sell_ratio = quantity / float(investment.quantity) if float(investment.quantity) > 0 else 0
                new_invested = float(investment.invested_amount) * (1 - sell_ratio)
                
                investment.quantity = new_quantity
                investment.invested_amount = new_invested
                investment.purchase_price = new_invested / new_quantity if new_quantity > 0 else 0
            
            investment.updated_at = datetime.now()
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    def get_investment_transactions(self, investment_id: int, user_id: int = None) -> List[Trade]:
        """Get all transactions for an investment"""
        query = self.db.query(Trade)\
            .filter(Trade.investment_id == investment_id)\
            .order_by(desc(Trade.trade_date))
        
        if user_id:
            # Verify investment belongs to user
            investment = self.get_investment_by_id(investment_id, user_id)
            if not investment:
                return []
        
        return query.all()
    
    # PRICE AND MARKET DATA INTEGRATION
    def _get_asset_profile(self, symbol: str, asset_type: str) -> Dict[str, Any]:
        """Get asset profile information from database or API"""
        try:
            if asset_type == 'crypto':
                # First try from database
                profile = self.db.query(CryptoProfile).filter(
                    CryptoProfile.symbol == symbol.upper()
                ).first()
                
                if profile:
                    return {
                        'name': profile.name,
                        'description': profile.description_es or profile.description_en,
                        'website': profile.website,
                        'categories': profile.categories or [],
                        'market_cap_rank': profile.market_cap_rank,
                        'logo_url': profile.logo_url,
                        'source': 'database'
                    }
                else:
                    # If not in database, get from API
                    api_profile = self.crypto_service.get_coin_profile(symbol)
                    if api_profile:
                        return {
                            'name': api_profile.get('name'),
                            'description': api_profile.get('description'),
                            'website': api_profile.get('website'),
                            'categories': api_profile.get('categories', []),
                            'market_cap_rank': api_profile.get('market_cap_rank'),
                            'logo_url': api_profile.get('logo_url'),
                            'source': 'api'
                        }
                        
            elif asset_type == 'stock':
                profile = self.db.query(StockProfile).filter(
                    StockProfile.symbol == symbol.upper()
                ).first()
                if profile:
                    return {
                        'name': profile.company_name,
                        'description': profile.description,
                        'sector': profile.sector,
                        'industry': profile.industry,
                        'website': profile.website,
                        'country': profile.country,
                        'ipo_date': profile.ipo_date,
                        'employees': profile.employees,
                        'source': 'database'
                    }
                    
            return {}
            
        except Exception as e:
            logger.error(f"Error getting asset profile for {symbol}: {str(e)}")
            return {}
    
    def _get_market_data(self, symbol: str, asset_type: str) -> Dict[str, Any]:
        """Get market data like market cap, volume, etc."""
        try:
            if asset_type == 'crypto':
                # Use crypto service for market data
                market_data = self.crypto_service.get_detailed_market_data(symbol)
                if market_data:
                    return {
                        'market_cap': market_data.get('market_cap'),
                        'volume_24h': market_data.get('total_volume'),
                        'price_change_24h': market_data.get('price_change_24h'),
                        'price_change_percentage_24h': market_data.get('price_change_percentage_24h'),
                        'price_change_percentage_7d': market_data.get('price_change_percentage_7d'),
                        'circulating_supply': market_data.get('circulating_supply'),
                        'total_supply': market_data.get('total_supply'),
                        'max_supply': market_data.get('max_supply'),
                        'ath': market_data.get('ath'),
                        'atl': market_data.get('atl'),
                        'source': 'coingecko'
                    }
                    
            elif asset_type == 'stock':
                fundamentals = self.db.query(StockFundamentalsCurrent).filter(
                    StockFundamentalsCurrent.symbol == symbol.upper()
                ).first()
                if fundamentals:
                    return {
                        'market_cap': fundamentals.market_cap,
                        'pe_ratio': fundamentals.pe_ratio,
                        'eps': fundamentals.eps,
                        'dividend_yield': fundamentals.dividend_yield,
                        'year_high': fundamentals.year_high,
                        'year_low': fundamentals.year_low,
                        'volume_avg': fundamentals.volume_avg,
                        'source': 'database'
                    }
        
            return {}
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {str(e)}")
            return {}
    
    def _get_related_news(self, symbol: str, asset_type: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get related news - placeholder for FinnHub integration"""
        # TODO: Integrate with FinnHub News API
        try:
            # Mock data for now
            mock_news = [
                {
                    'title': f'Market Update: {symbol} shows strong performance',
                    'summary': f'Recent market analysis indicates positive trends for {symbol}.',
                    'source': 'Financial News',
                    'published_at': datetime.now() - timedelta(hours=2),
                    'url': '#',
                    'sentiment': 'positive'
                },
                {
                    'title': f'{symbol} Technical Analysis',
                    'summary': f'Technical indicators suggest potential growth opportunities for {symbol}.',
                    'source': 'Market Analysis',
                    'published_at': datetime.now() - timedelta(days=1),
                    'url': '#',
                    'sentiment': 'neutral'
                }
            ]
            return mock_news[:limit]
            
        except Exception as e:
            logger.error(f"Error getting news for {symbol}: {str(e)}")
            return []
    
    # PORTFOLIO ANALYTICS
    def get_portfolio_allocations(self, user_id: int) -> Dict[str, Any]:
        """Get portfolio allocations by asset type and category"""
        investments = self.get_user_investments(user_id)
        summary = self.get_portfolio_summary(user_id)
        
        allocations = {
            'by_asset_type': {},
            'by_category': {},
            'by_platform': {}
        }
        
        for inv_data in summary['investments']:
            investment = inv_data['investment']
            current_value = inv_data['current_value']
            
            # By asset type
            asset_type = investment.asset_type
            allocations['by_asset_type'][asset_type] = \
                allocations['by_asset_type'].get(asset_type, 0) + current_value
            
            # By platform
            platform_name = investment.platform.display_name if investment.platform else 'Unknown'
            allocations['by_platform'][platform_name] = \
                allocations['by_platform'].get(platform_name, 0) + current_value
        
        # Convert to percentages
        total_value = summary['total_current_value']
        if total_value > 0:
            for key in ['by_asset_type', 'by_platform']:
                for subkey in allocations[key]:
                    allocations[key][subkey] = (allocations[key][subkey] / total_value) * 100
        
        return allocations
    
    def get_performance_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get portfolio performance metrics"""
        summary = self.get_portfolio_summary(user_id)
        allocations = self.get_portfolio_allocations(user_id)
        
        return {
            'total_roi': summary['total_roi'],
            'total_profit_loss': summary['total_profit_loss'],
            'total_invested': summary['total_invested'],
            'total_current_value': summary['total_current_value'],
            'investment_count': summary['investment_count'],
            'allocations': allocations,
            'best_performer': self._get_best_performer(user_id),
            'worst_performer': self._get_worst_performer(user_id)
        }
    
    def _get_best_performer(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get best performing investment"""
        investments = self.get_user_investments(user_id)
        best_roi = -float('inf')
        best_investment = None
        
        for investment in investments:
            current_price = self._get_current_price(investment.symbol, investment.asset_type)
            if current_price and investment.purchase_price:
                roi = (current_price - float(investment.purchase_price)) / float(investment.purchase_price) * 100
                if roi > best_roi:
                    best_roi = roi
                    best_investment = {
                        'investment': investment,
                        'roi': roi,
                        'current_price': current_price
                    }
        
        return best_investment
    
    def _get_worst_performer(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get worst performing investment"""
        investments = self.get_user_investments(user_id)
        worst_roi = float('inf')
        worst_investment = None
        
        for investment in investments:
            current_price = self._get_current_price(investment.symbol, investment.asset_type)
            if current_price and investment.purchase_price:
                roi = (current_price - float(investment.purchase_price)) / float(investment.purchase_price) * 100
                if roi < worst_roi:
                    worst_roi = roi
                    worst_investment = {
                        'investment': investment,
                        'roi': roi,
                        'current_price': current_price
                    }
        
        return worst_investment