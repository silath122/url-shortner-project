from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel
import random
import string
from typing import Optional

# In the terminal, start the FastAPI server using Uvicorn
# uvicorn url_service:app --reload

app = FastAPI()

# # Work flow Testing
# 1️⃣ Develop your API
# Write your FastAPI endpoints (@app.get(), @app.post(), etc.).
# 2️⃣ Use Postman for quick testing
# Send a request → Check if it works → Fix any issues.
# 3️⃣ Once API works, write unittest tests
# Automate the tests using unittest so future changes won’t break your API.
# 4️⃣ Use Postman for debugging when things break
# If a unittest test fails, use Postman to send the request manually and figure out the issue.

# Get the service resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Instantiate table resource object for url shortners
table = dynamodb.Table('url-shortner-db')

# Instatiate item object to add to table
class Url(BaseModel):
    original_url: str
    short_url: str = None

# POST /shorten_url: Shortens a URL
@app.post("/shorten_url")
def shorten_url(url: Url):

    # Model_dump is BaseModels version of a dictionary
    url_dict = url.model_dump()

    # check if the user provided short_url  
    if url_dict["short_url"]:
        # check if the short_url is already in table 
        response = table.query(
            KeyConditionExpression=Key('short_url').eq(url_dict['short_url'])
        )

        if response['Items']:
            raise HTTPException(status_code=404, detail=f"Short URL '{url_dict['short_url']}' already exists.")

    else:
        # create unique short_url
        while True:
            characters = string.ascii_letters + string.digits # a-z, A-Z, 0-9
            temp_short_url = "".join(random.choices(characters, k=8))
            
            response = table.query(
                KeyConditionExpression=Key('short_url').eq(temp_short_url)
            )

            if not response['Items']:
                url_dict["short_url"] = temp_short_url
                break

    # return {'short_url': url_dict["short_url"]}

    # add timestamp to url item
    url_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

    try:
        # store in dynamodb 
        response = table.put_item(
            Item={
                "short_url": url_dict["short_url"], # partition key
                "timestamp": url_dict["timestamp"], # sort key
                "original_url": url_dict["original_url"]
            }
        )

        # check if put_itm was successful
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            return {"short_url": url_dict["short_url"]}
        
        # raise exception it the data was failed to be stored in URL
        raise HTTPException(status_code=500, detail="Failed to store URL")
    
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail=f"DynamoDB error: {str(e)}")




# GET /list_urls: Lists all shortened URLs
@app.get("/list_urls")
def list_urls():
    final_lst = []
    response = table.scan()
        
    for item in response['Items']:
        final_lst.append({"short_url":item["short_url"],
                        "original_url":item["original_url"],
                        "timestamp":item["timestamp"]})
    # loop through items in database and append to list
    # return entire list
    return final_lst


# GET /redirect/{short_url}: Redirects to the original URL
@app.get("/redirect/{short_url}")
def redirect(short_url: str):

    # query for singular short url in table
    response = table.query(KeyConditionExpression=Key('short_url').eq(short_url))

    # if response contains no items that are equal short_url provided by user
    if response['Items'] == []:
        raise HTTPException(status_code=404, detail=f"No URL found for '{short_url}' found.") 
    
    # only one item to loop through the list of items
    for item in response['Items']:
        return {"original_url" : item["original_url"]}