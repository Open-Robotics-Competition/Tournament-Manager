from itertools import combinations
import random
from pathlib import Path

try:
	from . import schedule_io
	from .Match import Match
except ImportError:
	import schedule_io
	from Match import Match


class RoundRobinError(ValueError):
	"""Raised when the team list cannot produce a valid round-robin schedule."""


def generate_round_robin(teams, rng: random.Random | None = None) -> list[Match]:
	if rng is None:
		rng = random.SystemRandom()
	team_ids = [team.eventID for team in teams]
	if len(team_ids) < 4:
		raise RoundRobinError("Round-robin generation requires at least four teams.")
	if len(set(team_ids)) != len(team_ids):
		raise RoundRobinError("Every team must have a unique eventID.")

	schedule = []
	alliances = list(combinations(team_ids, 2))
	paired_alliances, unmatched_alliances = _pair_disjoint_alliances(alliances, rng)
	for first_alliance, second_alliance in paired_alliances:
		schedule.append(_create_match(
			first_alliance, second_alliance, 0, rng
		))

	if unmatched_alliances:
		remaining_alliance = unmatched_alliances[0]
		surrogate_candidates = [team_id for team_id in team_ids if team_id not in remaining_alliance]
		first_surrogate_alliance = rng.sample(surrogate_candidates, 2)
		schedule.append(_create_match(
			remaining_alliance, first_surrogate_alliance, 0, rng,
			first_surrogate_alliance,
		))

	_assign_batches(schedule)
	for match_number, match in enumerate(schedule, start=1):
		match.match_number = match_number

	return schedule


def _pair_disjoint_alliances(alliances, rng: random.Random):
	target_unmatched = len(alliances) % 2
	best_pairs = []
	best_unmatched = list(alliances)

	for _attempt in range(256):
		pending = list(alliances)
		rng.shuffle(pending)
		pairs = []
		unmatched = []
		while pending:
			alliance = pending.pop()
			compatible = [
				index for index, other in enumerate(pending)
				if set(alliance).isdisjoint(other)
			]
			if not compatible:
				unmatched.append(alliance)
				if len(unmatched) > len(best_unmatched):
					break
				continue
			partner_index = rng.choice(compatible)
			partner = pending.pop(partner_index)
			pairs.append((alliance, partner))
		if len(unmatched) < len(best_unmatched):
			best_pairs = pairs
			best_unmatched = unmatched
		if len(best_unmatched) == target_unmatched:
			return best_pairs, best_unmatched

	if len(best_unmatched) != target_unmatched:
		raise RoundRobinError("Could not pair alliances into distinct-team matches.")
	return best_pairs, best_unmatched


def _assign_batches(schedule: list[Match]) -> None:
	batch_team_ids: list[set[int]] = []
	for match in schedule:
		match_team_ids = {
			match.red_team_1,
			match.red_team_2,
			match.blue_team_1,
			match.blue_team_2,
		}
		for batch_index, used_team_ids in enumerate(batch_team_ids):
			if not match_team_ids & used_team_ids:
				match.batch = batch_index + 1
				used_team_ids.update(match_team_ids)
				break
		else:
			batch_team_ids.append(set(match_team_ids))
			match.batch = len(batch_team_ids)


def _create_match(
	first_alliance,
	second_alliance,
	batch: int,
	rng: random.Random,
	surrogate_team_ids: list[int] | None = None,
) -> Match:
	match_alliances = [list(first_alliance), list(second_alliance)]
	rng.shuffle(match_alliances)
	for alliance in match_alliances:
		rng.shuffle(alliance)
	match = Match()
	match.batch = batch
	match.match_type = "Q"
	match.red_team_1, match.red_team_2 = match_alliances[0]
	match.blue_team_1, match.blue_team_2 = match_alliances[1]
	match.surrogate_team_ids = list(surrogate_team_ids or ())
	return match


def write_schedule(schedule: list[Match], tournament_data_path: str) -> Path:
	return schedule_io.write_schedule(schedule, tournament_data_path)
