"""Pydantic models for OptionSense API responses."""
from pydantic import BaseModel
from typing import List, Literal


class VWAPSignal(BaseModel):
    value: float
    is_bullish: bool
    message: str


class PCRData(BaseModel):
    value: float
    trend: Literal["RISING", "FALLING", "STABLE"]


class SentimentData(BaseModel):
    score: int
    label: Literal["STRONG BUY", "STRONG SELL", "NEUTRAL"]
    color: str


class OIAlert(BaseModel):
    message: str
    bg_color: str


class DashboardData(BaseModel):
    price: float
    price_change: float
    price_change_pct: float
    vwap_signal: VWAPSignal
    pcr: PCRData
    sentiment: SentimentData
    oi_alert: OIAlert


class DashboardSnapshot(BaseModel):
    status: str
    symbol: str
    last_updated: str
    market_status: Literal["OPEN", "CLOSED"]
    data: DashboardData


class StrikeData(BaseModel):
    strike: int
    ce_change: int
    pe_change: int
    ce_bar_color: Literal["GREEN", "RED", "GREY"]
    pe_bar_color: Literal["GREEN", "RED", "GREY"]
    is_atm: bool = False


class OIDetails(BaseModel):
    status: str
    symbol: str
    atm_strike: int
    strikes: List[StrikeData]
