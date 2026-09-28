"""Ranking computation derived from the match schedule (the single source of truth)."""

try:
	from .Match import Match
	from .Team import Team
except ImportError:
	from Match import Match
	from Team import Team


def calculate_rankings(schedule: list[Match], teams: list[Team]) -> list[dict]:
	stats = {
		team.eventID: {
			"team": team, "rp": 0, "matches_played": 0,
			"wins": 0, "losses": 0, "ties": 0, "total_score": 0,
		}
		for team in teams
	}

	for match in schedule:
		if not match.played:
			continue
		surrogates = set(match.surrogate_team_ids)
		if match.red_score > match.blue_score:
			red_outcome, blue_outcome = "wins", "losses"
		elif match.blue_score > match.red_score:
			red_outcome, blue_outcome = "losses", "wins"
		else:
			red_outcome = blue_outcome = "ties"

		for team_ids, rp, outcome, score in (
			((match.red_team_1, match.red_team_2), match.red_rp, red_outcome, match.red_score),
			((match.blue_team_1, match.blue_team_2), match.blue_rp, blue_outcome, match.blue_score),
		):
			for team_id in team_ids:
				if team_id in surrogates:
					continue
				entry = stats.get(team_id)
				if entry is None:
					continue
				entry["matches_played"] += 1
				entry["rp"] += max(0, rp)
				entry["total_score"] += max(0, score)
				entry[outcome] += 1

	rankings = []
	for entry in stats.values():
		matches_played = entry["matches_played"]
		normalized_rp = entry["rp"] / matches_played if matches_played else 0.0
		rankings.append({
			"team": entry["team"],
			"matches_played": matches_played,
			"wins": entry["wins"],
			"losses": entry["losses"],
			"ties": entry["ties"],
			"rp": entry["rp"],
			"normalized_rp": normalized_rp,
			"total_score": entry["total_score"],
		})

	rankings.sort(key=lambda item: (-item["normalized_rp"], -item["total_score"], item["team"].eventID))
	for index, item in enumerate(rankings, start=1):
		item["rank"] = index
	return rankings
