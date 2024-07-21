import os
import sys
import dotenv
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from pydantic import BaseModel, Field
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime
from utils import get_logger, EncryptionUtils, cacheWrapper
from MW import cacheops

logger = get_logger(__name__)

# All the requests will be prependded with /auth/
auth = APIRouter(
    prefix='/auth',
    tags=['auth']
)

# Secret key and algorithm used in JWT tokens

dotenv_file = dotenv.find_dotenv()
dotenv.load_dotenv(dotenv_file)

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM =  os.environ["ALGORITHM"]

# Configuration used for hashing passwords
encryption = EncryptionUtils()

# Used to authenticate every request used to access todo database for their respective databases
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token',
                                    scheme_name="user_oauth2_schema")
 

# Used for Data validation of our token as to which format our json format of token should be like
class Token(BaseModel):
    access_token: str
    token_type: str

# This is used to authenticate and see if the credentials of user/password-hashed_password exists in the database
# If credentials exist we return the user object which has all the data about the user else return False.
def authenticate_user(username: str, password: str):
    userid = encryption.encrypt(username)
    logger.info("Authenticating user")
    if not password: # If user is None, i.e. there is no user in the database
        logger.warning("User doesn't exist in the database")
        return False
    passwd = os.environ["USER_PASSWD"]
    if not password == encryption.decrypt(passwd): # Checks if the password from the token matches user password from the database 
        logger.warning("Wrong password")
        return False
    return userid

# Creates the access json web token for a standardized way to securely send data between two parties
def create_access_token(user_id: int, expires_delta: timedelta):
    logger.info(f"Creating a jwt token for user id: {user_id}")
    encode = {'id': user_id} # This is the payload information
    expires = datetime.utcnow() + expires_delta # Expiry time of the json token
    encode.update({'exp': expires})
    logger.info(f"Created a jwt token for user: {user_id}")
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM) # We specify the algorithm to encode the json token and the encrypt the json token using secret key, and then pass the payload for the json token

# This function is used to decode jwt and verify if user retreived from the jwt, exists in the database or not.
@cacheWrapper(cacheops)
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get('id') # User_id specified in 'encode' of create_access_token
        username = encryption.encrypt(user_id)
        logger.info(f"Got the jwt payload for user id: {username}")
        if username is None:
            logger.info(f"Could validate credentials of user id: {user_id}, from the database")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate credentials of user')
        
        logger.info(f"Validated the user: {user_id} successfully")
        return {'user': username}
    except JWTError:
        logger.error("JWT error occured")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')


# Verfication of token is done. If the verification is successful then return the token code which is used to transmit the data.
# form_data -> Is the json web token format which has the 
@auth.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    userid = authenticate_user(username=form_data.username, password=form_data.password)
    if not userid:
        logger.warning("User validation unsuccessful")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')
    token = create_access_token(user_id=userid, expires_delta=timedelta(hours=24))
    logger.info(f"Login is successful for user: {encryption.decrypt(userid)}")
    return {'access_token' : token, 'token_type' : 'bearer'}