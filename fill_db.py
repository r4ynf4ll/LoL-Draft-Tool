import csv
from sqlmodel import Session
from models import Champion, engine, SQLModel

def populate_db():
    """Populate the database with champion data from CSV."""
    # Clear existing data and recreate tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    
    # Read CSV and insert into database
    with open("opgg_champions.csv", "r") as csvfile:
        reader = csv.DictReader(csvfile)
        champions = []
        
        for row in reader:
            champion = Champion(
                champion_name=row["champion_name"],
                tier_number=int(row["tier_number"]),
                role=row["role"],
                winrate=float(row["winrate"].rstrip("%")),
                pickrate=float(row["pickrate"].rstrip("%"))
            )
            champions.append(champion)
        
        # Insert all at once
        with Session(engine) as session:
            for champion in champions:
                session.add(champion)
            session.commit()
    
    print(f"Successfully inserted {len(champions)} champions into the database!")

if __name__ == "__main__":
    populate_db()
