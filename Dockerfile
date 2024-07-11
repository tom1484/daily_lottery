FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the contents into the container at /app
COPY ./requirements.txt ./
COPY ./src/* ./

RUN pip3 install --no-cache-dir -r ./requirements.txt

EXPOSE 5000
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
