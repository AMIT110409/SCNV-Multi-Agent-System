from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class STORecord(Base):
    """
    SQLAlchemy model representing a Stock Transfer Order (STO) event
    stored in the Memory Layer (PostgreSQL).
    """
    __tablename__ = "sto_records"

    id = Column(Integer, primary_key=True, index=True)
    sto_id = Column(String, unique=True, index=True)
    source_location = Column(String, index=True)
    destination_location = Column(String, index=True)
    sku_id = Column(String, index=True)
    quantity = Column(Float)
    creation_date = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Classification Results
    classification = Column(String, nullable=True) # PRODUCTIVE vs UNPRODUCTIVE
    rule_applied = Column(Integer, nullable=True)
    root_cause = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    reasoning_text = Column(String, nullable=True)
    
    # Action Status
    human_approved = Column(Boolean, nullable=True) # Null=Pending, True=Approved, False=Rejected
    executed_in_sap = Column(Boolean, default=False)
    
# In Phase 1, we define the schema but don't strictly require a running DB
# yet, as we are mainly testing the Python logic. Phase 2/3 will dockerize PG.
# engine = create_engine("postgresql://user:pass@localhost/scnv")
# Base.metadata.create_all(bind=engine)
