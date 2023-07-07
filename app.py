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


@app.get("/", response_description="Display entire thermostat status and set points / schedule.")
async def list_full_status():
    full_status = {}
    thermostat_status = await db[collection_thermostat_status].find().to_list(2)
    thermostat_setpoints = await db[collection_setpoints].find().to_list(5)
    json_status = jsonable_encoder(thermostat_status)
    json_setpoints = jsonable_encoder(thermostat_setpoints)
    full_status["thermostat_status"] = json_status
    full_status["setpoints"] = json_setpoints
    return full_status


@app.post("/schedule", response_description="Add new schedule temperature set point", response_model=ScheduleModel)
async def create_setpoint(setpoint: ScheduleModel = Body(...)):
    setpoint = jsonable_encoder(setpoint)
    new_setpoint = await db[collection_setpoints].insert_one(setpoint)
    created_setpoint = await db[collection_setpoints].find_one({"_id": new_setpoint.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_setpoint)


@app.get(
    "/schedule", response_description="List all setpoints", response_model=List[ScheduleModel]
)
async def list_setpoints():
    setpoints = await db[collection_setpoints].find().to_list(1000)
    return setpoints


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
    "/thermostat_status", response_description="List the current thermostat system status", response_model=List[ThermostatStatusModel]
)
async def list_thermostat_status():
    thermostat_status = await db[collection_thermostat_status].find().to_list(1000)
    return thermostat_status


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


@app.post("/reset_thermostat_status", response_description="Reset the thermostat status entry.")
async def reset_thermostat_status():
    drop_thermostat_status = [];
    drop_thermostat_status = await db[collection_thermostat_status].find().to_list(1)
    if drop_thermostat_status != []:
        drop_thermostat_status = await db[collection_thermostat_status].drop()
        if drop_thermostat_status is None:
            return JSONResponse(status_code=200, content=f"The thermostat status entry was successfully reset.")
        else:
            raise HTTPException(status_code=500, detail=f"There was an internal server error resetting the status. Check server logs.")

    raise HTTPException(status_code=403, detail=f"There is currently no thermostat status. POST a new status to /thermostat_status endpoint.")
