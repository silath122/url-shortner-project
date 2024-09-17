import unittest
from url_service import app, urlItem, urls, shorten_url, list_urls, redirect
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Tomorrow figure out how to implement fastapi.testclient with unittest
# Might switch out unittest for fastapi.testclient because of difficulty with proving redirect

"""
Test suite for url_service.py
"""
class TestUrlServiceMethods(unittest.TestCase):
    
    def setUp(self):
        urls.clear()

    # Test case function to check if the shorten_url works with a custom short_url
    def test_shorten_url_custom(self):
        print("Start shorten_url custom test\n")

        self.assertEqual(shorten_url("http://www.example.com", "exampleShort"), {"short_url":"exampleShort"})
        
    # Test to check if you can not add the same short_url to the database twice
    def test_shorten_url_twice(self):
        print("Start shorten_url twice custom test\n")

        shorten_url("http://www.example.com", "exampleShort")
        self.assertRaises(HTTPException,shorten_url("http://www.example.com", "exampleShort"))

    # Test case function to check if the shorten_url works without a custom short_url
    def test_shorten_url(self):
        print("Start shorten_url without custom test\n")

        self.assertNotEqual(shorten_url("http://www.example.com","exampleShort"), shorten_url("http://www.example.com"))

    # Test case function to check if list_urls gets a list of all url items
    def test_list_urls(self):
        print("Start list_urls test\n")
        
        shorten_url("http://www.example.com", "exampleShort")
        shorten_url("http://www.example.com", "abc123")

        self.assertEqual(list_urls(), 
            [
                {
                    "short_url":"exampleShort",
                    "url":"http://www.example.com"
                },
                {
                    "short_url":"abc123",
                    "url":"http://www.example.com"
                }
            ])

    # Test case function to see if short_url redirects to its original url
    def test_redirect(self):
        print("Start true redirect test\n")
        shorten_url("http://www.example.com", "abc123")
        # WIP finish tomorrow




    # Test case function to see if short_url does not redirects to its original url
    #def test_redirect(self):

if __name__ == '__main__':
    unittest.main()