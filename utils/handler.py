import time
import asyncio
import argparse
from datetime import datetime, timedelta
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from utils import get_logger

logger = get_logger(__name__)
# immediately after imports

parser = argparse.ArgumentParser()
parser.add_argument('--port', help='port number to run the service on, example: 8000', default=8000)
args = parser.parse_args()

class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app , timeout_seconds: int = 10):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            async with asyncio.timeout(self.timeout_seconds):
                response = await call_next(request)
            return response
        except asyncio.TimeoutError:
            logger.warning(
                f"TimeoutMiddleware: Request timed out after {time.time() - start_time} seconds.",
                extra={"path": request.url.path},
            )
            raise HTTPException(status_code=408, detail="Request timeout")


class RateLimitingMiddleware(BaseHTTPMiddleware):
    # Rate limiting configurations
    RATE_LIMIT_DURATION = timedelta(seconds=10)
    RATE_LIMIT_REQUESTS = 5

    def __init__(self, app):
        super().__init__(app)
        # Dictionary to store request counts for each IP
        self.request_counts = {}

    async def dispatch(self, request, call_next):
        # Get the client's IP address
        client_ip = request.client.host

        # Check if IP is already present in request_counts
        request_count, last_request = self.request_counts.get(client_ip, (0, datetime.min))

        logger.info(f"No. of requests made are : {request_count}. Last request made was on {last_request.strftime("%m/%d/%Y, %H:%M:%S")}")

        # Calculate the time elapsed since the last request
        elapsed_time = datetime.now() - last_request

        if elapsed_time > self.RATE_LIMIT_DURATION:
            # If the elapsed time is greater than the rate limit duration, reset the count
            request_count = 1
        else:
            if request_count >= self.RATE_LIMIT_REQUESTS:
                # If the request count exceeds the rate limit, return a JSON response with an error message
                logger.error(f"Exceeded maximum number of requests made for the duration try again in next {self.RATE_LIMIT_DURATION.seconds}")
                return JSONResponse(
                    status_code=429,
                    content={"message": "Rate limit exceeded. Please try again later."}
                )
            request_count += 1

        # Update the request count and last request timestamp for the IP
        self.request_counts[client_ip] = (request_count, datetime.now())

        # Proceed with the request
        response = await call_next(request)
        return response

class Message(BaseModel):
    message: str

class RequestContextLogMiddleware(BaseHTTPMiddleware):
    async def get_body(self, request: Request) -> bytes:
        body = await request.body()
        # await self.set_body(request, body)
        return body

    # @cache
    async def dispatch(self, request: Request, call_next):
        # await self.set_body(request, request.body())
        body = await self.get_body(request)
        logger.info(f"The {request.method} request accessed by path: {request.url}")
        if request.method == 'POST' or request.method =='PUT':
            logger.info(f"The body of the request is: {body}")
        response = await call_next(request)    
        return response