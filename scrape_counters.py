import csv
import re
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup


OUTPUT_CSV = Path(__file__).with_name("counter_data.csv")
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# Map roles to op.gg URL format
ROLE_MAP = {
	"TOP": "top",
	"JUNGLE": "jungle",
	"MID": "mid",
	"ADC": "adc",
	"SUPPORT": "support",
}


def fetch_counter_data(champion: str, role: str) -> Optional[list[dict[str, str]]]:
	"""Fetch top 10 counters for a champion/role from op.gg"""
	# op.gg URL format: /lol/champions/{champion}/counters/{role}
	# Champion names with spaces/special chars: spaces and ' are removed
	# e.g. "Bel'Veth" -> "belveth", "Aureliion Sol" -> "aurelionsol"
	role_key = ROLE_MAP.get(role.upper(), role.lower())
	champion_url = champion.lower().replace(" ", "").replace("'", "").replace(".", "")
	url = f"https://op.gg/lol/champions/{champion_url}/counters/{role_key}"
	
	try:
		response = requests.get(url, headers=HEADERS, timeout=30)
		response.raise_for_status()
	except requests.RequestException as e:
		print(f"Error fetching {champion} {role}: {e}")
		return None
	
	try:
		soup = BeautifulSoup(response.text, 'html.parser')
		
		counters = []
		
		# Find the div containing all counter data
		target_text = None
		for div in soup.find_all('div'):
			text = div.get_text()
			# Look for divs that include both champion matchup info and multiple counter names with winrates
			if 'Win rate' in text and 'Games' in text:
				target_text = text
				break
		
		if not target_text:
			print(f"Could not find counter data for {champion} {role}")
			return None
		
		# The format is all in one line: "...Search a championWin rateGamesLee Sin54.42%147Viego55.86%145..."
		# Extract the counter list part (after "Games" label)
		
		# Find where the actual counter list starts
		# Look for "Search a championWin rateGames" then the first champion
		games_idx = target_text.rfind('Games')  # Get the last "Games" (the header)
		if games_idx == -1:
			print(f"Could not find 'Games' header for {champion} {role}")
			return None
		
		counter_text = target_text[games_idx + 5:]  # Skip "Games"
		
		# Parse pattern: "ChampionName Winrate% Games ..."
		# regex:  ChampionName (one or more words, letters, spaces, apostrophes) + digits.digits% + digits
		pattern = r'([A-Za-z\s&\'\.]+?)(\d+\.\d+)%(\d+)'
		
		matches = re.findall(pattern, counter_text)
		
		if not matches:
			print(f"Could not parse counters for {champion} {role}")
			return None
		
		parsed_rows: list[tuple[str, float]] = []

		# Parse candidate rows. We capture more than 10, then sort by winrate.
		for counter_name, winrate_str, games_str in matches[:25]:
			counter_name = counter_name.strip()
			
			# Validate: must be at least 2 chars, not start with digit
			if len(counter_name) < 2 or counter_name[0].isdigit():
				continue
			
			# Skip obvious non-champion text (stat labels, UI text)
			skip_keywords = ['rate', 'pick', 'ban', 'damage', 'kda', 'participation', 'win', 'lane', 'search', 'tier', 'role', 'games']
			if any(skip in counter_name.lower() for skip in skip_keywords):
				continue
			
			# Make sure it has a valid win rate
			try:
				winrate = float(winrate_str)
			except ValueError:
				continue
			
			parsed_rows.append((counter_name, winrate))

		# Rank by highest matchup win rate and keep top 10.
		for rank, (counter_name, winrate) in enumerate(
			sorted(parsed_rows, key=lambda row: row[1], reverse=True)[:10],
			start=1,
		):
			counters.append(
				{
					"champion_name": champion,
					"role": role,
					"counter_champion": counter_name,
					"matchup_winrate": f"{winrate:.2f}%",
					"rank": rank,
				}
			)
		
		return counters if counters else None
		
	except Exception as e:
		print(f"Error parsing data for {champion} {role}: {e}")
		return None


def get_champions_from_csv(csv_path: str = "opgg_champions.csv") -> list[tuple[str, str]]:
	"""Extract unique champion/role pairs from the existing CSV"""
	champions = set()
	try:
		with open(csv_path, "r") as f:
			reader = csv.DictReader(f)
			for row in reader:
				champions.add((row['champion_name'], row['role']))
		return sorted(list(champions))
	except FileNotFoundError:
		print(f"CSV file {csv_path} not found")
		return []


def main() -> None:
	champions = get_champions_from_csv()
	
	if not champions:
		print("No champions found in CSV. Run scrape.py first.")
		return
	
	all_counters = []
	
	print(f"Fetching counter data for {len(champions)} champion/role combinations...")
	for i, (champion, role) in enumerate(champions, 1):
		print(f"[{i}/{len(champions)}] Fetching {champion} {role}...", end=" ", flush=True)
		
		counters = fetch_counter_data(champion, role)
		if counters:
			all_counters.extend(counters)
			print(f"✓ ({len(counters)} counters)")
		else:
			print("✗ (no data)")
	
	# Write to CSV
	if all_counters:
		OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
		with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
			writer = csv.DictWriter(
				f,
				fieldnames=['champion_name', 'role', 'counter_champion', 'matchup_winrate', 'rank']
			)
			writer.writeheader()
			writer.writerows(all_counters)
		print(f"\nWrote {len(all_counters)} counter records to {OUTPUT_CSV}")
	else:
		print("\nNo counter data fetched!")


if __name__ == "__main__":
	main()
