class Player:
    # This object represents a player and holds their unit, commands, etc
    def __init__(self, player_id, command_script):
        self.id = player_id
        self.units = set()
        self.command_script = command_script

    def num_units(self):
        return len(self.units)
