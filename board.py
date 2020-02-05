from typing import List
from typing import Union
from unit import Unit
from random import choice
from math import ceil
from random import randint
import logging

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(1)


class BoardMatrix:
    # A wrapper class for the matrix of elements on the board, which takes as an index a list of two values (x index
    # and y index)
    board_matrix: List[List[Union[Unit, None]]]  # Type hinting

    def __init__(self, size):
        self.board_matrix = [[None for _ in range(size[1])] for _ in range(size[0])]

    def __getitem__(self, loc):
        return self.board_matrix[loc[0]][loc[1]]

    def __setitem__(self, loc, value):
        self.board_matrix[loc[0]][loc[1]] = value


class Board:
    # This class handles the board_matrix object and the units on it and the manipulation thereof.
    # It also handles all unit- and board_matrix-related commands that should not be directly exposed to the user

    def __init__(self, turn_handler, players, board_size, unit_limit_pct):
        # Board initialization
        self.turn_handler = turn_handler
        self.players = players
        self.board_size = board_size
        self.unit_limit = ceil(board_size[0] * board_size[1] * unit_limit_pct)
        self.board_matrix = BoardMatrix(board_size)
        self.num_total_units_spawned = 0

        if unit_limit_pct <= 0 or unit_limit_pct > 1:
            raise Exception("Unit limit (% of board capacity) must be greater than 0 and less than or equal to 1")

    ####################################################################################################################
    # Board manipulation
    ####################################################################################################################

    def spawn_unit(self, player_id, loc):
        # Add new unit to board
        if not self.is_free(loc):
            raise Exception("Cannot spawn unit in location " + str(loc) + " since it is occupied")

        if self.players[player_id].num_units() >= self.unit_limit:
            logger.log(10, "Player " + str(player_id)
                       + " attempted to spawn new unit, but has reached the spawn limit.")
            return

        self.num_total_units_spawned += 1
        unit_id = self.num_total_units_spawned
        new_unit = Unit(self, unit_id, player_id, loc)
        self.board_matrix[loc] = new_unit
        self.turn_handler.add_to_queue(new_unit)
        self.players[player_id].units.add(new_unit)
        logger.log(10, "New unit " + str(unit_id) + " spawned by player " + str(player_id) + " in location " + str(loc))

    def despawn_unit(self, unit):
        # Remove unit from board
        loc = unit.loc
        self.board_matrix[loc] = None
        self.turn_handler.remove_from_queue(unit)
        self.players[unit.player_id].units.remove(unit)

    def spawn_in_adjacent_location(self, player_id, loc):
        spawn_loc = self.get_free_adjacent_loc(loc)
        if spawn_loc is None:
            return
        self.spawn_unit(player_id, spawn_loc)

    def move_unit(self, unit, new_loc):
        if not self.is_free(new_loc):
            raise Exception("Tried to move unit " + str(unit.id) + "to occupied location " + str(new_loc))
        old_loc = unit.loc
        unit.loc = new_loc
        self.board_matrix[old_loc] = None
        self.board_matrix[new_loc] = unit

    ####################################################################################################################
    # Functions for use in user-commands
    ####################################################################################################################

    def num_allies_around_unit(self, unit):
        loc = unit.loc
        player_id = unit.player_id
        return self.count_adjacent_locs(loc, lambda tloc: self.is_ally(tloc, player_id))

    def num_enemies_around_unit(self, unit):
        return 8 - self.num_free_tiles_around_unit(unit) - self.num_allies_around_unit(unit)

    def num_total_allies(self, player_id):
        return self.players[player_id].num_units() - 1

    def num_total_enemies(self, player_id):
        return sum([self.players[t_id].num_units() for t_id in self.players if t_id != player_id])

    def distance_from_closest_ally(self, unit):
        dist = [self.board_size[0] + self.board_size[1]]
        for ally in self.get_all_allies(unit):
            dist.append(self.distance_between_units(unit, ally))
        return min(dist)

    def distance_from_closest_enemy(self, unit):
        dist = [self.board_size[0] + self.board_size[1]]
        for enemy in self.get_all_enemies(unit):
            dist.append(self.distance_between_units(unit, enemy))
        return min(dist)

    def attack_adjacent_enemy(self, unit, dmg):
        enemy_unit = self.get_adjacent_enemy_unit(unit)
        if enemy_unit is None:
            logger.log(10, "Unit " + str(unit.id) + " tried to attack, but no enemy units in range")
            return
        logger.log(10, "Unit " + str(unit.id) + " attacked unit " + str(enemy_unit.id))
        enemy_unit.damage(dmg)

    ####################################################################################################################
    # Helper functions
    ####################################################################################################################

    def get_random_location(self):
        return [randint(0, self.board_size[0] - 1), randint(0, self.board_size[1]) - 1]

    def is_free(self, loc):
        return self.board_matrix[loc] is None

    def is_ally(self, loc, player_id):
        unit_in_loc = self.get_unit_in_loc(loc)
        return unit_in_loc is not None and unit_in_loc.player_id == player_id

    def is_enemy(self, loc, player_id):
        unit_in_loc = self.get_unit_in_loc(loc)
        return unit_in_loc is not None and unit_in_loc.player_id != player_id

    def get_all_adjacent_locs(self, loc):
        adjacent_locs = [None, None, None, None, None, None, None, None]  # Preallocate list for efficiency
        for x_id, x_adj in enumerate([-1, 0, 1]):
            for y_id, y_adj in enumerate([-1, 0, 1]):
                locx = (loc[0] + x_adj + self.board_size[0]) % self.board_size[0]
                locy = (loc[1] + y_adj + self.board_size[1]) % self.board_size[1]

                # Calculate index in list of the location. Ignore the middle spot (since it is not "adjacent"), and
                # shift all indices after it by -1 to compensate
                idx = x_id * 3 + y_id
                if idx < 4:
                    adjacent_locs[idx] = [locx, locy]
                elif idx > 4:
                    adjacent_locs[idx - 1] = [locx, locy]
        return adjacent_locs

    def get_free_adjacent_loc(self, loc):
        free_adjacent_locs = self.get_adjacent_locs(loc, self.is_free)
        if len(free_adjacent_locs) == 0:
            return None
        return choice(free_adjacent_locs)

    def num_free_tiles_around_loc(self, loc):
        return self.count_adjacent_locs(loc, self.is_free)

    def num_free_tiles_around_unit(self, unit):
        loc = unit.loc
        return self.num_free_tiles_around_loc(loc)

    def get_unit_in_loc(self, loc):
        return self.board_matrix[loc]

    def get_adjacent_enemy_unit(self, unit):
        enemy_locs = self.get_adjacent_locs(unit.loc,
                                            lambda tloc: self.is_enemy(tloc, unit.player_id))
        if len(enemy_locs) == 0:
            return None
        return self.get_unit_in_loc(choice(enemy_locs))

    def count_adjacent_locs(self, loc, f_bool=lambda x: True):
        # Get a location and a boolean function, and count the number of adjacent locations that satisfy the function
        return len(self.get_adjacent_locs(loc, f_bool))

    def get_adjacent_locs(self, loc, f_bool=lambda x: True):
        # Get a location and a boolean function, and return all adjacent locations that satisfy the function
        adjacent_locs = self.get_all_adjacent_locs(loc)
        return [adjacent_loc for adjacent_loc in adjacent_locs if f_bool(adjacent_loc)]

    def get_all_enemies(self, unit):
        return [t_unit
                for player_id in self.players if player_id != unit.player_id
                for t_unit in self.players[player_id].units]

    def get_all_allies(self, unit):
        return [t_unit
                for t_unit in self.players[unit.player_id].units
                if t_unit != unit]

    def distance_between_units(self, unit1, unit2):
        # Return the distance between two units. Here, distance is defined as the minimal number of steps needed to
        # reach one unit from the other, taking into account that units can move one tile in any direction (including
        # diagonally) and that the board_matrix wraps around (so it may be shorter to go from the other side).
        loc1 = unit1.loc
        loc2 = unit2.loc
        xdist_abs = abs(loc1[0] - loc2[0])
        xdist = min(xdist_abs, self.board_size[0] - xdist_abs)
        ydist_abs = abs(loc1[1] - loc2[1])
        ydist = min(ydist_abs, self.board_size[1] - ydist_abs)
        return max(xdist, ydist)

    def get_unit_limit(self):
        # Return the unit limit
        return self.unit_limit

    ####################################################################################################################
    # Display
    ####################################################################################################################

    def print_board(self):
        # Print the board_matrix matrix nicely formatted
        # Code adapted from https://stackoverflow.com/questions/13214809/pretty-print-2d-python-list/32159502
        output_mtx = [['X' if elem is None else elem.id for elem in row] for row in self.board_matrix.board_matrix]
        s = [[str(e) for e in row] for row in output_mtx]
        lens = [max(map(len, col)) for col in zip(*s)]
        fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
        table = [fmt.format(*row) for row in s]
        table_formatted = '\n'.join(table)
        logger.log(20, table_formatted)