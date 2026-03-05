import csv
from collections import defaultdict
from pathlib import Path

from sqlmodel import Session, delete

from models import Counter, engine, init_db


def populate_counters_db():
	"""Populate Counter table from CSV using top 10 highest matchup win rates."""
	init_db()
	csv_path = Path(__file__).with_name("counter_data.csv")

	# Read and group by champion/role so we can rank by matchup_winrate.
	grouped: dict[tuple[str, str], list[dict[str, str | float]]] = defaultdict(list)
	with csv_path.open("r", encoding="utf-8", newline="") as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			winrate = float(row["matchup_winrate"].rstrip("%"))
			key = (row["champion_name"], row["role"])
			grouped[key].append(
				{
					"counter_champion": row["counter_champion"],
					"matchup_winrate": winrate,
				}
			)

	# Build final rows: top 10 per champion/role by highest winrate.
	counters: list[Counter] = []
	for (champion_name, role), rows in grouped.items():
		sorted_rows = sorted(rows, key=lambda r: float(r["matchup_winrate"]), reverse=True)
		for idx, row in enumerate(sorted_rows[:10], start=1):
			counters.append(
				Counter(
					champion_name=champion_name,
					role=role,
					counter_champion=str(row["counter_champion"]),
					matchup_winrate=float(row["matchup_winrate"]),
					rank=idx,
				)
			)

	# Replace only Counter rows; leave Champion rows untouched.
	with Session(engine) as session:
		session.exec(delete(Counter))
		for counter in counters:
			session.add(counter)
		session.commit()

	print(f"Successfully inserted {len(counters)} counter records into the database!")


if __name__ == "__main__":
	populate_counters_db()
