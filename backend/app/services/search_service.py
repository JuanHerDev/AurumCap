from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.asset import Asset
from app.providers.massive_provider import massive_provider
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.schemas.search import SearchResponse, SearchResultItem
from app.core.cache import cache_get, cache_set, key_search, TTL_SEARCH


async def search_assets(query: str, db: AsyncSession, limit: int = 10) -> SearchResponse:
    query_clean = query.strip()

    if not query_clean:
        return SearchResponse(query=query, results=[], total=0)

    # 1. Check cache — search results are stable for 5 minutes
    cached = await cache_get(key_search(query_clean, limit))
    if cached:
        return SearchResponse(**cached)

    # 2. Search in our own database first
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

    # 3. If sufficient results exist in DB, return them directly
    if len(db_assets) >= limit:
        response = SearchResponse(
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
        await cache_set(key_search(query_clean, limit), response.model_dump(), TTL_SEARCH)
        return response

    # 4. Complement with external providers if DB results are insufficient
    db_symbols = {a.symbol for a in db_assets}
    external_results = []

    # Search stocks/ETFs in Massive
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

    # Search crypto in CoinMarketCap
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

    # 5. Combine DB + external results and apply limit
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

    response = SearchResponse(
        query=query,
        results=all_results,
        total=len(all_results),
    )

    # 6. Store in cache for TTL_SEARCH seconds (5 min)
    await cache_set(key_search(query_clean, limit), response.model_dump(), TTL_SEARCH)

    return response