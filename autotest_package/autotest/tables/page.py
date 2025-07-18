from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base
from datetime import datetime
from zoneinfo import ZoneInfo

def get_local_time():
    return datetime.now(ZoneInfo("Asia/Kolkata"))

class Page(Base):
    __tablename__ = "page"
    domain_id = Column(Integer, ForeignKey("domain.id"))
    page_url = Column(String, primary_key=True, index=True)
    page_title = Column(String)
    page_source = Column(Text)
    page_metadata = Column(JSON) 
    test_cases = Column(JSON)
    test_cases_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=get_local_time , onupdate=get_local_time)

    domain = relationship("Domain", back_populates="page")
    test_case = relationship("TestCase", back_populates="page")
    redirect = relationship("Redirect", back_populates="page")