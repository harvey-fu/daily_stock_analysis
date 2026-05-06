# -*- coding: utf-8 -*-
"""Portfolio API schemas."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PortfolioAccountCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    broker: Optional[str] = Field(None, max_length=64)
    market: Literal["cn", "hk", "us"] = "cn"
    base_currency: str = Field("CNY", min_length=3, max_length=8)
    owner_id: Optional[str] = Field(None, max_length=64)
    # 2026-05-06: 融资融券账户支持
    account_type: Literal["cash", "margin"] = "cash"
    margin_interest_rate: Optional[float] = Field(None, ge=0, description="融资年利率，如0.08表示8%")
    securities_interest_rate: Optional[float] = Field(None, ge=0, description="融券年利率")
    margin_ratio: Optional[float] = Field(None, ge=0, le=1, description="保证金比例，如0.5表示50%")


class PortfolioAccountUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    broker: Optional[str] = Field(None, max_length=64)
    market: Optional[Literal["cn", "hk", "us"]] = None
    base_currency: Optional[str] = Field(None, min_length=3, max_length=8)
    owner_id: Optional[str] = Field(None, max_length=64)
    is_active: Optional[bool] = None


class PortfolioAccountItem(BaseModel):
    id: int
    owner_id: Optional[str] = None
    name: str
    broker: Optional[str] = None
    market: str
    base_currency: str
    is_active: bool
    # 2026-05-06: 融资融券账户字段
    account_type: str = "cash"
    margin_interest_rate: Optional[float] = None
    securities_interest_rate: Optional[float] = None
    margin_ratio: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class PortfolioAccountListResponse(BaseModel):
    accounts: List[PortfolioAccountItem] = Field(default_factory=list)


class PortfolioTradeCreateRequest(BaseModel):
    account_id: int
    symbol: str = Field(..., min_length=1, max_length=16)
    trade_date: date
    side: Literal["buy", "sell"]
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    fee: float = Field(0.0, ge=0)
    tax: float = Field(0.0, ge=0)
    market: Optional[Literal["cn", "hk", "us"]] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=8)
    trade_uid: Optional[str] = Field(None, max_length=128)
    note: Optional[str] = Field(None, max_length=255)


class PortfolioCashLedgerCreateRequest(BaseModel):
    account_id: int
    event_date: date
    direction: Literal["in", "out"]
    amount: float = Field(..., gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=8)
    note: Optional[str] = Field(None, max_length=255)


class PortfolioCorporateActionCreateRequest(BaseModel):
    account_id: int
    symbol: str = Field(..., min_length=1, max_length=16)
    effective_date: date
    action_type: Literal["cash_dividend", "split_adjustment"]
    market: Optional[Literal["cn", "hk", "us"]] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=8)
    cash_dividend_per_share: Optional[float] = Field(None, ge=0)
    split_ratio: Optional[float] = Field(None, gt=0)
    note: Optional[str] = Field(None, max_length=255)


class PortfolioEventCreatedResponse(BaseModel):
    id: int


class PortfolioDeleteResponse(BaseModel):
    deleted: int


class PortfolioTradeListItem(BaseModel):
    id: int
    account_id: int
    trade_uid: Optional[str] = None
    symbol: str
    market: str
    currency: str
    trade_date: str
    side: str
    quantity: float
    price: float
    fee: float
    tax: float
    note: Optional[str] = None
    created_at: Optional[str] = None


class PortfolioTradeListResponse(BaseModel):
    items: List[PortfolioTradeListItem] = Field(default_factory=list)
    total: int
    page: int
    page_size: int


class PortfolioCashLedgerListItem(BaseModel):
    id: int
    account_id: int
    event_date: str
    direction: str
    amount: float
    currency: str
    note: Optional[str] = None
    created_at: Optional[str] = None


class PortfolioCashLedgerListResponse(BaseModel):
    items: List[PortfolioCashLedgerListItem] = Field(default_factory=list)
    total: int
    page: int
    page_size: int


class PortfolioCorporateActionListItem(BaseModel):
    id: int
    account_id: int
    symbol: str
    market: str
    currency: str
    effective_date: str
    action_type: str
    cash_dividend_per_share: Optional[float] = None
    split_ratio: Optional[float] = None
    note: Optional[str] = None
    created_at: Optional[str] = None


class PortfolioCorporateActionListResponse(BaseModel):
    items: List[PortfolioCorporateActionListItem] = Field(default_factory=list)
    total: int
    page: int
    page_size: int


class PortfolioPositionItem(BaseModel):
    symbol: str
    market: str
    currency: str
    quantity: float
    avg_cost: float
    total_cost: float
    last_price: float
    market_value_base: float
    unrealized_pnl_base: float
    unrealized_pnl_pct: Optional[float] = None
    valuation_currency: str
    price_source: str = "unknown"
    price_provider: Optional[str] = None
    price_date: Optional[str] = None
    price_stale: bool = False
    price_available: bool = True


class PortfolioAccountSnapshot(BaseModel):
    account_id: int
    account_name: str
    owner_id: Optional[str] = None
    broker: Optional[str] = None
    market: str
    base_currency: str
    as_of: str
    cost_method: str
    total_cash: float
    total_market_value: float
    total_equity: float
    realized_pnl: float
    unrealized_pnl: float
    fee_total: float
    tax_total: float
    fx_stale: bool
    positions: List[PortfolioPositionItem] = Field(default_factory=list)


class PortfolioSnapshotResponse(BaseModel):
    as_of: str
    cost_method: str
    currency: str
    account_count: int
    total_cash: float
    total_market_value: float
    total_equity: float
    realized_pnl: float
    unrealized_pnl: float
    fee_total: float
    tax_total: float
    fx_stale: bool
    accounts: List[PortfolioAccountSnapshot] = Field(default_factory=list)


class PortfolioImportTradeItem(BaseModel):
    trade_date: str
    symbol: str
    side: Literal["buy", "sell"]
    quantity: float
    price: float
    fee: float
    tax: float
    trade_uid: Optional[str] = None
    dedup_hash: str
    currency: Optional[str] = None


class PortfolioImportParseResponse(BaseModel):
    broker: str
    record_count: int
    skipped_count: int
    error_count: int
    records: List[PortfolioImportTradeItem] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class PortfolioImportCommitResponse(BaseModel):
    account_id: int
    record_count: int
    inserted_count: int
    duplicate_count: int
    failed_count: int
    dry_run: bool
    errors: List[str] = Field(default_factory=list)


class PortfolioImportBrokerItem(BaseModel):
    broker: str
    aliases: List[str] = Field(default_factory=list)
    display_name: Optional[str] = None


class PortfolioImportBrokerListResponse(BaseModel):
    brokers: List[PortfolioImportBrokerItem] = Field(default_factory=list)


class PortfolioFxRefreshResponse(BaseModel):
    as_of: str
    account_count: int
    refresh_enabled: bool
    disabled_reason: Optional[str] = None
    pair_count: int
    updated_count: int
    stale_count: int
    error_count: int


class PortfolioRiskResponse(BaseModel):
    as_of: str
    account_id: Optional[int] = None
    cost_method: str
    currency: str
    thresholds: Dict[str, Any] = Field(default_factory=dict)
    concentration: Dict[str, Any] = Field(default_factory=dict)
    sector_concentration: Dict[str, Any] = Field(default_factory=dict)
    drawdown: Dict[str, Any] = Field(default_factory=dict)
    stop_loss: Dict[str, Any] = Field(default_factory=dict)


# ===================================
# 2026-05-06: 融资融券相关 Schema
# ===================================


class MarginTradeCreateRequest(BaseModel):
    """融资融券交易录入请求"""
    account_id: int
    symbol: str = Field(..., min_length=1, max_length=16)
    market: Literal["cn", "hk", "us"] = "cn"
    side: Literal["margin_buy", "short_sell", "margin_repay", "short_cover"]
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    interest_rate: float = Field(..., ge=0, description="年利率，如0.08表示8%")
    fee: float = Field(0.0, ge=0)
    tax: float = Field(0.0, ge=0)
    note: Optional[str] = Field(None, max_length=255)


class MarginDetailItem(BaseModel):
    """融资融券明细"""
    id: int
    account_id: int
    trade_id: Optional[int] = None
    symbol: str
    market: str
    margin_type: Literal["margin", "securities"]
    principal: float
    quantity: Optional[float] = None
    interest_rate: float
    accrued_interest: float = 0.0
    total_interest_paid: float = 0.0
    open_date: str
    close_date: Optional[str] = None
    is_open: bool = True
    collateral_value: Optional[float] = None
    maintenance_ratio: Optional[float] = None
    note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MarginDetailListResponse(BaseModel):
    """融资融券明细列表"""
    items: List[MarginDetailItem] = Field(default_factory=list)
    total: int


class MarginSummary(BaseModel):
    """融资融券汇总"""
    total_margin_principal: float = 0.0  # 融资总额
    total_securities_principal: float = 0.0  # 融券总额
    total_interest_accrued: float = 0.0  # 累计应计利息
    total_interest_paid: float = 0.0  # 累计已付利息
    open_margin_count: int = 0  # 未平仓融资笔数
    open_securities_count: int = 0  # 未平仓融券笔数
    maintenance_ratio: Optional[float] = None  # 维持担保比例
    collateral_value: Optional[float] = None  # 担保品价值


class MarginInterestItem(BaseModel):
    """融资融券利息明细"""
    detail_id: int
    symbol: str
    margin_type: str
    principal: float
    interest_rate: float
    open_date: str
    days_held: int
    accrued_interest: float
    total_interest_paid: float


class MarginInterestResponse(BaseModel):
    """融资融券利息计算响应"""
    as_of: str
    items: List[MarginInterestItem] = Field(default_factory=list)
    total_accrued: float = 0.0


class MaintenanceRatioResponse(BaseModel):
    """维持担保比例响应"""
    account_id: int
    account_name: str
    total_assets: float = 0.0  # 总资产
    total_liabilities: float = 0.0  # 总负债
    net_equity: float = 0.0  # 净资产
    maintenance_ratio: Optional[float] = None  # 维持担保比例
    margin_call_threshold: float = 150.0  # 追保线（%）
    liquidation_threshold: float = 130.0  # 平仓线（%）
    risk_level: str = "safe"  # safe / warning / danger


class MarginCloseRequest(BaseModel):
    """平仓融资融券请求"""
    close_date: date
    repay_amount: Optional[float] = Field(None, gt=0, description="还款金额（融资）")
    repay_quantity: Optional[float] = Field(None, gt=0, description="还券数量（融券）")
