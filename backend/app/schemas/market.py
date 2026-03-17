from pydantic import BaseModel


class MarketStatusResponse(BaseModel):
    status: str         # "open" | "extended-hours" | "closed" | "unknown"
    description: str    # "Market is open", "After hours", etc.