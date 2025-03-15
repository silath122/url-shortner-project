from datetime import datetime
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
    short_url: str | None = None # it's saying that there is an issue with short_url not existing in the url_dict
    timestamp: str | None = None # it can't process the code

# POST /shorten_url: Shortens a URL
@app.post("/shorten_url")
def shorten_url(url: Url):

    # Model_dump is BaseModels version of a dictionary
    url_dict = url.model_dump()

    # need to check if original url is already in database
    if url_dict.short_url is not None and url_dict.short_url in table:
        raise HTTPException(status_code=404, detail="Short URL '{short_url}' already exists.")
    
    # if it is not provided by user then make short url using uuid
    elif url_dict.short_url is None:
        # create an escape_loop value and make it true
        escape_loop = False

        # Create a while loop that keeps going while False
        while escape_loop == False:

            # create temp_short_url using uuid and make it 8 characters only
            temp_short_url = (str(uuid.uuid4()))[:8]

            # check if temp_short_url already exists in the database
            if temp_short_url not in table:
                # if not then change escape_loop to True otherwise just continue with loop\
                escape_loop = True
        
        # update url item and add temp_short_url to short_url
        url.short_url = temp_short_url
        

    # add timestamp to url item
    url.timestamp = str(datetime.now(tzinfo=datetime.timezone.utc))

    try:
        # if the short url is provided by user and not in the database then
        # add to database and return url item
        response = table.put_item(
            Item={
                'pk': url.short_url,
                'sk': url.timestamp,
                'original_url': url.original_url
            }
        )

        # check if put_itm was successful
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            return {"short_url": url.short_url}
        
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
