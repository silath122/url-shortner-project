from datetime import datetime
from fastapi import FastAPI, HTTPException
import boto3
from pydantic import BaseModel
import uuid
from typing import Optional

app = FastAPI()


# Get the service resource
dynamodb = boto3.resource('dynamodb')

# Instantiate table resource object
table = dynamodb.Table('url-shortner-db')

# Instatiate item object to add to table
class Url(BaseModel):
    original_url: str
    short_url: Optional[str] = None
    timestamp: Optional[str] = None

# POST /shorten_url: Shortens a URL
@app.post("/shorten_url")
def shorten_url(original_url: str, short_url: Optional[str] = None):
    # need to check if original url is already in database
    if short_url != None and short_url in table:
        raise HTTPException(status_code=404, detail="Short URL '{short_url}' already exists.")
    
    # if it is not provided by user then make short url using uuid
    elif short_url == None:
        return {}

    # if the short url is provided by user and not in the database then
    # add to database and return url item
    else:
        return{}



# GET /list_urls: Lists all shortened URLs
@app.get("/list_urls")
def list_urls():
    # loop through items in database and append to list
    # return entire list
    return {}


# GET /redirect/{short_url}: Redirects to the original URL
@app.get("/redirect/{short_url}")
def redirect(short_url: str):

    # if short url does not exist then return error message:
    # {"error_message":"No URL fond for 'nonexistent' found."}

    # if short url does exist then redirect to original url
    # Response 200: {"original_url":"https://www.example.com"}

    return {}
