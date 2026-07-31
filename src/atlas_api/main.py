#!/usr/bin/env python3

import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class StockPurchase(BaseModel):
    ticker: str
    shares: int
    price: float

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

@app.get("/stocks/{ticker}")
async def get_stock(ticker: str, days: int = 30):
    return {
        "ticker": ticker,
        "days": days,
    }

@app.get("/stocks/{ticker}/quote")
async def get_stock_quote(ticker: str):
    """Fetches the latest stock quote for the given ticker symbol, using the Finnhub API.

    Return fields: 
        c: Current price
        d: Price change
        dp: Percent change
        h: High price of the day
        l: Low price of the day
        o: Open price of the day
        pc: Previous close price
        t: Unix timestamp for the quote.
    """
    if not FINNHUB_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="Finnhub API key not found in environment variables."
        )
    url = "https://finnhub.io/api/v1/quote"
    params = {
        "symbol": ticker,
        "token": FINNHUB_API_KEY
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error fetching stock quote: {response.text}"
            )
        quote_data = response.json()
        return {
            "ticker": ticker.upper(),
            "current_price": quote_data.get("c"),
            "price_change": quote_data.get("d"),
            "percent_change": quote_data.get("dp"),
            "high_price": quote_data.get("h"),
            "low_price": quote_data.get("l"),
            "open_price": quote_data.get("o"),
            "previous_close_price": quote_data.get("pc"),
            "timestamp": quote_data.get("t"),
        }