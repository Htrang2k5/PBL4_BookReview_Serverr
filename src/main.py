from fastapi import FastAPI

from .routers import authors, posts, sessions, users

app = FastAPI(title='Book Review API')


@app.get('/')
async def read_root():
    return {'message': 'Welcome to the Book Review API!'}


app.include_router(users.router)
app.include_router(authors.router)
app.include_router(posts.router)
app.include_router(sessions.router)
