from fastapi import APIRouter
from sqlalchemy import func

from src.database import DBSession
from src.models import PostReport, session

router = APIRouter(prefix='/reports', tags=['Reactions'])


# CRUD
def get_reports_by_post_id(db: DBSession, post_id: int):
    reports = db.query(PostReport).filter(PostReport.post_id == post_id).all()
    return reports
