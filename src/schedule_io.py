import csv
from pathlib import Path

try:
	from .Match import Match
	from .Team import Team
except ImportError:
	from Match import Match
	from Team import Team

SCHEDULE_FILENAME = "schedule.txt"
SCHEDULE_FINAL_FILENAME = "schedule_final.txt"
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


def write_human_readable_schedule(
	schedule: list[Match], teams: list[Team], tournament_data_path: str
) -> Path:
	"""Writes a plain-text, column-aligned schedule for distribution to teams."""
	names_by_id = {team.eventID: team.name for team in teams}

	def team_name(team_id: int) -> str:
		return names_by_id.get(team_id, f"Unknown team {team_id}")

	rows = [
		(
			f"{match.match_type}{match.match_number}",
			team_name(match.red_team_1), team_name(match.red_team_2),
			team_name(match.blue_team_1), team_name(match.blue_team_2),
		)
		for match in schedule
	]

	match_header, red_1_header, red_2_header, blue_1_header, blue_2_header = (
		"Match", "RED 1", "RED 2", "BLUE 1", "BLUE 2",
	)
	match_width = max([len(match_header)] + [len(row[0]) for row in rows])
	# Every RED/BLUE column shares one width so any team name fits in any column.
	alliance_width = max(
		[len(red_1_header), len(red_2_header), len(blue_1_header), len(blue_2_header)]
		+ [len(name) for row in rows for name in row[1:]]
	)

	def format_row(match_label: str, red_1: str, red_2: str, blue_1: str, blue_2: str) -> str:
		return (
			f"{match_label:<{match_width}} || "
			f"{red_1:<{alliance_width}} | {red_2:<{alliance_width}} || "
			f"{blue_1:<{alliance_width}} | {blue_2:<{alliance_width}}"
		)

	lines = [format_row(match_header, red_1_header, red_2_header, blue_1_header, blue_2_header)]
	lines.append("-" * len(lines[0]))
	lines.extend(format_row(*row) for row in rows)

	output_path = Path(tournament_data_path) / SCHEDULE_FINAL_FILENAME
	output_path.parent.mkdir(parents=True, exist_ok=True)
	output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
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
