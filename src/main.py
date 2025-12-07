import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.routers import follows

from .routers import authors, posts, sessions, users

app = FastAPI(title='Book Review API')


@app.get('/')
async def read_root():
    return {'message': 'Welcome to the Book Review API!'}


app.include_router(users.router)
app.include_router(authors.router)
app.include_router(posts.router)
app.include_router(sessions.router)
app.include_router(follows.router)

# BASE_DIR = thư mục BOOKREVIEW_SERVER (project root)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Mount static
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
