# ECE531 Cloud Endpoint assignment using MongoDB with FastAPI

This is a project to build a quick API with [MongoDB](https://developer.mongodb.com/) and [FastAPI](https://fastapi.tiangolo.com/).
It based on a [blog post](https://developer.mongodb.com/quickstart/python-quickstart-fastapi/) - you should go read it!

## Author
Andrew Rechenberg\
Universtory of New Mexico\
Internet of Things (IoT), Summer 2023\
arechenberg at unm dot edu\
github at rechenberg dot net

## TL;DR

If you really don't want to read the [blog post](https://developer.mongodb.com/quickstart/python-quickstart-fastapi/) and want to get up and running,
activate your Python virtualenv, and then run the following from your terminal (edit the `MONGODB_URL` first!):

```bash
# Install the requirements:
pip install -r requirements.txt

# Configure the location of your MongoDB database:
export MONGODB_URL="mongodb://localhost:8989/thermostat?retryWrites=true&w=majority"

# Start the service:
uvicorn app:app --reload --header "server:ece531endpoint/0.0.1" --host 0.0.0.0 --port 8989
```

Now you can load http://localhost:8989/docs in your browser ... but there won't be much to see until you've inserted some data.

