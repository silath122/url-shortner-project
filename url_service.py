from datetime import datetime
from fastapi import FastAPI
import boto3


# Get the service resource
dynamodb = boto3.resource('dynamodb')

# Instantiate table resource object
table = dynamodb.Table('url-shortner-db')