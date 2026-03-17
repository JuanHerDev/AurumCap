from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.asset import Asset
from app.providers.massive_provider import massive_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.search import SearchResponse, SearchResultItem


async def search_assets(query: str, db: AsyncSession, limit: int = 10) -> SearchResponse:
    query_clean = query.strip()

    if not query_clean:
        return SearchResponse(query=query, results=[], total=0)

    # First, search in our own database for matches
    result = await db.execute(
        select(Asset)
        .where(
            or_(
                Asset.symbol.ilike(f"%{query_clean}%"),
                Asset.name.ilike(f"%{query_clean}%"),
            )
        )
        .limit(limit)
    )
    db_assets = result.scalars().all()

    # Second, if there are sufficient results in the database, return them directly
    if len(db_assets) >= limit:
        return SearchResponse(
            query=query,
            results=[
                SearchResultItem(
                    symbol=a.symbol,
                    name=a.name,
                    asset_type=a.asset_type,
                    exchange=a.exchange,
                )
                for a in db_assets
            ],
            total=len(db_assets),
        )

    # Third, if there are few results in the database, complement with external providers
    db_symbols = {a.symbol for a in db_assets}
    external_results = []

    # Search for stocks/ETFs in Massive
    massive_results = await massive_provider.search_assets(query_clean, limit)
    for item in massive_results:
        if item.symbol not in db_symbols:
            external_results.append(SearchResultItem(
                symbol=item.symbol,
                name=item.name,
                asset_type=item.asset_type,
                exchange=item.exchange,
            ))
            db_symbols.add(item.symbol)

    # Search for crypto in CoinMarketCap
    cmc_results = await coinmarketcap_provider.search_assets(query_clean, limit)
    for item in cmc_results:
        if item.symbol not in db_symbols:
            external_results.append(SearchResultItem(
                symbol=item.symbol,
                name=item.name,
                asset_type="crypto",
                rank=item.rank,
            ))
            db_symbols.add(item.symbol)

    # Fourth, combine DB + external results and limit
    all_results = [
        SearchResultItem(
            symbol=a.symbol,
            name=a.name,
            asset_type=a.asset_type,
            exchange=a.exchange,
        )
        for a in db_assets
    ] + external_results

    all_results = all_results[:limit]

    return SearchResponse(
        query=query,
        results=all_results,
        total=len(all_results),
    )