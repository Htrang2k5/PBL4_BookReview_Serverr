import os
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from .routers import authors, posts, users

app = FastAPI(title='Book Review API')

STATIC_DIR = os.path.join(os.path.dirname(__file__), '..', 'static')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
os.makedirs(IMAGES_DIR, exist_ok=True)

UPLOAD_FILE_PARAM = File(...)


@app.get('/')
async def read_root():
    return {'message': 'Welcome to the Book Review API!'}


app.include_router(users.router)
app.include_router(authors.router)
app.include_router(posts.router)

# mount static files
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


@app.post('/upload-image')
async def upload_image(file: UploadFile = UPLOAD_FILE_PARAM):
    # 1. Check loại file
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, detail='File upload không phải là ảnh'
        )

    # 2. Tạo tên file mới cho unique
    ext = file.filename.split('.')[-1]
    filename = f'{uuid4().hex}.{ext}'

    # 3. Đường dẫn lưu file
    file_path = os.path.join(IMAGES_DIR, filename)

    # 4. Lưu file
    with open(file_path, 'wb') as f:
        f.write(await file.read())

    # 5. Trả về URL để frontend dùng
    file_url = f'/static/images/{filename}'
    return {'filename': filename, 'url': file_url}
