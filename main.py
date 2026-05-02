from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from models import Champion, engine, init_db, Counter

app = FastAPI()


@app.on_event("startup")
def startup() -> None:
	init_db()

@app.get("/champ_stats")
def get_champstats(champion: str, role: str):
    with Session(engine) as session:
        statement = (
            select(Champion)
            .where(Champion.champion_name == champion)
            .where(Champion.role == role)
        )
        results = session.exec(statement).first()
        if results:
            return [
                {
                    "champion_name": result.champion_name,
                    "role": result.role,
                    "tier_number": result.tier_number,
                    "winrate": result.winrate,
                    "pickrate": result.pickrate,
                }
                for result in results
            ]
        return {"error": "Champion not found"}
    
@app.get("/counters")
def get_counters(champion: str, role: str):
     with Session(engine) as session:
          statement = (
            select(Counter)
            .where(Counter.champion_name == champion)
            .where(Counter.role == role)
            .order_by(Counter.rank)
        )
          results = session.exec(statement).all()
          if results:
               return [
                    {
                         "champion_name": result.champion_name,
                         "role": result.role,
                         "rank": result.rank,
                         "counter_champion": result.counter_champion,
                         "matchup_winrate": result.matchup_winrate,
                    }
                    for result in results
               ]
          return {"error": "No counters found"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")