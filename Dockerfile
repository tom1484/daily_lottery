FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the contents into the container at /app
COPY ./requirements.txt ./
COPY ./src/* ./
COPY ./.env ./

RUN pip3 install -r ./requirements.txt

EXPOSE 5000
CMD [ "python3", "./wsgi.py"]
