import csv
import re
from pathlib import Path

import requests


URL = "https://op.gg/lol/champions"
OUTPUT_CSV = Path(__file__).with_name("opgg_champions.csv")


def fetch_champion_rows(url: str = URL) -> list[dict[str, str]]:
	response = requests.get(
		url,
		headers={
			"User-Agent": (
				"Mozilla/5.0 (X11; Linux x86_64) "
				"AppleWebKit/537.36 (KHTML, like Gecko) "
				"Chrome/124.0.0.0 Safari/537.36"
			)
		},
		timeout=30,
	)
	response.raise_for_status()

	pattern = re.compile(
		r'\\"key\\":\\"(?P<key>[^\\"]+)\\",'
		r'\\"name\\":\\"(?P<name>[^\\"]+)\\",'
		r'\\"image_url\\":\\"[^\\"]+\\",'
		r'\\"positionName\\":\\"(?P<role>[^\\"]+)\\",'
		r'\\"positionWinRate\\":(?P<win>[0-9.]+),'
		r'\\"positionPickRate\\":(?P<pick>[0-9.]+)'
		r'.*?\\"positionRank\\":(?P<rank>\d+)',
		re.DOTALL,
	)

	seen: set[tuple[str, str]] = set()
	rows: list[dict[str, str]] = []

	for match in pattern.finditer(response.text):
		key = match.group("key")
		role = match.group("role").upper()
		dedupe_key = (key, role)
		if dedupe_key in seen:
			continue
		seen.add(dedupe_key)

		rows.append(
			{
				"champion_name": match.group("name"),
				"tier_number": match.group("rank"),
				"role": role,
				"winrate": f"{float(match.group('win')):.2f}%",
				"pickrate": f"{float(match.group('pick')):.2f}%",
			}
		)

	rows.sort(key=lambda row: (int(row["tier_number"]), row["champion_name"], row["role"]))
	return rows


def write_csv(rows: list[dict[str, str]], output_path: Path = OUTPUT_CSV) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", newline="", encoding="utf-8") as csv_file:
		writer = csv.DictWriter(
			csv_file,
			fieldnames=["champion_name", "tier_number", "role", "winrate", "pickrate"],
		)
		writer.writeheader()
		writer.writerows(rows)


def main() -> None:
	rows = fetch_champion_rows()
	write_csv(rows)
	print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
	main()
