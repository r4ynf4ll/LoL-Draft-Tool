from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from models import Champion, Counter, engine, init_db

app = FastAPI()


@app.on_event("startup")
def startup() -> None:
    init_db()

@app.get("/champ_stats")
def get_champstats(champion: str, role: str) -> dict[str, object] | dict[str, str]:
    with Session(engine) as session:
        statement = (
            select(Champion)
            .where(Champion.champion_name == champion)
            .where(Champion.role == role)
        )
        result = session.exec(statement).first()
    if not result:
        return {"error": "Champion not found"}
    return {
        "champion_name": result.champion_name,
        "role": result.role,
        "tier_number": result.tier_number,
        "winrate": float(result.winrate),
        "pickrate": float(result.pickrate),
    }


@app.get("/counters")
def get_counters(
    champion: str,
    role: str,
    matchup_type: str | None = None,
) -> list[dict[str, object]] | dict[str, str]:
    with Session(engine) as session:
        statement = (
            select(Counter)
            .where(Counter.champion_name == champion)
            .where(Counter.role == role)
        )
        if matchup_type:
            statement = statement.where(Counter.matchup_type == matchup_type)
        statement = statement.order_by(Counter.rank)
        results = session.exec(statement).all()

    if not results:
        return {"error": "No counters found"}

    return [
        {
            "champion_name": result.champion_name,
            "role": result.role,
            "matchup_type": result.matchup_type,
            "rank": result.rank,
            "counter_champion": result.counter_champion,
            "matchup_winrate": float(result.matchup_winrate),
        }
        for result in results
    ]


app.mount("/", StaticFiles(directory="static", html=True), name="static")