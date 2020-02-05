from collections import deque


class TurnHandler:
    # This class handles keeping track of turns. Which is the active unit/player, turn order, etc.
    def __init__(self):
        self.queue = deque()
        self.turn_number = 0
        self.performed_critical_action = None  # Critical actions are user-commands such as attack() or move(),
        # which may not be performed more than once a turn

    def current_unit(self):
        return self.queue[-1]

    def current_player(self):
        return self.current_unit().player_id

    def start_turn(self):
        self.turn_number += 1
        self.performed_critical_action = False
        self.current_unit().on_new_turn()

    def end_turn(self):
        self.queue.appendleft(self.queue.pop())

    def add_to_queue(self, unit):
        self.queue.appendleft(unit)

    def remove_from_queue(self, unit):
        self.queue.remove(unit)

    def perform_critical_action(self):
        self.performed_critical_action = True
