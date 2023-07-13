"""

UNM ECE531, Intro to Internet of Things (IoT)
Summer 2023

Andrew Rechenberg
arechenbeg at unm dot edu
andrew at rechenberg dot net

app.py uses fastapi and uvicorn to implement an API endpoint for a
thermostat daemon running on an Internet of Things device. This code
is part of the final project for UNM ECE531 class.

The API is documented in the README.md file in this repository.

"""

import os
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field, EmailStr
from bson import ObjectId
from typing import Optional, List
import motor.motor_asyncio

app = FastAPI(docs_url="/flux")
client = motor.motor_asyncio.AsyncIOMotorClient(os.environ["MONGODB_URL"])
db = client.thermostat
collection_setpoints = "setpoints"
collection_thermostat_status = "thermostat_status"

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class BaseScheduleModel(BaseModel):
    name: str = Field(...)
    time: int = Field(..., ge=0, le=86400)
    temperature: float = Field(..., ge=15.5, le=35.0)
    current: bool = Field(...)


class ScheduleModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    time: int = Field(..., ge=0, le=86400)
    temperature: float = Field(..., ge=15.5, le=35.0)
    current: bool = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "setPoint1",
                "time": "3600",
                "temperature": "20.0",
                "current": "false"
            }
        }

class ScheduleModelResponse(BaseModel):
    setpoints: List[ScheduleModel]

    class Config:
        json_encoders = {ObjectId: str}

class CleanScheduleModel(BaseModel):
    name: str = Field(...)
    time: int = Field(...)
    temperature: float = Field(...)
    current: bool = Field(...)


class CleanScheduleResponse(BaseModel):
    setpoints: List[CleanScheduleModel]


class UploadScheduleModel(BaseModel):
    setpoints: List[BaseScheduleModel]

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "setpoints": [
                     {
                        "name": "setPoint1",
                        "time": "3600",
                        "temperature": "20",
                        "current": "false"
                     },
                     {
                        "name": "setPoint2",
                        "time": "10000",
                        "temperature": "20.2",
                        "current": "true"
                     },
                     {
                        "name": "setPoint3",
                        "time": "24000",
                        "temperature": "18.2",
                        "current": "false"
                     }
                ]
            }
        }

class UpdateScheduleModel(BaseModel):
    name: str
    time: int
    temperature: float
    current: bool

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "name": "setPoint1",
                "time": "3600",
                "temperature": "20.0",
                "current": "False"
            }
        }

class ThermostatStatusModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    current_setpoint: str = Field(...)
    current_temp: float = Field(...)
    heater_status: bool = Field(False)
    new_schedule_avaialble: bool = Field(False)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "current_setpoint": "setPoint3",
                "current_temp": "19.2",
                "heater_status": "False",
                "new_schedule_avaialble": "False"
            }
        }

class UpdateThermostatStatusModel(BaseModel):
    curren_setpoint: str
    current_temp: float
    heater_status: bool
    new_schedule_available: bool

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "current_setpoint": "setPoint3",
                "current_temp": "19.2",
                "heater_status": "False",
                "new_schedule_avaialble": "False"
            }
        }

class ThermostatStatusResponse(BaseModel):
    thermostat_status: List[ThermostatStatusModel]

    class Config:
        json_encoders = {ObjectId: str}


class UpdateThermostatStatusModel(BaseModel):
    current_setpoint: str
    current_temp: float
    heater_status: bool

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "current_setpoint": "setPoint3",
                "current_temp": "19.2",
                "heater_status": "False",
                "new_schedule_available": "False"
            }
        }

class FullStatusModel(BaseModel):
    thermostat_status: List[ThermostatStatusModel]
    setpoints: List[ScheduleModel]

    class Config:
        json_encoders = {ObjectId: str}


@app.get("/", response_description="Display entire thermostat status and set points / schedule.", response_model=FullStatusModel)
async def list_full_status():
    status = await db[collection_thermostat_status].find().to_list(1)
    setpoints = await db[collection_setpoints].find().to_list(1000)
    full_status = FullStatusModel(thermostat_status=status, setpoints=setpoints)
    full_status = jsonable_encoder(full_status)
    return JSONResponse(status_code=200, content=full_status)


@app.post("/schedule", response_description="Add new schedule temperature set point", response_model=ScheduleModel)
async def create_setpoint(setpoint: ScheduleModel = Body(...)):
    setpoint = jsonable_encoder(setpoint)
    new_setpoint = await db[collection_setpoints].insert_one(setpoint)
    created_setpoint = await db[collection_setpoints].find_one({"_id": new_setpoint.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_setpoint)


@app.get(
    "/schedule", response_description="List all setpoints", response_model=ScheduleModelResponse
)
async def list_setpoints():
    setpoints = await db[collection_setpoints].find().to_list(1000)
    schedule = ScheduleModelResponse(setpoints=setpoints)
    schedule = jsonable_encoder(schedule)
    return schedule


@app.get(
    "/schedule/{id}", response_description="Get a single setpoint", response_model=ScheduleModel
)
async def show_setpoint(id: str):
    if (setpoint := await db[collection_setpoints].find_one({"_id": id})) is not None:
        return setpoint

    raise HTTPException(status_code=404, detail=f"Set point {id} not found")


@app.put("/schedule/{id}", response_description="Update a setpoint", response_model=ScheduleModel)
async def update_setpoint(id: str, setpoint: UpdateScheduleModel = Body(...)):
    setpoint = {k: v for k, v in setpoint.dict().items() if v is not None}

    if len(setpoint) >= 1:
        update_result = await db[collection_setpoints].update_one({"_id": id}, {"$set": setpoint})

        if update_result.modified_count == 1:
            if (
                updated_setpoint := await db[collection_setpoints].find_one({"_id": id})
            ) is not None:
                return updated_setpoint

    if (existing_setpoint := await db[collection_setpoints].find_one({"_id": id})) is not None:
        return existing_setpoint

    raise HTTPException(status_code=404, detail=f"Set point {id} not found")


@app.delete("/schedule/{id}", response_description="Delete a setpoint")
async def delete_setpoint(id: str):
    delete_result = await db[collection_setpoints].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(status_code=404, detail=f"Set point {id} not found")


@app.get(
    "/schedule_clean", response_description="List all setpoints with no _id", response_model=CleanScheduleResponse
)
async def list_setpoints():
    setpoints = await db[collection_setpoints].find().to_list(1000)
    clean_schedule = CleanScheduleResponse(setpoints=setpoints)
    return clean_schedule


@app.post("/reset_schedule", response_description="Reset the thermostat schedule removing all temperature set points.", responses={403: {}, 500: {}})
async def reset_schedule(response: Response):
    drop_schedule = [];
    drop_schedule = await db[collection_setpoints].find().to_list(1)
    if drop_schedule != []:
        drop_schedule = await db[collection_setpoints].drop()
        if drop_schedule is None:
            return JSONResponse(status_code=200, content=f"The thermostat status entry was successfully reset.")
        else:
            raise HTTPException(status_code=500, detail=f"There was an internal server error resetting the status. Check server logs.")

    raise HTTPException(status_code=403, detail=f"There is currently no thermostat schedule. POST some new thermostat set points to /schedule endpoint.")


@app.post("/upload_schedule", response_description="Upload full list of schedule set points", response_model=List[ScheduleModel])
async def upload_schedule(full_schedule: UploadScheduleModel = Body(...)):
    full_schedule = jsonable_encoder(full_schedule)
    drop_schedule = []

    # Reset current schedule and create new set points
    drop_schedule = await db[collection_setpoints].find().to_list(1)
    if drop_schedule is not None:
        drop_setpoints = await db[collection_setpoints].drop()

    for setpoint in full_schedule['setpoints']:
        new_setpoint = await db[collection_setpoints].insert_one(setpoint)
        created_setpoint = await db[collection_setpoints].find_one({"_id": new_setpoint.inserted_id})

    setpoints = await db[collection_setpoints].find().to_list(1000)

    if setpoints is not None:
        return setpoints
    else:
        return HTTPException(status_code=500, detail=f"An error occurred resetting the current schedule. Contact an administrator")


@app.get(
    "/thermostat_status", response_description="List the current thermostat system status", response_model=ThermostatStatusResponse
)
async def list_thermostat_status():
    thermostat_status = await db[collection_thermostat_status].find().to_list(1000)
    status_reponse = ThermostatStatusResponse(thermostat_status=thermostat_status)
    status_reponse = jsonable_encoder(status_reponse)
    return status_reponse


@app.post("/thermostat_status", response_description="Create thermostat status entry", response_model=ThermostatStatusModel)
async def create_thermostat_status(thermostat_status: ThermostatStatusModel = Body(...)):
    check_thermostat_status = []
    check_thermostat_status = await db[collection_thermostat_status].find().to_list(1000)
    if check_thermostat_status == []:
        thermostat_status = jsonable_encoder(thermostat_status)
        new_thermostat_status = await db[collection_thermostat_status].insert_one(thermostat_status)
        created_thermostat_status = await db[collection_thermostat_status].find_one({"_id": new_thermostat_status.inserted_id})
        return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_thermostat_status)

    raise HTTPException(status_code=403, detail=f"Thermostat status entry already exists. Use GET method instead.")


@app.put("/thermostat_status/{id}", response_description="Update status", response_model=ThermostatStatusModel)
async def update_status(id: str, status : UpdateThermostatStatusModel = Body(...)):
    status = {k: v for k, v in status.dict().items() if v is not None}

    if len(status) >= 1:
        update_result = await db[collection_thermostat_status].update_one({"_id": id}, {"$set": status})

        if update_result.modified_count == 1:
            if (
                updated_status := await db[collection_thermostat_status].find_one({"_id": id})
            ) is not None:
                return updated_status

    if (existing_status := await db[collection_thermostat_status].find_one({"_id": id})) is not None:
        return existing_status

    raise HTTPException(status_code=404, detail=f"Set point {id} not found")


@app.post("/reset_thermostat_status", response_description="Reset the thermostat status entry.", responses={403: {}, 500: {}})
async def reset_thermostat_status(response: Response):
    drop_thermostat_status = [];
    drop_thermostat_status = await db[collection_thermostat_status].find().to_list(1)
    if drop_thermostat_status != []:
        drop_thermostat_status = await db[collection_thermostat_status].drop()
        if drop_thermostat_status is None:
            return JSONResponse(status_code=200, content=f"The thermostat status entry was successfully reset.")
        else:
            raise HTTPException(status_code=500, detail=f"There was an internal server error resetting the status. Check server logs.")

    raise HTTPException(status_code=403, detail=f"There is currently no thermostat status. POST a new status to /thermostat_status endpoint.")
