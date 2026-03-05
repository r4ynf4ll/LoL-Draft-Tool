import csv
from pathlib import Path

from sqlmodel import Session, delete

from models import Champion, engine

def populate_db():
    """Populate the database with champion data from CSV."""
    csv_path = Path(__file__).with_name("opgg_champions.csv")

    # Parse CSV first so we never wipe existing rows if parsing fails.
    with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        champions: list[Champion] = []

        for row in reader:
            champions.append(
                Champion(
                    champion_name=row["champion_name"],
                    tier_number=int(row["tier_number"]),
                    role=row["role"],
                    winrate=float(row["winrate"].rstrip("%")),
                    pickrate=float(row["pickrate"].rstrip("%")),
                )
            )

    # Replace champion rows only (do not drop other tables).
    with Session(engine) as session:
        session.exec(delete(Champion))
        for champion in champions:
            session.add(champion)
        session.commit()
    
    print(f"Successfully inserted {len(champions)} champions into the database!")

if __name__ == "__main__":
    populate_db()
