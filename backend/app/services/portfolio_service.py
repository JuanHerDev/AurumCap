from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.asset import Asset

def calculate_portfolio(db: Session, user_id: int):

    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .all()
    )

    holdings = defaultdict(lambda: {
        "quantity": 0,
        "total_cost": 0
    })

    for tx in transactions:

        asset_id = tx.asset_id

        if tx.type == "BUY":

            holdings[asset_id]["quantity"] += tx.quantity
            holdings[asset_id]["total_cost"] += tx.quantity * tx.price

        elif tx.type == "SELL":

            holdings[asset_id]["quantity"] -= tx.quantity

    result = []

    for asset_id, data in holdings.items():

        quantity = data["quantity"]

        if quantity <= 0:
            continue

        avg_price = data["total_cost"] / quantity

        asset = db.query(Asset).filter(Asset.id == asset.id).first()

        result.append({
            "asset": asset.symbol,
            "quantity": quantity,
            "avg_price": avg_price
        })

    return result