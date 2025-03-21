from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from pydantic import BaseModel
import uuid
from typing import Optional

# In the terminal, start the FastAPI server using Uvicorn
# uvicorn url_service:app --reload

app = FastAPI()

# # Work flow
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

# Instantiate table resource object
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
    if url_dict['short_url']:
        # check if the short_url is already in table 
        existing_item = table.get_item(Key={"short_url": url_dict["short_url"]}) # the error starts here
        if "Item" in existing_item:
            raise HTTPException(status_code=404, detail="Short URL '{short_url}' already exists.")
    else:
        # create unique short_url
        while True:
            temp_short_url = str(uuid.uuid4())[:8]
            existing_item = table.get_item(Key={"pk": temp_short_url})
            if "Item" not in existing_item:
                url_dict["short_url"] = temp_short_url
                break

    

    # add timestamp to url item
    url_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

    try:
        # store in dynamodb 
        response = table.put_item(
            Item={
                'pk': url_dict["short_url"],
                'sk': url_dict["timestamp"],
                'original_url': url_dict["original_url"]
            }
        )

        # check if put_itm was successful
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            return {"short_url": url_dict["short_url"]}
        
        # raise exception it the data was failed to be stored in URL
        raise HTTPException(status_code=500, detail="Failed to store URL")
    
    except BotoCoreError as e:
        raise HTTPException(status_code=500, detail="DynamoDB connection error")




# # GET /list_urls: Lists all shortened URLs
# @app.get("/list_urls")
# def list_urls():
#     # loop through items in database and append to list
#     # return entire list
#     return {}


# # GET /redirect/{short_url}: Redirects to the original URL
# @app.get("/redirect/{short_url}")
# def redirect(short_url: str):

#     # if short url does not exist then return error message:
#     # {"error_message":"No URL fond for 'nonexistent' found."}

#     # if short url does exist then redirect to original url
#     # Response 200: {"original_url":"https://www.example.com"}

#     return {}
