from fastapi import FastAPI, Depends
import bcrypt
import databases
import sqlalchemy
from sqlalchemy import create_engine, Column, String
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

""" Database Configuration"""

DATABASE_URL = "sqlite:///./test.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    Column("id", sqlalchemy.Integer, primary_key=True, index=True),
    Column("username", String, unique=True, index=True),
    Column("hashed_password", String),
)

engine = create_engine(DATABASE_URL)
metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get a database connection
async def get_db():
    async with database.transaction():
        yield database



app.add_middleware(CORSMiddleware,
                   allow_origins=["*"],
                   allow_credentials=True,
                   allow_headers=["*"],
                   allow_methods=["*"], )


class User(BaseModel):
    """ Schema to validate user payload
    """
    username: str
    password: str



""" Api configuration """

def hash_password(password: str) -> str:
    """ Hash user password to store in database
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed__password: str) -> bool:
    """ Verify User password
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed__password.encode('utf-8'))


@app.post("/register")
async def register(user: User, db: databases.Database = Depends(get_db)):
    """ Register User to database
    """
    hashed_password = hash_password(user.password)

    try:
        query = users.insert().values(username=user.username, hashed_password=hashed_password)
        await db.execute(query)
    except:
        return {"message": "User Already Existed"}
    return {"message": "User Registered Successfully"}


@app.post("/login")
async def login(user_schema: User, db: databases.Database = Depends(get_db)):
    """ Login User
    """
    query = users.select().where(users.c.username == user_schema.username)
    user = await db.fetch_one(query)

    if user and verify_password(user_schema.password, user.hashed_password):
        return {"message": "User Logged In Successfully"}
    else:
        return {"message": "Invalid Credentials, Please Retry"}


if __name__ == "__main__":
    uvicorn.run('main:app', host="0.0.0.0", port=8000, log_level="debug", reload=True)