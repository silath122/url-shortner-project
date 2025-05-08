from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt import InvalidTokenError
import jwt
from passlib.context import CryptContext

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import BotoCoreError, ClientError

from pydantic import BaseModel
import random
import string
from typing import Optional
from datetime import datetime, timezone, timedelta

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

# Instantiate table resource object for url shortners and users
table = dynamodb.Table('url-shortner-db')
user_table = dynamodb.Table('url-shortner-users')

# for user access - JWT Config
SECRET_KEY = "54fa514fb1ae408676769e8073ca2bf4918c5897fabbc63ffa21b351345225d7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Authoriation dependencies
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# models for users and urls
class Url(BaseModel):
    original_url: str
    short_url: str = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    url_limit: int
    disabled: bool = False  # Default to False

class UserInDB(User):
    hashed_password: str

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

# utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(user_table, username: str):
    try:
        # query the user table for the given username
        response = user_table.query(
            KeyConditionExpression=Key('username').eq(username)
        )
        # check if the user exists in the table
        if response['Items']:
            user_data = response['Items'][0]  # extract the first item from the response
            return UserInDB(**user_data) # gets the key value pairs "**"
        else:
            return None  # User not found
    except ClientError as e:
        # handle DynamoDB client errors
        raise HTTPException(status_code=500, detail=f"Error querying user table: {str(e)}")
    
def authenticate_user(user_table, username: str, password: str):
    user = get_user(user_table, username)
    if not user:
        return False # you are not authenticated and user does not exist
    if not verify_password(password, user.hashed_password):
        return False # password is wrong 
    
    return user

# create access token based on login data
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy() # copy data so if we make any changes to it, the original one is not changed
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt # this is our access token

async def get_current_user(token: str = Depends(oauth2_scheme)): # calls oauth2 function which parses out token and gives the user access to it in this parameter 
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials", headers={"WW-Authenticate":"Bearer"}) # could not authetnicate bearer token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # parse out the token
        username: str = payload.get("sub") # get the user that is encoded in the token
        if username is None: # check if user exists
            raise credential_exception # user does not exist
        
        token_data = TokenData(username=username) # use tokendata model to store username
    except InvalidTokenError:
        raise credential_exception
    
    user = get_user(user_table, username=token_data.username) # make sure user is inside database
    if user is None:
        raise credential_exception
    
    return user # if user is in database

# checks if user is not active 
async def get_current_active_user(curr_user: UserInDB = Depends(get_current_user)):
    if curr_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return curr_user

@app.post("/token", response_model=Token)
# the data that we accept here will be a username and password, which is specified in the OAuth2PasswordRequestForm stuff
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(user_table, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password", headers={"WW-Authenticate":"Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta= access_token_expires)

    return{"access_token": access_token, "token_type": "bearer"}

# sign up a user
@app.post("/create_user")
async def create_user(user: UserInDB):
    try:
        # Hash the password before storing it
        hashed_pw = get_password_hash(user.hashed_password)
        user_table.put_item(Item={
            "username": user.username,
            "hashed_password": hashed_pw,
            "url_limit": user.url_limit,
            "disabled": user.disabled  # Default is False unless explicitly set
        })
        return {"msg": f"User {user.username} created successfully."}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

# change password of user
@app.post("/change_password")
async def change_password(password_change: PasswordChange, current_user: UserInDB = Depends(get_current_user)):
    # Ensure the user is active
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    # Verify the old password
    if not verify_password(password_change.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect.")
    
    # Hash the new password
    new_hashed_password = get_password_hash(password_change.new_password)
    
    try:
        # Update the user's password in the database
        user_table.update_item(
            Key={"username": current_user.username},
            UpdateExpression="SET hashed_password = :new_password",
            ExpressionAttributeValues={":new_password": new_hashed_password}
        )
        return {"msg": "Password updated successfully."}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error updating password: {str(e)}")

# get list of user's personal URLs
@app.get("/list_my_urls")
async def list_my_urls(current_user: UserInDB = Depends(get_current_active_user)):
    try:
        # query the table for URLs belonging to the current user
        response = table.scan(
            FilterExpression=Key("username").eq(current_user.username)
        )
        user_urls = response.get("Items", [])
        
        # format the response
        return [
            {
                "original_url": item["original_url"],
                "short_url": item["short_url"],
                "timestamp": item["timestamp"]
            }
            for item in user_urls
        ]
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving URLs: {str(e)}")

# update the url limit for user
@app.post("/update_url_limit")
async def update_url_limit(new_limit: int, current_user: UserInDB = Depends(get_current_active_user)):
    try:
        # update the users URL limit in the database
        user_table.update_item(
            Key={"username": current_user.username},
            UpdateExpression="SET url_limit = :new_limit",
            ExpressionAttributeValues={":new_limit": new_limit}
        )
        return {"msg": f"URL limit updated to {new_limit} for user {current_user.username}."}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error updating URL limit: {str(e)}")


# POST /shorten_url: Shortens a URL
@app.post("/shorten_url")
async def shorten_url(url: Url, current_user: UserInDB = Depends(get_current_active_user)):
    # check if the user has reached their URL limit
    response = table.scan(
        FilterExpression=Key("username").eq(current_user.username)
    )
    if len(response.get("Items", [])) >= current_user.url_limit:
        raise HTTPException(status_code=403, detail="URL limit reached. Please update your limit or delete existing URLs.")

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

    # add timestamp and username to url item
    url_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    url_dict["username"] = current_user.username

    try:
        # store in dynamodb 
        response = table.put_item(
            Item={
                "original_url": url_dict["original_url"],
                "short_url": url_dict["short_url"], # partition key
                "timestamp": url_dict["timestamp"], # sort key
                "username": url_dict["username"]
            }
        )

        # check if put_item was successful
        if response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200:
            return {"short_url": url_dict["short_url"]}
        
        # raise exception if the data failed to be stored in URL
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
                        "timestamp":item["timestamp"],
                        "username":item["username"]})
    # loop through items in database and append to list
    # return entire list
    return final_lst


# GET /redirect/{short_url}: Redirects to the original URL
@app.get("/redirect/{short_url}")
def redirect(short_url: str):

    # query for singular short url in table
    response = table.scan(FilterExpression=Key('short_url').eq(short_url))

    # if response contains no items that are equal short_url provided by user
    if response['Items'] == []:
        raise HTTPException(status_code=404, detail=f"No URL found for '{short_url}' found.") 
    
    # only one item to loop through the list of items
    for item in response['Items']:
        return {"original_url" : item["original_url"]}