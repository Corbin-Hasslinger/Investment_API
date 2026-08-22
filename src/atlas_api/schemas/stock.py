#!/usr/bin/env python3

from pydantic import BaseModel
from decimal import Decimal


class StockQuote(BaseModel):
    symbol: str 
    current_price: Decimal
    price_change: Decimal
    percent_change: Decimal
    high_price: Decimal
    low_price: Decimal
    open_price: Decimal
    previous_close_price: Decimal
    timestamp: int