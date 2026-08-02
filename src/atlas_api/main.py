#!/usr/bin/env python3


from fastapi import FastAPI

from atlas_api.routes import API_ROUTERS

app = FastAPI()

for router in API_ROUTERS:
    app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}