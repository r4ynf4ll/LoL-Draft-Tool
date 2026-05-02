from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from models import Champion, engine, init_db

app = FastAPI()


@app.on_event("startup")
def startup() -> None:
	init_db()

@app.get("/champ_stats")
def get_champstats(champion: str):
    with Session(engine) as session:
        statement = (
            select(Champion)
            .where(Champion.champion_name == champion)
            .order_by(Champion.role)
        )
        results = session.exec(statement).all()
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

app.mount("/", StaticFiles(directory="static", html=True), name="static")