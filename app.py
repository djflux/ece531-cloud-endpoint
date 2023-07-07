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
collection_status = "status"

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
                "current": "false"
            }
        }


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
