from fastapi import FastAPI

from .routers import users

app = FastAPI(title='Book Review API')


@app.get('/')
async def read_root():
    return {'message': 'Welcome to the Book Review API!'}


app.include_router(users.router)
