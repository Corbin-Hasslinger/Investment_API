#!/usr/bin/env python3

from pydantic import BaseModel


class StockQuote(BaseModel):
    symbol: str 
    current_price: float
    price_change: float
    percent_change: float
    high_price: float
    low_price: float
    open_price: float
    previous_close_price: float
    timestamp: int