from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.settings import settings
from app.db.init_db import init_db
from app.db.session import engine
from app.routes import portfolio, price, search, fundamentals, market, auth
from app.providers.coinmarketcap_provider import coinmarketcap_provider
from app.providers.finnhub_provider import finnhub_provider

import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # TODO: await init_redis() with caché
    yield

    # Shutdown
    await coinmarketcap_provider.close()
    finnhub_provider._client.close()
    await engine.dispose() 
    # TODO: await close_redis() with caché


app = FastAPI(
    title = "AurumCap API",
    description = "RESTful API for managing cryptocurrency and stock investment portfolios",
    version = "1.0.0",
    debug = settings.DEBUG,
    lifespan=lifespan,
)

@app.get("/")
def root():
    return {"message" : "AurumCap API running"}

app.include_router(portfolio.router)
app.include_router(price.router)
app.include_router(search.router)
app.include_router(fundamentals.router)
app.include_router(market.router)
app.include_router(auth.router)



if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=settings.DEBUG)