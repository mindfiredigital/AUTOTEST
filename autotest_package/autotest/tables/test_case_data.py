from sqlalchemy import Column, Integer, ForeignKey, Text, String, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base
from datetime import datetime
from zoneinfo import ZoneInfo

def get_local_time():
    return datetime.now(ZoneInfo("Asia/Kolkata"))

class TestCase(Base):
    __tablename__ = "test_case_data"
    id = Column(Integer, primary_key=True, index=True)
    page_url = Column(String, ForeignKey("page.page_url"))
    test_case_name = Column(String)
    test_case_type = Column(String)
    test_case = Column(JSON)  # JSON string
    test_script = Column(Text)
    script_path = Column(String)
    timestamp = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    page = relationship("Page", back_populates="test_case")