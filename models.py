from sqlmodel import SQLModel, Field, create_engine
from sqlalchemy import Numeric

class Champion(SQLModel, table=True):
    champion_name: str = Field(primary_key=True)
    role: str = Field(primary_key=True)
    tier_number: int
    winrate: float = Field(sa_type=Numeric(10, 2))
    pickrate: float = Field(sa_type=Numeric(10, 2))

engine = create_engine("sqlite:///league.db", echo=False)

def init_db():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)