# SpotifyToken table

from sqlalchemy import Column, Integer, String, DateTime
from backend.auth.db import Base
import datetime


class SpotifyToken(Base):
    __tablename__ = 'spotify_tokens'

    id = Column(Integer, primary_key=True)
    spotify_user_id = Column(String, unique=True, nullable=False)
    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)