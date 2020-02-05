import interpreter
import board
import turn_handler
import player
import cmd
import argparse
import logging

# Setup logging
logger = logging.getLogger(__name__)


class Game:
    def __init__(self, filepaths):
        # Verify arguments
        if len(filepaths) < 2:
            raise Exception("Game requires at least two players. "
                            "Provide a filepath for the script used for each player")
        self.strategy_filepaths = filepaths

        # DEFAULT PARAMETERS
        self.board_size = [20, 20]
        self.turn_limit = 10000
        self.unit_limit_pct = 0.05  # The maximum number of allowed units per player, as a percentage of board capacity
        self.log_level = 10  # Level of log info. Use 30 to only display win/lose messages, 20 to also display turn
        # numbers and the board, and 10 to also display action messages
        self.write_to_file = True
        self.log_path = "log.txt"

        # OBJECT INITIALIZATION
        self.players = {}  # Dict of players, player_id -> player_object
        self.turn_handler = turn_handler.TurnHandler()  # Turn handler in charge of determining which unit acts when
        self.board = board.Board(self.turn_handler, self.players,
                                 self.board_size, self.unit_limit_pct)  # Board and units
        self.user_commands = cmd.Commands(self.board, self.turn_handler)
        self.interpreter = interpreter.Interpreter(self.turn_handler, self.user_commands)

        # CONFIGURE LOGGER
        self.configure_logger()

    def configure_logger(self):
        # Configure the logger and its handlers
        formatter = logging.Formatter('%(message)s')
        handlers = []

        # Handler for stream output
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(self.log_level)
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)

        # Handler for file output
        if self.write_to_file:
            file_handler = logging.FileHandler(self.log_path, mode='w', encoding='utf-8')
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        logging.basicConfig(handlers=handlers, level=10)

    def populate_players(self):
        # For each player, read their script and analyze it, and create a new player object
        # with the resulting instructions
        for idx, path in enumerate(self.strategy_filepaths):
            with open(path, 'r') as input_file:
                bot_cmds = input_file.read()
            self.players[idx + 1] = player.Player(idx + 1, self.interpreter.analyze(bot_cmds))

    def spawn_initial_units(self):
        # For each player, spawn one unit in a random location on the board_matrix. If the location has already
        # been picked, keep picking random locations until an available one has been found.
        spawn_locs = set()
        newloc = self.board.get_random_location()
        for player_id in self.players:
            while tuple(newloc) in spawn_locs:
                newloc = self.board.get_random_location()
            spawn_locs.add(tuple(newloc))
            self.board.spawn_unit(player_id, newloc)

    def turn_limit_reached(self):
        return self.turn_handler.turn_number >= self.turn_limit

    def turn(self):
        # Start turn (resetting all relevant state variables), execute script for current acting unit, and end turn
        self.turn_handler.start_turn()
        logger.log(20, "Turn number " + str(self.interpreter.turn_handler.turn_number))
        logger.log(20, "Acting unit: " + str(self.interpreter.turn_handler.current_unit().id))
        self.players[self.turn_handler.current_player()].command_script()
        self.turn_handler.end_turn()
        self.board.print_board()
        self.remove_losing_players()

    def remove_losing_players(self):
        # Check if any players have had all of their units destroyed, and remove them from the players list
        players_to_remove = []
        for player_id, player_r in self.players.items():
            if player_r.num_units() == 0:
                players_to_remove.append(player_id)
                logger.log(30, "Player " + str(player_id) + " eliminated")
        for player_id in players_to_remove:
            del self.players[player_id]

    def announce_winner(self):
        # Check and report the winning player(s).
        # If only one player remains, they win. Otherwise, check number of remaining units per player.
        # The winners are all the players who hold the highest number of remaining units.

        if self.one_player_left():
            logger.log(30, "Player " + str(list(self.players)[0]) + " has won the game")
            return

        #  Make a player id -> remaining units dict, check max value, then get all player ids with this max value
        remaining_units = {player_id: self.players[player_id].num_units() for player_id in self.players}
        max_num_units_left = max(remaining_units.values())
        tied_players = [player_id for player_id in remaining_units
                        if remaining_units[player_id] == max_num_units_left]

        if len(tied_players) == 1:
            logger.log(30, "Turn limit reached, player " + str(tied_players[0]) + " wins with "
                       + str(max_num_units_left) + " units remaining")
            return

        logger.log(30, "Turn limit reached, players " + str(tied_players) + " are tied with "
                   + str(max_num_units_left) + " units remaining")

    def one_player_left(self):
        # Game ends when only one player has surviving units (or if turn limit is reached)
        return len(self.players) == 1

    def game_ended(self):
        return self.turn_limit_reached() or self.one_player_left()

    def start_game(self):
        self.populate_players()
        self.spawn_initial_units()

        while not self.game_ended():
            self.turn()

        self.announce_winner()


def main():
    # Argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filepaths', nargs='*', help='Filepaths for bot strategy scripts')
    paths = parser.parse_args().filepaths

    game = Game(paths)
    game.start_game()


if __name__ == "__main__":
    main()
