from fastapi import FastAPI

from .routers import authors, users

app = FastAPI(title='Book Review API')


@app.get('/')
async def read_root():
    return {'message': 'Welcome to the Book Review API!'}


app.include_router(users.router)
app.include_router(authors.router)
