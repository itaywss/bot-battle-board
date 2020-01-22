from unit_obj import Unit
from collections import deque
from random import randint


class Board:
    def __init__(self, turn_handler):
        self.turn_handler = turn_handler
        self.board_size = [10, 10]
        self.board = [[None for _ in range(self.board_size[0])] for _ in range(self.board_size[1])]
        self.units = {}
        self.num_total_units_spawned = 0
        self.spawn_unit(1, [5, 5])
        self.spawn_unit(2, [2, 2])

    def is_free(self, loc):
        if self.board[loc[0]][loc[1]] is None:
            return True
        return False

    def spawn_unit(self, player_id, loc):
        if not self.is_free(loc):
            raise Exception("Cannot spawn unit in location " + str(loc) + " since it is occupied")

        self.num_total_units_spawned += 1
        unit_id = self.num_total_units_spawned
        new_unit = Unit(self, unit_id, player_id, loc)
        self.board[loc[0]][loc[1]] = new_unit
        self.turn_handler.add_to_queue(new_unit)
        self.units[unit_id] = new_unit
        print("New unit " + str(unit_id) + " spawned by player " + str(player_id) + " in location " + str(loc))

    def despawn_unit(self, unit):
        loc = unit.loc
        self.board[loc[0]][loc[1]] = None
        self.turn_handler.remove_from_queue(unit)
        del self.units[unit.id]

    def spawn_in_adjacent_location(self, player_id, loc):
        spawn_loc = self.get_free_adjacent_loc(loc)
        if spawn_loc is None:
            return
        self.spawn_unit(player_id, spawn_loc)

    def get_free_adjacent_loc(self, loc):
        if self.num_free_tiles_around_loc(loc) == 0:
            return None
        free_loc = self.get_adjacent_loc(loc)
        while not self.is_free(free_loc):
            free_loc = self.get_adjacent_loc(free_loc)
        return free_loc

    def get_adjacent_loc(self, loc):
        return [(loc[0] + randint(-1, 1) + self.board_size[0]) % self.board_size[0],
                (loc[1] + randint(-1, 1) + self.board_size[1]) % self.board_size[1]]

    def move_unit(self, unit, new_loc):
        if not self.is_free(new_loc):
            raise Exception("Tried to move unit " + str(unit.id) + "to occupied location " + str(new_loc))
        old_loc = unit.loc
        unit.loc = new_loc
        self.board[old_loc[0]][old_loc[1]] = None
        self.board[new_loc[0]][new_loc[1]] = unit

    def num_free_tiles_around_loc(self, loc):
        return self.count_boolean_function_around_loc(loc, self.is_free)

    def num_free_tiles_around_unit(self, unit):
        loc = unit.loc
        return self.num_free_tiles_around_loc(loc)

    def get_unit_in_loc(self, loc):
        return self.board[loc[0]][loc[1]]

    def num_enemies_around_unit(self, unit):
        return 8 - self.num_free_tiles_around_unit(unit) - self.num_allies_around_unit(unit)

    def is_ally(self, loc, player_id):
        unit_in_loc = self.get_unit_in_loc(loc)
        if unit_in_loc is not None and unit_in_loc.player_id == player_id:
            return True
        return False

    def num_allies_around_unit(self, unit):
        loc = unit.loc
        player_id = unit.player_id
        return self.count_boolean_function_around_loc(loc, lambda tloc: self.is_ally(tloc, player_id)) - 1

    def count_boolean_function_around_loc(self, loc, f_bool):
        n = 0
        for x_adj in [-1, 0, 1]:
            for y_adj in [-1, 0, 1]:
                locx = (loc[0] + x_adj + self.board_size[0]) % self.board_size[0]
                locy = (loc[1] + y_adj + self.board_size[1]) % self.board_size[1]
                if f_bool([locx, locy]) is True:
                    n += 1
        return n

    def print_board(self):
        output_mtx = []
        for row in self.board:
            output_mtx.append(['X' if elem is None else elem.player_id for elem in row])
        s = [[str(e) for e in row] for row in output_mtx]
        lens = [max(map(len, col)) for col in zip(*s)]
        fmt = '\t'.join('{{:{}}}'.format(x) for x in lens)
        table = [fmt.format(*row) for row in s]
        print('\n'.join(table))

    def num_total_allies(self, player_id):
        num_allies = 0
        for unit_id in self.units:
            if self.units[unit_id].player_id == player_id:
                num_allies += 1
        return num_allies - 1

    def num_total_enemies(self, player_id):
        return len(self.units) - self.num_total_allies(player_id) - 1

    #
    # def distance_between_units(self, unit1, unit2):
    #     loc1 = unit1.loc
    #     loc2 = unit2.loc
    #     xdist = (loc1[0] - loc2[0] + self.board_size[0]) % self.board_size[0]
