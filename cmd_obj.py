import inspect
from functools import wraps


def critical_action(func):
    # Decorator for "critical actions", which can only be executed once per turn and only if the unit is able
    # to act (i.e. not in the middle of spawning etc)
    @wraps(func)
    def decorated(self, *args, **kwargs):
        if self.turn_handler.performed_critical_action is True \
                or self.turn_handler.current_unit().can_act is False:
            return None
        self.turn_handler.performed_critical_action = True
        return func(self, *args, **kwargs)
    return decorated


class Commands:
    # This class handles verification and execution of allowable user-input commands
    def __init__(self, board, turn_handler):
        self.board = board
        self.turn_handler = turn_handler

    def verify_command(self, cmd, args):
        # Check that input command is defined in this class, and correct number of arguments is provided
        # This prevents users from executing general python commands
        try:
            num_expected_args = len(inspect.signature(getattr(self, cmd)).parameters)
        except AttributeError:
            raise Exception("Unknown command " + cmd + "()!")
        if cmd == "execute_command" or cmd == "verify_command":
            raise Exception("Command unavailable to user")
        if len(args) != num_expected_args:
            print(cmd)
            print(args)
            raise Exception("Invalid number of arguments; expected " + str(num_expected_args)
                            + " and got " + str(len(args)))

    def execute_command(self, cmd, args):
        return getattr(self, cmd)(*args)

    ####################################################################################################################
    # USER COMMANDS
    ####################################################################################################################

    ####################################################################################################################
    # Critical actions (will not allow execution of any more commands in the same turn)
    ####################################################################################################################

    @critical_action
    def attack(self):
        # Attack random adjacent enemy
        unit = self.turn_handler.current_unit()
        self.board.attack_adjacent_enemy(unit)

    @critical_action
    def move(self):
        # Move to random free adjacent tile
        unit = self.turn_handler.current_unit()
        current_loc = unit.loc
        new_loc = self.board.get_free_adjacent_loc(current_loc)
        if new_loc is None:
            return
        print("Unit " + str(unit.id) + " moved from " + str(current_loc) + " to " + str(new_loc))
        self.board.move_unit(unit, new_loc)

    @critical_action
    def spawn(self):
        # Set spawn timer of unit to 3 (unit will be unable to act for 3 turns, and will then spawn a new unit
        # in an adjacent free tile.
        self.turn_handler.current_unit().set_spawn(3)
        print("Setting spawn for unit " + str(self.turn_handler.current_unit().id) + " belonging to player " +
              str(self.turn_handler.current_unit().player_id) + " in 3 turns")

    @critical_action
    def wait(self):
        # Forfeit turn
        print("Unit " + str(self.turn_handler.current_unit().id) + " has forfeited its turn")
        pass

    @critical_action
    def defend(self):
        # Unit goes into defense mode (will block up to one attack until next turn)
        print("Unit " + str(self.turn_handler.current_unit().id) + " is defending")
        self.turn_handler.current_unit().defend()

    ####################################################################################################################
    # Non-critical actions (information-providing commands)
    ####################################################################################################################

    def get_unit_id(self):
        return self.turn_handler.current_unit().id

    def num_adjacent_allies(self):
        return self.board.num_allies_around_unit(self.turn_handler.current_unit())

    def num_adjacent_enemies(self):
        return self.board.num_enemies_around_unit(self.turn_handler.current_unit())

    def num_total_allies(self):
        return self.board.num_total_allies(self.turn_handler.current_player())

    def num_total_enemies(self):
        return self.board.num_total_enemies(self.turn_handler.current_player())

    def distance_from_closest_ally(self):
        return self.board.distance_from_closest_ally(self.turn_handler.current_unit())

    def distance_from_closest_enemy(self):
        return self.board.distance_from_closest_enemy(self.turn_handler.current_unit())

    ####################################################################################################################
    # Arithmetic and general commands
    ####################################################################################################################

    def define(self, symb, val):
        # Command for defining new symbol
        self.turn_handler.current_unit().var_data[symb] = val
        return True

    @staticmethod
    def if_else(pred, if_true, if_false):
        if pred:
            return if_true()
        else:
            return if_false()

    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def sub(a, b):
        return a - b

    @staticmethod
    def mul(a, b):
        return a * b

    @staticmethod
    def div(a, b):
        if b == 0:
            raise Exception("Division by 0")
        return a / b

    @staticmethod
    def eq(a, b):
        return a == b

    @staticmethod
    def gt(a, b):
        return a > b

    @staticmethod
    def gqt(a, b):
        return a >= b

    @staticmethod
    def lt(a, b):
        return a < b

    @staticmethod
    def lqt(a, b):
        return a <= b

    @staticmethod
    def neg(a):
        return not a

    @staticmethod
    def prnt(a):
        print(a)
