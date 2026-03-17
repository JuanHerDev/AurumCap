from app.services.price_service import get_price
from app.models.asset import Asset
from app.models.price_history import PriceHistory

def update_prices(db):

    assets = db.query(Asset).all()

    for asset in assets:

        price = get_price(asset)

        price_row = PriceHistory(
            asset_id = asset.id,
            price = price
        )

        db.add(price_row)

    db.commit()