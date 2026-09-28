from collections import Counter


def analyze_schedule(schedule, teams) -> dict:
	team_names = {team.eventID: team.name for team in teams}
	non_surrogate_matches = Counter()
	partner_counts = Counter()
	opponent_counts = Counter()
	back_to_back_cases = 0
	previous_scheduled_team_ids = set()

	for match in schedule:
		red_alliance = (match.red_team_1, match.red_team_2)
		blue_alliance = (match.blue_team_1, match.blue_team_2)
		surrogate_ids = set(match.surrogate_team_ids)
		current_team_ids = set(red_alliance + blue_alliance)
		real_team_ids = current_team_ids - surrogate_ids

		back_to_back_cases += len(previous_scheduled_team_ids & current_team_ids)
		previous_scheduled_team_ids = current_team_ids

		for team_id in real_team_ids:
			non_surrogate_matches[team_id] += 1

		if not set(red_alliance) & surrogate_ids:
			partner = tuple(sorted(red_alliance))
			partner_counts[partner] += 1
		if not set(blue_alliance) & surrogate_ids:
			partner = tuple(sorted(blue_alliance))
			partner_counts[partner] += 1

		for red_id in red_alliance:
			for blue_id in blue_alliance:
				if red_id not in surrogate_ids and blue_id not in surrogate_ids:
					opponent_counts[tuple(sorted((red_id, blue_id)))] += 1

	repeat_partner_cases = sum(count - 1 for count in partner_counts.values() if count > 1)
	repeat_opponent_cases = sum(count - 1 for count in opponent_counts.values() if count > 1)
	return {
		"total_matches": len(schedule),
		"non_surrogate_matches": {
			team_id: non_surrogate_matches[team_id]
			for team_id in team_names
		},
		"back_to_back_cases": back_to_back_cases,
		"repeat_partner_cases": repeat_partner_cases,
		"repeat_opponent_cases": repeat_opponent_cases,
	}



def format_schedule_statistics(statistics: dict, teams) -> str:
	team_names = {team.eventID: team.name for team in teams}
	match_counts = statistics["non_surrogate_matches"]
	unique_counts = set(match_counts.values())
	if len(unique_counts) <= 1:
		non_surrogate_lines = [
			f"NON-SURROGATE MATCHES PER TEAM: {next(iter(unique_counts), 0)}"
		]
	else:
		team_entries = [
			f"{team_names[team_id]}: {count}"
			for team_id, count in match_counts.items()
		]
		non_surrogate_lines = ["NON-SURROGATE MATCHES PER TEAM (UNEVEN):"] + [
			" | ".join(team_entries[index:index + 8])
			for index in range(0, len(team_entries), 8)
		]
	return "\n".join((
		f"TOTAL MATCHES: {statistics['total_matches']}  |  "
		f"BACK-TO-BACK: {statistics['back_to_back_cases']}  |  "
		f"REPEAT PARTNERS: {statistics['repeat_partner_cases']}  |  "
		f"REPEAT OPPONENTS: {statistics['repeat_opponent_cases']}",
		*non_surrogate_lines,
	))
