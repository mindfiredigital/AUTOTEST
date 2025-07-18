from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base
from datetime import datetime
from zoneinfo import ZoneInfo

def get_local_time():
    return datetime.now(ZoneInfo("Asia/Kolkata"))

class Redirect(Base):
    __tablename__ = "redirect"
    id = Column(Integer, primary_key=True, index=True)
    page_url = Column(String, ForeignKey("page.page_url"))
    event_selector = Column(String)  # e.g., "a[href='/home']"
    redirected_url = Column(String)
    event_description = Column(String)
    verified = Column(Boolean, default= True)
    timestamp = Column(DateTime, default=get_local_time)
    
    page = relationship("Page", back_populates="redirect")