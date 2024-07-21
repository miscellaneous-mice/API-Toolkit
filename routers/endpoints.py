# from models import Shows
import os
import sys
import time
from typing import Annotated, Optional
from starlette import status
from fastapi import HTTPException, APIRouter, Path, Query, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor

from auth import get_current_user
from utils import sp_l, get_logger
from services import Calculations

cal = Calculations()

security = HTTPBearer()

user_dependency = Annotated[dict, Depends(get_current_user)]

api = APIRouter(
    prefix='/test',
    tags=['Test Queries']
)

class JSON(BaseModel):
    data: str

class Fact(BaseModel):
    low: int = Field(ge=1)
    high: int = Field(lt=100000)

    class Config:
        json_schema_extra = {
                'example' : {
                    'low' : 20000,
                    'high' : 20100
                }
        }

class SQL(BaseModel):
    columns : Optional[str] = Field(default='*',
                                  description='columns: Transaction ID, Timestamp, Sender Name, Sender UPI ID, Receiver Name, Receiver UPI ID, Amount, Status')
    filter_by : Optional[str] = Field(default='', description='column: operator (>, <, =)')
    class Config:
        json_schema_extra = {
                'example' : {
                    'columns' : 'Transaction ID, Timestamp, Sender Name, Sender UPI ID, Receiver Name, Receiver UPI ID, Amount, Status',
                    'filter_by' : "Amount > 500, Status = 'SUCCESS'"
                }
        }


class Emoji(BaseModel):
    emoji_1: str = Field(title='First emoji', description='Specify the 1st emoji', min_length=2, max_length=10)
    emoji_2: str = Field(title='Second emoji', description='Specify the 2nd emoji', min_length=2, max_length=10)
    emoji_3: str = Field(title='Third emoji', description='Specify the 3rd emoji', min_length=2, max_length=10)

    class Config:
        json_schema_extra = {
                'example' : {
                    'emoji_1' : '(*.*)',
                    'emoji_2' : '(^_^)',
                    'emoji_3' : '(-_-)'
                }
        }


@api.get("/", status_code=status.HTTP_200_OK)
async def sample_get():
    return "Just testing some code"

@api.post("/performance", status_code=status.HTTP_200_OK)
async def sample_factorial(inputs: Fact):
    input_range = inputs.model_dump()
    start = time.time()
    print("Computing.....")
    for x in range(input_range['low'], input_range['high']):
        cal.factorial(x)
    end = time.time()
    return f"Execution time: {end - start}"

@api.get("/processing", status_code=status.HTTP_200_OK)
async def sample_factorial(process_type: str = Query(..., description='multiprocessing/multithreading')):
    start = time.time()
    print("Computing.....")
    await cal.interpolate(process_type=process_type)
    end = time.time()
    return f"Execution time for {process_type} : {end - start}"


@api.post("/add", status_code=status.HTTP_201_CREATED)
async def sample_post(json: JSON)-> JSONResponse: 
    data_model = json.model_dump()
    return JSONResponse( 
         status_code=status.HTTP_200_OK, 
         content={"detail": str(data_model)}, 
     )

@api.get("/testauth", status_code=status.HTTP_200_OK)
async def get_owner_id(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, details='Authentication Failed')
    return user

@api.post("/emojis/{loop}", status_code=status.HTTP_200_OK)
async def heavy_compute(emoji: Emoji, chunk: int = Query(default=10, gt=0, le=50), loop: int = Path(description='Minimum number of loops is 100', gte=100)):
    emojis = {i: v for i, v in enumerate(emoji.model_dump().values())}
    data = list(range(loop))
    with ProcessPoolExecutor(5) as executor:
        executor.map(cal.expressions, repeat(emojis), sp_l(data, chunk))

@api.post("/getdata", status_code=status.HTTP_200_OK)
async def heavy_compute(sql: SQL, num_of_records: int = Query(default=10, gt=0)):
    cols = sql.columns
    cond = sql.filter_by
    data = await cal.get_data_from_postgres(columns=cols, conditions=cond, num_of_records=num_of_records)
    return data

@api.get("/whoami")
def read_current_user(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]):
    return {"scheme": credentials.scheme, "credentials": credentials.credentials}