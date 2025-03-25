from fastapi.testclient import TestClient
from url_service import app

# instal: pip install pytest
# run: pytest

client = TestClient(app)

def test_shorten_url_w_short_url():
    response = client.post("/shorten_url", 
                           json={"original_url":"https://www.example.com",
                                 "short_url":"exampleShortTest"})
    assert response.status_code == 200
    assert response.json() == {"short_url":"exampleShortTest"}

def test_shorten_url_url_already_exists():
    response = client.post("/shorten_url", 
                           json={"original_url":"https://www.example.com",
                                 "short_url":"exampleShortTest"})
    assert response.status_code == 404
    assert response.json() == {'detail':"Short URL 'exampleShortTest' already exists."}

def test_shorten_url_wo_short_url():
    response = client.post("/shorten_url", 
                           json={"original_url":"https://www.example.com"})
    assert response.status_code == 200

def test_list_urls():
    response = client.get("/list_urls")
    assert response.status_code == 200

def test_redirect_urls_pass():
    response = client.get("/redirect/exampleShortTest")
    assert response.status_code == 200
    assert response.json() == {"original_url":"https://www.example.com"}

def test_redirect_urls_fail():
    response = client.get("/redirect/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"detail":"No URL found for 'nonexistent' found."}

