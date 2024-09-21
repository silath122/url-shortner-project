from url_service import app, urls, urlItem, shorten_url, list_urls, redirect
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import unittest

# How to run test
# python -m pytest

"""
Test suite for url_service.py
"""


client = TestClient(app)


# Test case function to check if the shorten_url works with a custom short_url
def test_shorten_url_custom():
    response = client.post("/shorten_url", 
                           json={"url" : "http://www.example.com", "short_url" : "exampleShort"})
    assert response.status_code == 200
    assert response.json() == {"short_url" : "exampleShort"}


# Test to check if you can not add the same short_url to the database twice
def test_shorten_url_already_exists():
    response = client.post("/shorten_url", 
                           json={"url" : "http://www.example.com", "short_url" : "exampleShort"})
    assert response.status_code == 404
    assert response.json() == {"detail" : "Short URL 'exampleShort' already exists."}


# IMPORTANT: Test this case only with the three cases above, otherwise comment it out for the rest of the testing!!

# # Test case function to check if the shorten_url works without a custom short_url
# def test_shorten_url_no_custom():
#     response = client.post("/shorten_url",
#                            json={"url" : "http://www.example.com"})
#     assert response.status_code == 200
#     assert response.json() == {"short_url" : "abc123"}


# Test case function to check if list_urls gets a list of all url items
def test_list_urls():
    response = client.get("/list_urls")
    assert response.status_code == 200
    assert response.json() == urls


# Test case function to see if short_url redirects to its original url
def test_redirect_right():
    response = client.get("/redirect/abc123")
    assert response.status_code == 200
    assert response.json() == {"original_url" : "https://www.example.com"}


# Test case function to see if short_url does not redirects to its original url
def test_redirect_wrong():
    response = client.get("/redirect/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"detail" : "No URL found for 'nonexistent' found."}


# # Test case function to delete url item based off of PK short_url - success
# def test_delete_url_success():
#     response = client.delete("/delete_url",
#                              json={"short_url" : "abc123"})
#     assert response.status_code == 200
#     assert response.json() == {"Success" : "Url deleted!"}


# # Test case function to delete url item based off of PK short_url - fail
# def test_delete_url_fail():
#     response = client.delete("/delete_url", 
#                              json={"short_url" : "nonexistent"})
#     assert response.status_code == 404
#     assert response.json() == {"error_message" : "Item short_url does not exist."}