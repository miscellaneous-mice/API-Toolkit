import time
import os
import sys
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.gzip import GZipMiddleware

from utils import RateLimitingMiddleware, RequestContextLogMiddleware, TimeoutMiddleware
from utils import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Netflix Search", description="My First API with FastAPI")

@app.on_event("startup")
async def startup():
    logger.info("starting the service")


@app.on_event("shutdown")
async def shutdown():
    logger.info("shutting down the service")

app.add_middleware(TimeoutMiddleware)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(f"The request took {process_time} duration")
    return response


app.add_middleware(RateLimitingMiddleware)
app.add_middleware(RequestContextLogMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.exception_handler(HTTPException)
async def http_exception_handler( 
     request: Request, exc: HTTPException
 ) -> JSONResponse: 
     logger.error(f"Inside http_exception_handler due to invalid authentication")
     return JSONResponse( 
         status_code=status.HTTP_401_UNAUTHORIZED, 
         content={"detail": str(exc.detail)}, 
     ) 

@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler( 
     request: Request, exc: RequestValidationError 
 ) -> JSONResponse: 
     logger.error(f"Inside request_validation_exception_handler as request contains invalid data")
     return JSONResponse( 
         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
         content={"detail": jsonable_encoder(exc.errors())}, 
     ) 