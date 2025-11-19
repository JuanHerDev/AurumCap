export type AssetType = "crypto" | "stock" | "fixed" | "real_state" | "other";

export interface InvestmentItem {
    symbol: string;
    asset_name: string;
    asset_type: AssetType;
    quantity: number;
    current_price: number;
    current_value: number;
    fundamentals?: Record<string, any>;
}

export interface PortfolioSummary {
    total_invested: number;
    current_value: number;
    gain_loss: number;
    roi: number;
    items: InvestmentItem[];
}