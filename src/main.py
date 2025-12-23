import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.routers import follows, notifications

from .routers import (
    authors,
    comments,
    posts,
    reactions,
    reports,
    sessions,
    users,
)

app = FastAPI(title='Book Review API')


@app.get('/')
async def read_root():
    return {'message': 'Welcome to the Book Review API!'}


app.include_router(users.router)
app.include_router(authors.router)
app.include_router(posts.router)
app.include_router(sessions.router)
app.include_router(follows.router)
app.include_router(comments.router)
app.include_router(reactions.router)
app.include_router(reports.router)
app.include_router(notifications.router)

# BASE_DIR = thư mục BOOKREVIEW_SERVER (project root)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Mount static
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


# @app.middleware('http')
# async def disable_static_cache(request: Request, call_next):
#     response: Response = await call_next(request)

#     # nếu chỉ muốn áp dụng cho static
#     if request.url.path.startswith('/static/'):
#         # xóa ETag nếu có
#         if 'etag' in response.headers:
#             del response.headers['etag']

#         # set no-cache
#         response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
#         response.headers['Pragma'] = 'no-cache'
#         response.headers['Expires'] = '0'

#     return response


# @app.middleware('http')
# async def disable_static_cache(request: Request, call_next):
#     response: Response = await call_next(request)

#     if request.url.path.startswith('/static/'):
#         # Ngăn conditional cache -> tránh 304
#         for h in ('etag', 'last-modified'):
#             if h in response.headers:
#                 del response.headers[h]

#         # Tắt cache trình duyệt
#         response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
#         response.headers['Pragma'] = 'no-cache'
#         response.headers['Expires'] = '0'

#     return response

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=['*'],  # ✅ cho web chạy ngay
#     allow_credentials=False,
#     allow_methods=['*'],
#     allow_headers=['*'],
# )
