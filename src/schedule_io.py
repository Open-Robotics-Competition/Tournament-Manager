import csv
from pathlib import Path

try:
	from .Match import Match
except ImportError:
	from Match import Match

SCHEDULE_FILENAME = "schedule.txt"
BREAKDOWN_KEYS = ("goal", "exc", "p1", "p2", "major_foul", "minor_foul")


def _serialize_breakdown(breakdown: dict[str, int] | None) -> str:
	if not breakdown:
		return ""
	return ";".join(f"{key}:{breakdown.get(key, 0)}" for key in BREAKDOWN_KEYS)


def _deserialize_breakdown(text: str) -> dict[str, int] | None:
	if not text:
		return None
	breakdown = {}
	for part in text.split(";"):
		key, _, value = part.partition(":")
		if key:
			breakdown[key] = int(value) if value else 0
	return breakdown


def write_schedule(schedule: list[Match], tournament_data_path: str) -> Path:
	output_path = Path(tournament_data_path) / SCHEDULE_FILENAME
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with output_path.open("w", newline="", encoding="utf-8") as schedule_file:
		writer = csv.writer(schedule_file)
		writer.writerow((
			"match_number", "match_type", "batch",
			"red_team_1", "red_team_2", "blue_team_1", "blue_team_2",
			"surrogate_team_ids",
			"red_score", "blue_score", "red_rp", "blue_rp", "played",
			"red_breakdown", "blue_breakdown",
		))
		for match in schedule:
			writer.writerow((
				match.match_number, match.match_type, match.batch,
				match.red_team_1, match.red_team_2, match.blue_team_1, match.blue_team_2,
				";".join(str(team_id) for team_id in match.surrogate_team_ids),
				match.red_score, match.blue_score, match.red_rp, match.blue_rp, match.played,
				_serialize_breakdown(match.red_breakdown),
				_serialize_breakdown(match.blue_breakdown),
			))
	return output_path


def read_schedule(tournament_data_path: str) -> list[Match]:
	input_path = Path(tournament_data_path) / SCHEDULE_FILENAME
	schedule = []
	with input_path.open("r", newline="", encoding="utf-8") as schedule_file:
		reader = csv.DictReader(schedule_file)
		for row in reader:
			match = Match()
			match.match_number = int(row["match_number"])
			match.match_type = row.get("match_type") or "Q"
			match.batch = int(row["batch"]) if row.get("batch") else 0
			match.red_team_1 = int(row["red_team_1"])
			match.red_team_2 = int(row["red_team_2"])
			match.blue_team_1 = int(row["blue_team_1"])
			match.blue_team_2 = int(row["blue_team_2"])
			match.surrogate_team_ids = [
				int(team_id) for team_id in row["surrogate_team_ids"].split(";") if team_id
			]
			match.red_score = int(row["red_score"])
			match.blue_score = int(row["blue_score"])
			match.red_rp = int(row["red_rp"])
			match.blue_rp = int(row["blue_rp"])
			match.played = row["played"] in ("True", "true", "1")
			match.red_breakdown = _deserialize_breakdown(row.get("red_breakdown", ""))
			match.blue_breakdown = _deserialize_breakdown(row.get("blue_breakdown", ""))
			schedule.append(match)
	return schedule
