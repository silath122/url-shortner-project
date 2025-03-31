
FROM python:3.12.9 AS base

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
CMD ["uvicorn", "url_service:app", "--host", "--port", "8000"]


# Define test stage
FROM base AS test

RUN pip install --no-cache-dir pytest

CMD ["pytest", "--disable-warnings"]