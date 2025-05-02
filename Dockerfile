# For me only to run: docker run -p 8888:8000 silath122/url-shortner-proj

FROM python:3.12.9

# set a directory for the app
WORKDIR /app

# copy requirements file into container
COPY requirements.txt .

# install depedencies
RUN pip install --no-cache-dir -r requirements.txt

# copy rest of applications
COPY . .

# Define the FastAPI port used
EXPOSE 8000

# Command to run application
CMD ["uvicorn", "url_service:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/etc/letsencrypt/live/messiah-urlshortnerproject.com-0001/privkey.pem", "--ssl-certfile", "/etc/letsencrypt/live/messiah-urlshortnerproject.com-0001/fullchain.pem"]


