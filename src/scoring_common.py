import time

try:
	from . import sound_effects
except ImportError:
	import sound_effects

GOAL_RP_THRESHOLD = 150
PARK_RP_THRESHOLD = 40


def goal_points(scores: dict[str, int]) -> int:
	return scores["goal"] * 3


def parking_points(scores: dict[str, int]) -> int:
	return sum(
		15 if scores[key] == 1 else 25 if scores[key] == 2 else 0
		for key in ("p1", "p2")
	)


def calc_match_score(scores: dict[str, int]) -> int:
	return (
		goal_points(scores)
		+ scores["exc"]
		+ parking_points(scores)
		- scores.get("major_foul", 0) * 15
		- scores.get("minor_foul", 0) * 5
	)


def calc_match_rp(own_scores: dict[str, int], own_total: int, opponent_total: int) -> int:
	if own_total > opponent_total:
		rp = 3
	elif own_total == opponent_total:
		rp = 2
	else:
		rp = 0
	if goal_points(own_scores) >= GOAL_RP_THRESHOLD:
		rp += 1
	if parking_points(own_scores) >= PARK_RP_THRESHOLD:
		rp += 1
	return rp


def calc_solo_score(scores: dict[str, int]) -> int:
	parking_points_value = 15 if scores["p1"] == 1 else 25 if scores["p1"] == 2 else 0
	return (
		scores["goal"] * 3
		+ scores["exc"]
		+ parking_points_value
		- scores.get("major_foul", 0) * 15
		- scores.get("minor_foul", 0) * 5
	)


def seconds_remaining(started_at: float, duration: int) -> int:
	return max(0, duration - int(time.monotonic() - started_at))


def start_timestamp() -> float:
	return time.monotonic()


def timer_text(state: dict, duration: int) -> str:
	if state["timer_state"] == 0:
		minutes, seconds = divmod(duration, 60)
		return f"{minutes}:{seconds:02d}"
	if state["timer_state"] == 2:
		return "0:00"

	remaining = seconds_remaining(state["timer_started_at"], duration)
	sound_effects.on_timer_tick(state, remaining)
	if remaining == 0:
		state["timer_state"] = 2
		return "0:00"
	minutes, seconds = divmod(remaining, 60)
	return f"{minutes}:{seconds:02d}"
