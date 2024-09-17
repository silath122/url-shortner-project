from fastapi import FastAPI, Path, Query, HTTPException
from typing import Optional
from pydantic import BaseModel

# python -m uvicorn fastapi-practice:app --reload to run on my computer

app = FastAPI()

class urlItem(BaseModel):
    url: str
    timestamp: str
    short_url: str


urls = {}

@app.post("/shorten_url")
def shorten_url(url: str, short_url: Optional[str] = None):
    return {}

@app.get("/list_urls")
def list_urls():
    return {}


@app.get("/redirect/{short_url}")
def redirect(short_url: str):
    return {}