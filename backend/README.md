AurumCap Backend

Stack:
Languaje - FastAPI
DB - PostgreSQL

Architecture

App -> Includes all of the AurumCap API, db and integration with therserized APIs

 * db -> Connection to PostgreSQL database
 * integrations -> 
 * models -> Information for differents tables for db
 * providers -> Comunication with therserized APIs (Coinmarketcap, Finnhub, Massive)
 * repositories ->
 * routes -> Endpoints for AurumCap logic that comunicates to get data for therserized APIs (providers)
 * schemas ->
 * services -> Centralize differents services in one file (ej: data for providers by 1 action, with differents paths)
 * worker -> Execute background jobs

 Architecture Map

 Routes -> Services -> Providers -> Externals APIs

 Example:
 Get /price/BTC -> price_service -> coinmarketcap_provider -> Coinmarketcap API

 Background Jobs

 Update the price_history every 5 minutes:
  Architecture:
  FastAPI -> Redis -> Celery Worker -> price ingestion