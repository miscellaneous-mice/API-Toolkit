import os
import sys
import uvicorn

homedir = os.getcwd()
sys.path.append(homedir)

from routers import api
from auth import auth
from MW import app
from utils import args

app.include_router(api)
app.include_router(auth)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=int(args.port))
