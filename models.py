from sqlmodel import SQLModel, Field, Session, create_engine
from sqlalchemy import Numeric, text

class Champion(SQLModel, table=True):
    champion_name: str = Field(primary_key=True)
    role: str = Field(primary_key=True)
    tier_number: int
    winrate: float = Field(sa_type=Numeric(10, 2))
    pickrate: float = Field(sa_type=Numeric(10, 2))

class Counter(SQLModel, table=True):
    champion_name: str = Field(primary_key=True)
    role: str = Field(primary_key=True)
    matchup_type: str = Field(primary_key=True)  # strong_against or weak_against
    rank: int = Field(primary_key=True)  # 1-10 for top 10 counters
    counter_champion: str
    matchup_winrate: float = Field(sa_type=Numeric(10, 2))

engine = create_engine("sqlite:///league.db", echo=False)

def init_db():
    """Create all database tables."""
    # Lightweight migration for existing SQLite DBs created before matchup_type existed.
    with Session(engine) as session:
        table_exists = session.exec(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='counter'")
        ).first()
        if table_exists:
            columns = session.exec(text("PRAGMA table_info(counter)")).all()
            column_names = {str(col[1]) for col in columns}
            if "matchup_type" not in column_names:
                session.exec(text("DROP TABLE counter"))
                session.commit()

    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!")