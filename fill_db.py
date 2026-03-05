import csv
from sqlmodel import Session
from models import Champion, engine, SQLModel

def populate_db():
    """Populate the database with champion data from the CSV file."""
    
    with open('opgg_champions.csv', 'r') as file:
        reader = csv.DictReader(file)
        with Session(engine) as session:
            for row in reader:
                winrate = (row['winrate'].rstrip('%'))
                champion = Champion(
                    champion_name=row['champion_name'],
                    tier_number=int(row['tier_number']),
                    role=row['role'],
                    winrate=float(winrate),
                    pickrate=float(row['pickrate'].rstrip('%'))
                )
                session.add(champion)
            
            session.commit()
            print("Database populated successfully!")

if __name__ == "__main__":
    populate_db()
