import json
import os
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from database import engine

Base = declarative_base()

class PlantMaster(Base):
    __tablename__ = "gap_plant_master"
    id = Column(Integer, primary_key=True, index=True)
    WERKS = Column(String, index=True)
    plant_id = Column(String)
    LAND1 = Column(String)
    PLANT_TYPE = Column(String)
    STRATEGIC_FLAG = Column(String)
    MAX_CAPACITY_HL = Column(Float)
    CURRENT_OCCUPANCY_PCT = Column(Float)

class SKUMaster(Base):
    __tablename__ = "gap_sku_master"
    id = Column(Integer, primary_key=True, index=True)
    sku_id = Column(String, index=True)
    material_type = Column(String)
    source_model = Column(String)
    SHELF_LIFE_DAYS = Column(Integer)
    shelf_life_days = Column(Integer)
    MIN_FRESHNESS_THRESHOLD = Column(Integer)

class ExtendedSTO(Base):
    __tablename__ = "gap_stos"
    id = Column(Integer, primary_key=True, index=True)
    sto_id = Column(String, unique=True, index=True)
    source_location = Column(String)
    destination_location = Column(String)
    sku_id = Column(String)
    quantity = Column(Float)
    creation_date = Column(String)
    COUNTRY_CODE = Column(String)
    VOLUME_HL = Column(Float)
    movement_type = Column(String)
    is_pre_goods_issue = Column(Boolean)
    CONFIDENCE_SCORE = Column(Float)

class SalesOrder(Base):
    __tablename__ = "gap_sales_orders"
    id = Column(Integer, primary_key=True, index=True)
    so_number = Column(String, index=True)
    so_item = Column(String)
    customer_number = Column(String)
    material_number = Column(String)
    assigned_plant = Column(String)
    optimal_plant = Column(String)
    is_optimal_allocation = Column(Boolean)
    quantity_hl = Column(Float)
    country_code = Column(String)
    order_date = Column(Date)
    planned_gi_date = Column(Date)
    allocation_efficiency_score = Column(Float)


def migrate_data():
    # Clean up existing tables to ensure schema updates apply
    try:
        PlantMaster.__table__.drop(engine, checkfirst=True)
        SKUMaster.__table__.drop(engine, checkfirst=True)
        ExtendedSTO.__table__.drop(engine, checkfirst=True)
        SalesOrder.__table__.drop(engine, checkfirst=True)
    except Exception as e:
        print(f"Drop error ignores: {e}")
        
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Clean up existing data to avoid unique constraint violations
    db.execute(PlantMaster.__table__.delete())
    db.execute(SKUMaster.__table__.delete())
    db.execute(ExtendedSTO.__table__.delete())
    db.execute(SalesOrder.__table__.delete())
    db.commit()
    
    data_dir = "../data/synthetic/gap_extended"
    
    # 1. Plants
    with open(os.path.join(data_dir, "plant_country_master.json"), "r") as f:
        plants = json.load(f)
        for p in plants:
            db_obj = PlantMaster(**p)
            db.add(db_obj)
            
    # 2. SKUs
    with open(os.path.join(data_dir, "sku_master_extended.json"), "r") as f:
        skus = json.load(f)
        for s in skus:
            s_clean = {k: v for k, v in s.items() if k != "sourcing_plants"}
            db_obj = SKUMaster(**s_clean)
            db.add(db_obj)
            
    # 3. STOs
    with open(os.path.join(data_dir, "incoming_stos_extended.json"), "r") as f:
        stos = json.load(f)
        for s in stos:
            db_obj = ExtendedSTO(**s)
            db.add(db_obj)
            
    # 4. SOs
    with open(os.path.join(data_dir, "customer_orders.json"), "r") as f:
        sos = json.load(f)
        for s in sos:
            s_dict = dict(s)
            s_dict["order_date"] = datetime.strptime(s_dict["order_date"], "%Y-%m-%d").date()
            s_dict["planned_gi_date"] = datetime.strptime(s_dict["planned_gi_date"], "%Y-%m-%d").date()
            db_obj = SalesOrder(**s_dict)
            db.add(db_obj)
            
    db.commit()
    db.close()
    
    print("Successfully migrated Gap Extended synthetic data to Database!")

if __name__ == "__main__":
    migrate_data()
