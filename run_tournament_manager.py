"""Entry point wrapper: puts src/ on sys.path and launches the tournament manager app."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import tournament_manager
import tournament_setup


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Run the field display tournament manager.")
	parser.add_argument(
		"-t", "--tournament-data", dest="tournament_data", default=None,
		help="Path to a tournament data folder to use instead of the default.",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	if args.tournament_data:
		tournament_setup.tournament_data_path = args.tournament_data
	tournament_manager.main()


if __name__ == "__main__":
	main()
