from sqlmodel import SQLModel, Field, create_engine
from sqlalchemy import Numeric

class Champion(SQLModel, table=True):
    champion_name: str = Field(primary_key=True)
    role: str = Field(primary_key=True)
    tier_number: int
    winrate: float = Field(sa_type=Numeric(10, 2))
    pickrate: float = Field(sa_type=Numeric(10, 2))

class Counter(SQLModel, table=True):
    champion_name: str = Field(primary_key=True)
    role: str = Field(primary_key=True)
    rank: int = Field(primary_key=True)  # 1-10 for top 10 counters
    counter_champion: str
    matchup_winrate: float = Field(sa_type=Numeric(10, 2))

engine = create_engine("sqlite:///league.db", echo=False)

def init_db():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")