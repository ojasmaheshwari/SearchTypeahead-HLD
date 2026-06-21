from sqlalchemy import Column, String, BigInteger, DateTime, func
from .database import Base

class Search(Base):
    __tablename__ = "searches"

    query = Column(String(255), primary_key=True, index=True)
    count = Column(BigInteger, nullable=False, default=1)
    last_searched = Column(DateTime, server_default=func.now(), onupdate=func.now())
