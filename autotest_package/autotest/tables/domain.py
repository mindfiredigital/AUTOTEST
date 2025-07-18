from sqlalchemy import Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.database import Base

class Domain(Base):
    __tablename__ = "domain"
    id = Column(Integer, primary_key=True, index=True)
    domain_name = Column(String, unique= True, index=True)

    page = relationship("Page", back_populates="domain")
