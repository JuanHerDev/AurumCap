from app.providers.coinmarketcap_provider import get_crypto_price
from app.providers.massive_provider import get_stock_price

def get_price(asset):

    if asset.asset_type == "crypto":

        return get_crypto_price(asset.symbol)
    
    if asset.asset_type in ["stock", "etf"]:

        return get_stock_price(asset.symbol)
    
    return None