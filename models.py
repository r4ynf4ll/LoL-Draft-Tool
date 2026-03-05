from decimal import Decimal
from sqlmodel import SQLModel, Field, create_engine
from sqlalchemy import Column, Float

class Champion(SQLModel, table=True):
    champion_name: str = Field(default=None, primary_key=True)
    role: str = Field(default=None, primary_key=True)
    tier_number: int = Field(default=None)
    winrate: float = Field(default=None, sa_column=Column(Float))
    pickrate: float = Field(default=None, sa_column=Column(Float))

engine = create_engine('sqlite:///league.db')
SQLModel.metadata.create_all(engine)