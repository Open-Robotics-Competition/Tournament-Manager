class Match:
    def __init__(self):
        self.match_number = 0
        self.match_type = ""
        self.surrogate_team_ids = []
        self.red_breakdown = None
        self.blue_breakdown = None

    batch = 0
    red_team_1 = -1
    red_team_2 = -1
    blue_team_1 = -1
    blue_team_2 = -1

    red_score = -1
    blue_score = -1

    red_rp = -1
    blue_rp = -1

    played = False