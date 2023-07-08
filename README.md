# ECE531 Cloud Endpoint assignment using MongoDB with FastAPI

This is a project to build a quick API with [MongoDB](https://developer.mongodb.com/) and [FastAPI](https://fastapi.tiangolo.com/).
It based on a [blog post](https://developer.mongodb.com/quickstart/python-quickstart-fastapi/) - you should go read it!

## Author
Andrew Rechenberg\
Universtory of New Mexico\
Internet of Things (IoT), Summer 2023\
arechenberg at unm dot edu\
andrew at rechenberg dot net

## TL;DR

NOTE: YOU MUST HAVE ALREADY INSTALL MONGODB FOR THIS TL;DR TO WORK. 

This code has been tested on Ubuntu 22.04 LTS. It should run just fine on other operating systems, but YMMV. A quick guide to install monogodb on Ubuntu 22.04 is available here:

https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/

If you really don't want to read the [blog post](https://developer.mongodb.com/quickstart/python-quickstart-fastapi/) and want to get up and running,
activate your Python virtualenv, and then run `./start.sh`. The startup script starts the API listening on all local IP addresses and TCP port 8989. 

```bash
# Install the requirements:
pip install -r requirements.txt

# Ensure mongodb is started (on Ubuntu)
sudo systemctl enable mongod
sudo systemctl restart mongod

# Start the service:
./start.sh
```

If the code has documentation turned on, you can load http://localhost:8989/flux in your browser to view the API methods available. There won't be much to see until you've inserted some data. See the `app = FastAPI(docs_url=...)` line in the code to find the docs URL or to turn it on or off. Set `docs_url=None` to turn off the docs URL.

## API Endpoint Description

The following is a description of the Thermostat Daemon API. An end user should never have to know this information and is being provided here for documentation and testing purposes.

| **URL path** | **HTTP method** | **Required arguments** | **Description** |
| -------------| --------------- | ---------------------- | --------------- |
| **/** | GET | None | Return complete thermostat status: current set point, temperature, heater status, and thermostat schedule. |
| **/schedule** | GET | None | Returns full schedule of temperature set points. |
| **/schedule** | POST | Set point JSON Object in POST body. Example below. | Creates a single thermostat schedule set point. |
| **/schedule/{id}** | GET | None | Returns single schedule set point identified by {id} |
| **/schedule/{id}** | PUT | Set point JSON Object in PUT body. Example below.  | Updates single data object identified by {id} |
| **/schedule/{id}** | DELETE | None | Deleted single schedule set point identified by {id} |
| **/reset_schedule** | POST | None | Resets the thermostat schedule removing all temperature set points. |
| **/thermostat_status** | GET | None | Returns only thermostat status. No schedule set points. |
| **/thermostat_status** | POST | Thermostat status JSON object in POST body. Example below | Creates a thermostat status if one doesn't exist. Returns 403 if status entry already exists. |
| **/reset_thermostat_status** | POST | None | Removes thermostat status entry. Returns 403 if there is no status entry. |
