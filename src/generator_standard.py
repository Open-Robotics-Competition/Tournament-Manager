import random
from pathlib import Path

try:
	from . import schedule_io
	from .Match import Match
except ImportError:
	import schedule_io
	from Match import Match


class StandardScheduleError(ValueError):
	"""Raised when a standard schedule cannot be generated for the inputs."""


def generate_standard(teams, batch_count: int, rng: random.Random | None = None) -> list[Match]:
	if rng is None:
		rng = random.SystemRandom()
	if batch_count < 1:
		raise StandardScheduleError("Batch count must be at least 1.")

	team_ids = [team.eventID for team in teams]
	if len(team_ids) < 4:
		raise StandardScheduleError("Standard schedule generation requires at least four teams.")
	if len(set(team_ids)) != len(team_ids):
		raise StandardScheduleError("Every team must have a unique eventID.")

	schedule = []
	partial_team_ids = []
	partial_batch = 0
	match_number = 1

	for batch_number in range(1, batch_count + 1):
		batch_order = list(team_ids)
		rng.shuffle(batch_order)
		if partial_team_ids:
			partial_ids = set(partial_team_ids)
			batch_order = (
				[team_id for team_id in batch_order if team_id not in partial_ids]
				+ [team_id for team_id in batch_order if team_id in partial_ids]
			)

		for team_id in batch_order:
			if not partial_team_ids:
				partial_batch = batch_number
			partial_team_ids.append(team_id)
			if len(partial_team_ids) == 4:
				schedule.append(_create_match(
					partial_team_ids, partial_batch, match_number, [], rng
				))
				match_number += 1
				partial_team_ids = []

	if partial_team_ids:
		surrogate_candidates = [
			team_id for team_id in team_ids if team_id not in partial_team_ids
		]
		missing_count = 4 - len(partial_team_ids)
		surrogate_ids = rng.sample(surrogate_candidates, missing_count)
		partial_team_ids.extend(surrogate_ids)
		schedule.append(_create_match(
			partial_team_ids, partial_batch, match_number, surrogate_ids, rng
		))
	return schedule


def _create_match(team_ids, batch_number: int, match_number: int, surrogate_ids, rng) -> Match:
	match_ids = list(team_ids)
	rng.shuffle(match_ids)
	match = Match()
	match.batch = batch_number
	match.match_number = match_number
	match.match_type = "Q"
	match.red_team_1, match.red_team_2, match.blue_team_1, match.blue_team_2 = match_ids
	match.surrogate_team_ids = list(surrogate_ids)
	return match


def write_schedule(schedule: list[Match], tournament_data_path: str) -> Path:
	return schedule_io.write_schedule(schedule, tournament_data_path)
