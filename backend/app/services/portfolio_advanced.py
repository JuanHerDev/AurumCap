import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import math

from app.models.investment import Investment
from app.models.risk_profile import RiskProfile, RiskProfileType
from app.models.investment_goal import InvestmentGoal
from app.models.dividend import Dividend
from app.models.price_alert import PriceAlert
from app.schemas.risk_profile import RiskProfileType as SchemaRiskProfileType

logger = logging.getLogger(__name__)

class PortfolioAdvancedService:
    def __init__(self, db: Session):
        self.db = db
    
    # 1. RISK PROFILE & AUTO-ALLOCATION
    def create_or_update_risk_profile(self, user_id: int, profile_type: SchemaRiskProfileType) -> RiskProfile:
        """Create or update user's risk profile with auto-calculated allocations"""
        
        # Map schema enum to model enum
        profile_type_map = {
            SchemaRiskProfileType.CONSERVATIVE: RiskProfileType.CONSERVATIVE,
            SchemaRiskProfileType.MODERATE: RiskProfileType.MODERATE,
            SchemaRiskProfileType.AGGRESSIVE: RiskProfileType.AGGRESSIVE
        }
        
        model_profile_type = profile_type_map.get(profile_type, RiskProfileType.MODERATE)
        
        # Define allocation templates based on risk profile
        allocation_templates = {
            RiskProfileType.CONSERVATIVE: {
                "crypto": 10.0,
                "stocks": 50.0,
                "bonds": 30.0,
                "cash": 10.0
            },
            RiskProfileType.MODERATE: {
                "crypto": 20.0,
                "stocks": 60.0,
                "bonds": 15.0,
                "cash": 5.0
            },
            RiskProfileType.AGGRESSIVE: {
                "crypto": 40.0,
                "stocks": 50.0,
                "bonds": 5.0,
                "cash": 5.0
            }
        }
        
        # Get or create risk profile
        risk_profile = self.db.query(RiskProfile).filter(
            RiskProfile.user_id == user_id
        ).first()
        
        if risk_profile:
            # Update existing profile
            risk_profile.profile_type = model_profile_type
            risk_profile.target_allocations = allocation_templates[model_profile_type]
            risk_profile.updated_at = datetime.now()
        else:
            # Create new profile
            risk_profile = RiskProfile(
                user_id=user_id,
                profile_type=model_profile_type,
                target_allocations=allocation_templates[model_profile_type]
            )
            self.db.add(risk_profile)
        
        self.db.commit()
        self.db.refresh(risk_profile)
        return risk_profile
    
    def calculate_portfolio_allocation(self, user_id: int) -> Dict[str, float]:
        """Calculate current portfolio allocation vs target"""
        # Get user's investments with current values
        from app.crud.portfolio_crud import PortfolioCRUD
        portfolio_crud = PortfolioCRUD(self.db)
        portfolio_summary = portfolio_crud.get_portfolio_summary(user_id)
        
        if not portfolio_summary or portfolio_summary['total_current_value'] <= 0:
            return {}
        
        # Calculate current allocation by asset type
        current_allocation = {}
        investments = portfolio_summary.get('investments', [])
        
        for inv in investments:
            asset_type = inv.get('asset_type', 'other')
            current_value = inv.get('current_value', 0)
            
            if asset_type not in current_allocation:
                current_allocation[asset_type] = 0
            current_allocation[asset_type] += current_value
        
        # Convert to percentages
        total_value = portfolio_summary['total_current_value']
        current_allocation_pct = {
            asset_type: (value / total_value * 100)
            for asset_type, value in current_allocation.items()
        }
        
        return current_allocation_pct
    
    def get_rebalancing_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Generate rebalancing recommendations based on risk profile"""
        # Get risk profile
        risk_profile = self.db.query(RiskProfile).filter(
            RiskProfile.user_id == user_id
        ).first()
        
        if not risk_profile:
            return {"error": "No risk profile found"}
        
        # Get current allocation
        current_allocation = self.calculate_portfolio_allocation(user_id)
        target_allocation = risk_profile.target_allocations
        
        # Calculate deviations
        deviations = {}
        rebalancing_needed = False
        
        for asset_type, target_pct in target_allocation.items():
            current_pct = current_allocation.get(asset_type, 0)
            deviation = current_pct - target_pct
            deviations[asset_type] = {
                "current": current_pct,
                "target": target_pct,
                "deviation": deviation,
                "deviation_absolute": abs(deviation)
            }
            
            if abs(deviation) > risk_profile.rebalance_threshold:
                rebalancing_needed = True
        
        # Generate recommendations
        recommendations = []
        if rebalancing_needed:
            # Calculate total portfolio value
            from app.crud.portfolio_crud import PortfolioCRUD
            portfolio_crud = PortfolioCRUD(self.db)
            portfolio_summary = portfolio_crud.get_portfolio_summary(user_id)
            total_value = portfolio_summary['total_current_value']
            
            for asset_type, data in deviations.items():
                deviation = data["deviation"]
                if abs(deviation) > risk_profile.rebalance_threshold:
                    adjustment_needed = (deviation / 100) * total_value
                    
                    if deviation > 0:
                        # Overweight - should sell
                        action = "SELL"
                        amount = abs(adjustment_needed)
                        recommendation = f"Reduce {asset_type} exposure by ${amount:,.2f} (sell)"
                    else:
                        # Underweight - should buy
                        action = "BUY"
                        amount = abs(adjustment_needed)
                        recommendation = f"Increase {asset_type} exposure by ${amount:,.2f} (buy)"
                    
                    recommendations.append({
                        "asset_type": asset_type,
                        "action": action,
                        "amount": amount,
                        "current_pct": data["current"],
                        "target_pct": data["target"],
                        "deviation": deviation,
                        "recommendation": recommendation
                    })
        
        return {
            "rebalancing_needed": rebalancing_needed,
            "threshold": risk_profile.rebalance_threshold,
            "deviations": deviations,
            "recommendations": recommendations,
            "last_rebalanced": risk_profile.last_rebalanced
        }
    
    # 2. SELL CALCULATOR (Sell Only Profits)
    def calculate_sell_profits_only(
        self, 
        user_id: int, 
        investment_id: int, 
        target_amount: float,
        current_price: float
    ) -> Dict[str, Any]:
        """Calculate how much to sell to realize only profits"""
        
        # Get investment details
        investment = self.db.query(Investment).filter(
            and_(
                Investment.id == investment_id,
                Investment.user_id == user_id
            )
        ).first()
        
        if not investment:
            return {"error": "Investment not found"}
        
        # Calculate profit per share
        purchase_price = float(investment.purchase_price) if investment.purchase_price else 0
        profit_per_share = current_price - purchase_price
        
        if profit_per_share <= 0:
            return {
                "error": "No profits available",
                "current_price": current_price,
                "purchase_price": purchase_price,
                "profit_per_share": profit_per_share
            }
        
        # Calculate shares needed to sell to get target amount from profits only
        shares_to_sell = target_amount / profit_per_share
        
        # Ensure we don't sell more than we own
        max_shares = float(investment.quantity)
        if shares_to_sell > max_shares:
            shares_to_sell = max_shares
            actual_amount = shares_to_sell * profit_per_share
        else:
            actual_amount = target_amount
        
        # Calculate percentages
        portfolio_percentage = (shares_to_sell / max_shares) * 100
        profit_percentage = (profit_per_share / purchase_price) * 100 if purchase_price > 0 else 0
        
        return {
            "investment_id": investment_id,
            "symbol": investment.symbol,
            "current_price": current_price,
            "purchase_price": purchase_price,
            "profit_per_share": profit_per_share,
            "profit_percentage": profit_percentage,
            "shares_to_sell": shares_to_sell,
            "amount_from_profits": actual_amount,
            "portfolio_percentage": portfolio_percentage,
            "remaining_shares": max_shares - shares_to_sell,
            "total_profit_realized": shares_to_sell * profit_per_share,
            "remaining_cost_basis": (max_shares - shares_to_sell) * purchase_price
        }
    
    def calculate_sell_percentage(
        self,
        user_id: int,
        investment_id: int,
        sell_percentage: float,
        current_price: float
    ) -> Dict[str, Any]:
        """Calculate sell details for a percentage of holdings"""
        
        if not 0 < sell_percentage <= 100:
            return {"error": "Percentage must be between 0 and 100"}
        
        # Get investment details
        investment = self.db.query(Investment).filter(
            and_(
                Investment.id == investment_id,
                Investment.user_id == user_id
            )
        ).first()
        
        if not investment:
            return {"error": "Investment not found"}
        
        # Calculate quantities
        total_shares = float(investment.quantity)
        shares_to_sell = total_shares * (sell_percentage / 100)
        purchase_price = float(investment.purchase_price) if investment.purchase_price else 0
        
        # Calculate profit/loss
        cost_basis = shares_to_sell * purchase_price
        sale_value = shares_to_sell * current_price
        profit_loss = sale_value - cost_basis
        profit_percentage = (profit_loss / cost_basis * 100) if cost_basis > 0 else 0
        
        return {
            "investment_id": investment_id,
            "symbol": investment.symbol,
            "sell_percentage": sell_percentage,
            "shares_to_sell": shares_to_sell,
            "current_price": current_price,
            "purchase_price": purchase_price,
            "cost_basis": cost_basis,
            "sale_value": sale_value,
            "profit_loss": profit_loss,
            "profit_percentage": profit_percentage,
            "remaining_shares": total_shares - shares_to_sell,
            "tax_implications": self._estimate_tax_implications(profit_loss)
        }
    
    def _estimate_tax_implications(self, profit_loss: float) -> Dict[str, Any]:
        """Estimate tax implications (simplified)"""
        # This is a simplified version - in production, you'd need
        # much more complex tax logic based on jurisdiction
        if profit_loss <= 0:
            return {
                "taxable_gain": 0,
                "tax_loss": abs(profit_loss),
                "can_offset": True
            }
        
        # Simplified tax rates (for demonstration)
        SHORT_TERM_RATE = 0.37  # Assume short-term (held < 1 year)
        LONG_TERM_RATE = 0.20   # Assume long-term (held > 1 year)
        
        # For demo, assume all are long-term
        tax_amount = profit_loss * LONG_TERM_RATE
        net_profit = profit_loss - tax_amount
        
        return {
            "taxable_gain": profit_loss,
            "tax_rate": LONG_TERM_RATE,
            "tax_amount": tax_amount,
            "net_profit": net_profit,
            "effective_tax_rate": (tax_amount / profit_loss) if profit_loss > 0 else 0
        }
    
    # 3. DIVIDEND TRACKING
    def record_dividend(
        self,
        user_id: int,
        investment_id: int,
        amount_per_share: float,
        total_shares: float,
        payment_date: datetime,
        ex_dividend_date: datetime,
        **kwargs
    ) -> Dividend:
        """Record a dividend payment"""
        
        # Calculate totals
        total_amount = amount_per_share * total_shares
        tax_withheld = kwargs.get('tax_withheld', 0.0)
        tax_rate = kwargs.get('tax_rate', 0.0)
        net_amount = total_amount - tax_withheld
        
        dividend = Dividend(
            user_id=user_id,
            investment_id=investment_id,
            amount_per_share=amount_per_share,
            total_shares=total_shares,
            total_amount=total_amount,
            currency=kwargs.get('currency', 'USD'),
            payment_date=payment_date,
            ex_dividend_date=ex_dividend_date,
            record_date=kwargs.get('record_date'),
            declared_date=kwargs.get('declared_date'),
            tax_withheld=tax_withheld,
            tax_rate=tax_rate,
            net_amount=net_amount,
            reinvested=kwargs.get('reinvested', False),
            payment_method=kwargs.get('payment_method', 'cash'),
            paid=kwargs.get('paid', True),
            source=kwargs.get('source', 'manual'),
            notes=kwargs.get('notes')
        )
        
        self.db.add(dividend)
        self.db.commit()
        self.db.refresh(dividend)
        
        # Update investment goal if applicable
        self._update_goals_from_dividend(user_id, dividend)
        
        return dividend
    
    def _update_goals_from_dividend(self, user_id: int, dividend: Dividend):
        """Update investment goals when dividends are received"""
        # Find active goals for this user
        goals = self.db.query(InvestmentGoal).filter(
            and_(
                InvestmentGoal.user_id == user_id,
                InvestmentGoal.is_active == True,
                InvestmentGoal.achieved == False
            )
        ).all()
        
        for goal in goals:
            # Add dividend to goal's current amount if it's cash (not reinvested)
            if not dividend.reinvested:
                goal.current_amount += dividend.net_amount
                goal.progress_percentage = (goal.current_amount / goal.target_amount) * 100
                
                # Check if goal is achieved
                if goal.current_amount >= goal.target_amount:
                    goal.achieved = True
                    goal.achievement_date = datetime.now()
                    goal.is_active = False
        
        if goals:
            self.db.commit()
    
    def get_dividend_summary(self, user_id: int, year: int = None) -> Dict[str, Any]:
        """Get dividend summary for a user"""
        
        query = self.db.query(Dividend).filter(
            Dividend.user_id == user_id,
            Dividend.paid == True
        )
        
        if year:
            query = query.filter(
                func.extract('year', Dividend.payment_date) == year
            )
        
        dividends = query.order_by(Dividend.payment_date.desc()).all()
        
        if not dividends:
            return {
                "total_dividends": 0,
                "total_tax_withheld": 0,
                "net_received": 0,
                "dividend_count": 0,
                "by_investment": {},
                "by_month": {}
            }
        
        # Calculate totals
        total_dividends = sum(d.total_amount for d in dividends)
        total_tax_withheld = sum(d.tax_withheld for d in dividends)
        net_received = sum(d.net_amount for d in dividends)
        
        # Group by investment
        by_investment = {}
        for dividend in dividends:
            inv_key = f"{dividend.investment_id}"
            if inv_key not in by_investment:
                by_investment[inv_key] = {
                    "total": 0,
                    "count": 0,
                    "dividends": []
                }
            by_investment[inv_key]["total"] += dividend.net_amount
            by_investment[inv_key]["count"] += 1
            by_investment[inv_key]["dividends"].append({
                "date": dividend.payment_date,
                "amount": dividend.net_amount,
                "reinvested": dividend.reinvested
            })
        
        # Group by month
        by_month = {}
        for dividend in dividends:
            month_key = dividend.payment_date.strftime("%Y-%m")
            if month_key not in by_month:
                by_month[month_key] = 0
            by_month[month_key] += dividend.net_amount
        
        return {
            "total_dividends": total_dividends,
            "total_tax_withheld": total_tax_withheld,
            "net_received": net_received,
            "dividend_count": len(dividends),
            "average_per_dividend": net_received / len(dividends) if dividends else 0,
            "by_investment": by_investment,
            "by_month": by_month,
            "reinvested_count": sum(1 for d in dividends if d.reinvested),
            "cash_dividends": sum(d.net_amount for d in dividends if not d.reinvested)
        }
    
    # 4. INVESTMENT GOALS
    def create_investment_goal(
        self,
        user_id: int,
        name: str,
        target_amount: float,
        target_date: datetime,
        **kwargs
    ) -> InvestmentGoal:
        """Create a new investment goal"""
        
        # Calculate months remaining
        months_remaining = self._calculate_months_remaining(target_date)
        
        goal = InvestmentGoal(
            user_id=user_id,
            name=name,
            description=kwargs.get('description'),
            target_amount=target_amount,
            current_amount=kwargs.get('initial_investment', 0.0),
            target_date=target_date,
            monthly_contribution=kwargs.get('monthly_contribution', 0.0),
            initial_investment=kwargs.get('initial_investment', 0.0),
            risk_profile=kwargs.get('risk_profile', SchemaRiskProfileType.MODERATE),
            is_active=True,
            achieved=False,
            progress_percentage=(kwargs.get('initial_investment', 0.0) / target_amount) * 100,
            months_remaining=months_remaining
        )
        
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        
        return goal
    
    def _calculate_months_remaining(self, target_date: datetime) -> int:
        """Calculate months between now and target date"""
        now = datetime.now()
        if target_date <= now:
            return 0
        
        # Calculate full months remaining
        months = (target_date.year - now.year) * 12 + (target_date.month - now.month)
        
        # Adjust for days
        if target_date.day < now.day:
            months -= 1
        
        return max(0, months)
    
    def update_goal_progress(self, user_id: int, goal_id: int, additional_amount: float = 0) -> InvestmentGoal:
        """Update goal progress with additional contribution"""
        
        goal = self.db.query(InvestmentGoal).filter(
            and_(
                InvestmentGoal.id == goal_id,
                InvestmentGoal.user_id == user_id
            )
        ).first()
        
        if not goal:
            raise ValueError("Goal not found")
        
        # Update current amount
        goal.current_amount += additional_amount
        
        # Update progress percentage
        goal.progress_percentage = (goal.current_amount / goal.target_amount) * 100
        
        # Update months remaining
        goal.months_remaining = self._calculate_months_remaining(goal.target_date)
        
        # Check if achieved
        if goal.current_amount >= goal.target_amount and not goal.achieved:
            goal.achieved = True
            goal.achievement_date = datetime.now()
            goal.is_active = False
        
        goal.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(goal)
        
        return goal
    
    def get_goal_projection(self, goal_id: int, user_id: int) -> Dict[str, Any]:
        """Project future value of investment goal"""
        
        goal = self.db.query(InvestmentGoal).filter(
            and_(
                InvestmentGoal.id == goal_id,
                InvestmentGoal.user_id == user_id
            )
        ).first()
        
        if not goal:
            return {"error": "Goal not found"}
        
        # Get risk-adjusted expected return
        expected_returns = {
            SchemaRiskProfileType.CONSERVATIVE: 0.05,  # 5% annual
            SchemaRiskProfileType.MODERATE: 0.07,      # 7% annual
            SchemaRiskProfileType.AGGRESSIVE: 0.10     # 10% annual
        }
        
        annual_return = expected_returns.get(goal.risk_profile, 0.07)
        monthly_return = annual_return / 12
        
        # Project future value
        months = goal.months_remaining
        monthly_contribution = goal.monthly_contribution
        current_amount = goal.current_amount
        
        # Future value formula: FV = PV*(1+r)^n + PMT*[((1+r)^n - 1)/r]
        future_value = (
            current_amount * ((1 + monthly_return) ** months) +
            monthly_contribution * (((1 + monthly_return) ** months - 1) / monthly_return)
            if monthly_return > 0 else
            current_amount + (monthly_contribution * months)
        )
        
        # Calculate required monthly contribution to reach goal
        if future_value < goal.target_amount:
            # Calculate required contribution
            required_contribution = (
                (goal.target_amount - current_amount * ((1 + monthly_return) ** months)) *
                monthly_return / ((1 + monthly_return) ** months - 1)
                if monthly_return > 0 else
                (goal.target_amount - current_amount) / months
            )
        else:
            required_contribution = 0
        
        return {
            "goal_id": goal_id,
            "goal_name": goal.name,
            "target_amount": goal.target_amount,
            "current_amount": current_amount,
            "months_remaining": months,
            "monthly_contribution": monthly_contribution,
            "projected_amount": future_value,
            "projected_surplus_deficit": future_value - goal.target_amount,
            "required_monthly_contribution": max(0, required_contribution),
            "progress_percentage": goal.progress_percentage,
            "expected_annual_return": annual_return * 100,
            "on_track": future_value >= goal.target_amount
        }
    
    def check_goals_alerts(self, user_id: int) -> List[Dict[str, Any]]:
        """Check and generate alerts for investment goals"""
        
        goals = self.db.query(InvestmentGoal).filter(
            and_(
                InvestmentGoal.user_id == user_id,
                InvestmentGoal.is_active == True,
                InvestmentGoal.achieved == False
            )
        ).all()
        
        alerts = []
        now = datetime.now()
        
        for goal in goals:
            # Check if goal is at risk
            months_remaining = self._calculate_months_remaining(goal.target_date)
            
            if months_remaining <= 3:
                # Goal is approaching deadline
                alerts.append({
                    "type": "goal_deadline_approaching",
                    "goal_id": goal.id,
                    "goal_name": goal.name,
                    "months_remaining": months_remaining,
                    "message": f"Goal '{goal.name}' deadline is approaching ({months_remaining} months remaining)",
                    "severity": "high"
                })
            
            # Check if contributions are on track
            projection = self.get_goal_projection(goal.id, user_id)
            if not projection.get("on_track", False):
                alerts.append({
                    "type": "goal_off_track",
                    "goal_id": goal.id,
                    "goal_name": goal.name,
                    "required_contribution": projection.get("required_monthly_contribution", 0),
                    "current_contribution": goal.monthly_contribution,
                    "message": f"Goal '{goal.name}' is off track. Consider increasing monthly contribution to ${projection.get('required_monthly_contribution', 0):,.2f}",
                    "severity": "medium"
                })
            
            # Check if goal is 90% complete
            if goal.progress_percentage >= 90:
                alerts.append({
                    "type": "goal_nearly_complete",
                    "goal_id": goal.id,
                    "goal_name": goal.name,
                    "progress": goal.progress_percentage,
                    "message": f"Goal '{goal.name}' is {goal.progress_percentage:.1f}% complete!",
                    "severity": "low"
                })
        
        return alerts
    
    # 5. PORTFOLIO HEALTH SCORE
    def calculate_portfolio_health_score(self, user_id: int) -> Dict[str, Any]:
        """Calculate comprehensive portfolio health score (0-100)"""
        
        scores = {}
        weights = {
            "diversification": 0.30,
            "risk_alignment": 0.25,
            "goal_progress": 0.20,
            "cost_efficiency": 0.15,
            "liquidity": 0.10
        }
        
        # 1. Diversification Score
        diversification_score = self._calculate_diversification_score(user_id)
        scores["diversification"] = diversification_score
        
        # 2. Risk Alignment Score
        risk_alignment_score = self._calculate_risk_alignment_score(user_id)
        scores["risk_alignment"] = risk_alignment_score
        
        # 3. Goal Progress Score
        goal_progress_score = self._calculate_goal_progress_score(user_id)
        scores["goal_progress"] = goal_progress_score
        
        # 4. Cost Efficiency Score (simplified)
        cost_efficiency_score = self._calculate_cost_efficiency_score(user_id)
        scores["cost_efficiency"] = cost_efficiency_score
        
        # 5. Liquidity Score
        liquidity_score = self._calculate_liquidity_score(user_id)
        scores["liquidity"] = liquidity_score
        
        # Calculate weighted total score
        total_score = sum(score * weights[category] 
                         for category, score in scores.items())
        
        # Determine health level
        if total_score >= 80:
            health_level = "excellent"
        elif total_score >= 60:
            health_level = "good"
        elif total_score >= 40:
            health_level = "fair"
        else:
            health_level = "needs_improvement"
        
        # Generate recommendations
        recommendations = self._generate_health_recommendations(scores)
        
        return {
            "total_score": round(total_score, 1),
            "health_level": health_level,
            "category_scores": scores,
            "category_weights": weights,
            "recommendations": recommendations,
            "last_calculated": datetime.now()
        }
    
    def _calculate_diversification_score(self, user_id: int) -> float:
        """Calculate diversification score (0-100)"""
        # Get current allocation
        current_allocation = self.calculate_portfolio_allocation(user_id)
        
        if not current_allocation:
            return 50.0  # Neutral score for empty portfolio
        
        # Score based on:
        # 1. Number of asset classes (max 4)
        num_asset_classes = len(current_allocation)
        asset_class_score = min(25, num_asset_classes * 6.25)  # 0-25 points
        
        # 2. Concentration (Herfindahl-Hirschman Index)
        hhi = sum((pct / 100) ** 2 for pct in current_allocation.values()) * 10000
        # HHI ranges from 0 (perfect diversification) to 10000 (single asset)
        concentration_score = max(0, 25 - (hhi / 400))  # 0-25 points
        
        # 3. International exposure (simplified)
        international_score = 25  # Placeholder
        
        # 4. Sector diversification (simplified)
        sector_score = 25  # Placeholder
        
        return asset_class_score + concentration_score + international_score + sector_score
    
    def _calculate_risk_alignment_score(self, user_id: int) -> float:
        """Calculate how well portfolio aligns with risk profile"""
        risk_profile = self.db.query(RiskProfile).filter(
            RiskProfile.user_id == user_id
        ).first()
        
        if not risk_profile:
            return 50.0
        
        # Get current vs target allocation
        current_allocation = self.calculate_portfolio_allocation(user_id)
        target_allocation = risk_profile.target_allocations
        
        if not current_allocation:
            return 50.0
        
        # Calculate deviation score
        total_deviation = 0
        matched_assets = 0
        
        for asset, target_pct in target_allocation.items():
            current_pct = current_allocation.get(asset, 0)
            deviation = abs(current_pct - target_pct)
            total_deviation += deviation
            
            if deviation <= risk_profile.rebalance_threshold:
                matched_assets += 1
        
        # Calculate scores
        deviation_score = max(0, 100 - total_deviation)  # Lower deviation = higher score
        match_score = (matched_assets / len(target_allocation)) * 100
        
        # Weighted average
        return (deviation_score * 0.6) + (match_score * 0.4)
    
    def _calculate_goal_progress_score(self, user_id: int) -> float:
        """Calculate score based on goal progress"""
        goals = self.db.query(InvestmentGoal).filter(
            and_(
                InvestmentGoal.user_id == user_id,
                InvestmentGoal.is_active == True
            )
        ).all()
        
        if not goals:
            return 75.0  # Neutral score for no goals
        
        total_progress = 0
        for goal in goals:
            total_progress += goal.progress_percentage
        
        average_progress = total_progress / len(goals)
        
        # Convert to score: 0% = 0, 100% = 100
        return min(100, average_progress)
    
    def _calculate_cost_efficiency_score(self, user_id: int) -> float:
        """Calculate cost efficiency score (simplified)"""
        # In production, this would analyze:
        # - Expense ratios
        # - Trading fees
        # - Tax efficiency
        # - Management fees
        
        # Placeholder: assume average score
        return 75.0
    
    def _calculate_liquidity_score(self, user_id: int) -> float:
        """Calculate liquidity score"""
        # In production, this would analyze:
        # - Cash position percentage
        # - Liquid vs illiquid assets
        # - Emergency fund adequacy
        
        # Placeholder
        return 80.0
    
    def _generate_health_recommendations(self, scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on low scores"""
        recommendations = []
        
        if scores.get("diversification", 100) < 60:
            recommendations.append(
                "Consider diversifying across more asset classes to reduce risk"
            )
        
        if scores.get("risk_alignment", 100) < 60:
            recommendations.append(
                "Rebalance portfolio to better align with your risk profile"
            )
        
        if scores.get("goal_progress", 100) < 50:
            recommendations.append(
                "Increase contributions to stay on track with your investment goals"
            )
        
        if scores.get("cost_efficiency", 100) < 60:
            recommendations.append(
                "Review investment costs and consider lower-fee alternatives"
            )
        
        if scores.get("liquidity", 100) < 50:
            recommendations.append(
                "Maintain adequate cash reserves for emergencies and opportunities"
            )
        
        return recommendations