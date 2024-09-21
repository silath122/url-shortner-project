from fastapi import FastAPI, Path, Query, HTTPException
from typing import Optional
from pydantic import BaseModel
import uuid
from datetime import datetime

# python -m uvicorn url_service:app --reload to run on my computer
# uvicorn url_service:app --reload to run on other computers


app = FastAPI()

# not sure if I'll need this tbh
class urlItem(BaseModel):
    url: str
    short_url: Optional[str] = None


urls = []


# Creates and appends new url item to urls
@app.post("/shorten_url")
def shorten_url(url_item: urlItem):
    
    if url_item.short_url in [item["short_url"] for item in urls]: # if short_url already in urls list
        raise HTTPException(status_code=404, detail=f"Short URL '{url_item.short_url}' already exists.")
    
    # Generate a new short URL if none is provided
    short_url = url_item.short_url or str(uuid.uuid5(uuid.NAMESPACE_URL, url_item.url))[:10]
    
    timestamp = datetime.now().ctime() # create timestamp
    
    # append created url item to urls list
    urls.append({
        "short_url": short_url,
        "url": url_item.url,
        "timestamp": timestamp
    })

    # return this if successful
    return {"short_url" : short_url}

# Returns list of urls in db
@app.get("/list_urls")
def list_urls():
    return urls


@app.get("/redirect/{short_url}")
def redirect(short_url: str):
    return {}

@app.delete("/delete_url")
def delete_url(short_url : str):
    return {}