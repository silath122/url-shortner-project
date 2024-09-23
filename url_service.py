from fastapi import FastAPI, Path, Query, HTTPException
from fastapi.responses import RedirectResponse # to redirect the client to the website
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


# Creates and appends new url item to database containing urls
@app.post("/shorten_url")
def shorten_url(url_item: urlItem):
    
    if url_item.short_url in [item["short_url"] for item in urls]: # if short_url already in urls list
        raise HTTPException(status_code=404, detail=f"Short URL '{url_item.short_url}' already exists.")
    
    # Generate a new short URL if none is provided
    url_len = len(url_item.url) - 6 # gets rid of www and edu/com/org because I know a url MUST contain those 2 items that are of length 6 in total (sometimes 5)
    short_url = url_item.short_url or str(uuid.uuid5(uuid.NAMESPACE_URL, url_item.url))[:url_len]
    
    timestamp = datetime.now().ctime() # create timestamp
    
    # append created url item to urls list
    urls.append({
        "short_url": short_url,
        "url": url_item.url,
        "timestamp": timestamp
    })

    # return this if successful
    return {"short_url" : short_url}


# Returns list of urls from database
@app.get("/list_urls")
def list_urls():
    return urls


# Redirect the client to the original website in the database given the request short_url
@app.get("/redirect/{short_url}")
def redirect(short_url: str):
    # find the original url or raise an error if not found
    item = next((item for item in urls if item["short_url"] == short_url), None)

    if item is None:
        raise HTTPException(status_code=404, detail=f"No URL found for '{short_url}'.")
    
    # Redirect to the original URL
    return RedirectResponse(url=item["url"]) and {"url" : item}


# Delete url item from database
@app.delete("/delete_url/{short_url}")
def delete_url(short_url: str):
    global urls
    item = next((item for item in urls if item["short_url"] == short_url), None)
    
    if item is None:
        raise HTTPException(status_code=404, detail="Url does not exist.")
    
    urls = [url for url in urls if url["short_url"] != short_url]
    
    return {"Success": "Url deleted!"}