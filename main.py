from math import sqrt
from fastapi import Depends, FastAPI, File, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from typing import Union
from PIL import Image
import io
import PIL.ImageOps
from pydantic import BaseModel
from datetime import datetime


app = FastAPI()

@app.get("/prime/{number}")
async def is_prime_number(number):
    numbers = range(1, 9223372036854775807)
    flag = 0
    if number.isnumeric():
        number = int(number)
        if (number in numbers):
            if (number > 1):
                for i in range(2, int(sqrt(number)) + 1):
                    if (number % i) == 0:
                        flag = 1
                if (flag == 0):
                    return f'This number is a prime number'
                else:
                    return f'This number is not a prime number'
            else:
                return f'This number is not a prime number'
        else:
            return f'Entered number should be in the range of 1 to 9223372036854775807'
    else:
        return f'It is not a number'

@app.post("/picture/invert")
async def picture(file: bytes = File()):
    getImage = Image.open(io.BytesIO(file))
    inverted_image = PIL.ImageOps.invert(getImage)
    printImage = io.BytesIO()
    inverted_image.save(printImage, "JPEG")
    printImage.seek(0)
    return StreamingResponse(printImage, media_type="image/jpeg")

fake_users_db = {
    "user": {
        "username": "user",
        "full_name": "User",
        "email": "user@example.com",
        "hashed_password": "fakehasheddog123",
        "disabled": False,
    },
}

def fake_hash_password(password: str):
    return "fakehashed" + password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None

class UserInDB(User):
    hashed_password: str

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def fake_decode_token(token):
    user = get_user(fake_users_db, token)
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    user = UserInDB(**user_dict)
    hashed_password = fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    return {"access_token": user.username, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@app.get("/time")
async def get_time(current_user: User = Depends(get_current_user)):
    return datetime.now().strftime("%H:%M:%S")
