import re
from cmd import CommandsInspector


class Interpreter:
    # This class handles parsing and analysis of user input
    def __init__(self, turn_handler, commands):
        self.turn_handler = turn_handler
        self.commands = commands

    @staticmethod
    def is_number(expr):
        try:
            float(expr)
            return True
        except ValueError:
            return False

    @staticmethod
    def parse(expr):
        # Initial parsing for expression; strip off leading and trailing whitespaces, replace multiple spaces with
        # singles, and separate into different commands on whitespace or linebreak if not enclosed within parentheses
        expr_parsed = ' '.join(expr.split()).replace("\n", " ").replace("\t", " ")
        par = 0
        token = ""
        expr_sep = []
        for char in expr_parsed:
            if par == 0 and char == " ":
                expr_sep.append(token)
                token = ""
            else:
                if char == ")":
                    par -= 1
                token += char
                if char == "(":
                    par += 1

        if token != "":
            expr_sep.append(token)

        return expr_sep

    @staticmethod
    def is_command(expr):
        return re.match("^.*[(].*[)]+$", expr) is not None

    @staticmethod
    def is_symbol(expr):
        # Note that all numbers are also symbols, but being a number takes higher precedence
        return isinstance(expr, str) and expr.isalnum()

    @staticmethod
    def get_number_value(expr):
        # Get number value as int if possible, or float if not
        f = float(expr)
        i = int(f)
        return i if i == f else f

    @staticmethod
    def get_cmd(expr):
        return expr.split("(")[0]

    @staticmethod
    def get_args(expr):
        # Extract the arguments inside the parentheses, separated by commas
        # In order to handle nested functions, we make sure to count parentheses and only tokenize arguments inside
        # the outermost parentheses
        par = 0
        token = ""
        args = []

        for char in expr:
            if char == "," and par == 1:
                args.append(token)
                token = ""
            else:
                if char == ")":
                    par -= 1
                if par > 0:
                    token += char
                if char == "(":
                    par += 1

        if token != "":
            args.append(token)
        if par != 0:
            raise Exception("Unclosed parentheses found")

        return args

    @staticmethod
    def execute_multiple(exprs):
        # Execute all lambda functions. This evaluates arguments and then executes command.
        # Note that we continue this only so long as the current unit is able to act.
        res = None
        for expr in exprs:
            res = expr()
        return res

    def get_symbol_value(self, expr):
        # Defined symbol values are saved on a per-unit basis, so the value is always taken from the dictionary
        # of the "current unit", which is determined by the turn handler
        if expr in self.turn_handler.current_unit().var_data:
            return self.turn_handler.current_unit().var_data[expr]
        raise Exception("Undefined symbol " + expr)

    def eval_and_exec_general(self, cmd, args):
        # First execute all lambda functions for all arguments, reducing them all to either numbers or symbols
        # Then resolve all symbols by replacing them with their defined values
        args_eval = args.copy()  # Avoid modifying the original arguments
        for idx, arg in enumerate(args_eval):
            args_eval[idx] = arg()
            if self.is_symbol(args_eval[idx]):
                args_eval[idx] = self.get_symbol_value(args_eval[idx])
        return CommandsInspector.execute_command(self.commands, cmd, args_eval)

    def eval_and_exec_define(self, cmd, args):
        # Define is a special case since it expects the first argument to be an undefined symbol, so we must not
        # attempt to fully resolve it
        args_eval = args.copy()  # Avoid modifying the original arguments
        for idx, arg in enumerate(args_eval):
            args_eval[idx] = arg()
        if self.is_symbol(args_eval[1]):
            args_eval[1] = self.get_symbol_value(args_eval[1])
        return CommandsInspector.execute_command(self.commands, cmd, args_eval)

    def eval_and_exec_if_else(self, cmd, args):
        # If statements are a special case since we only want to execute the lambdas of the arguments based on the
        # predicate. Therefore only the first argument (the predicate) is evaluated at this stage, and the relevant
        # result is evaluated within the function itself
        args_eval = args.copy()  # Avoid modifying the original arguments
        args_eval[0] = args_eval[0]()
        if self.is_symbol(args_eval[0]):
            args_eval[0] = self.get_symbol_value(args_eval[0])
        return CommandsInspector.execute_command(self.commands, cmd, args_eval)

    def eval_and_exec(self, cmd, args):
        # Command execution requires special handling for define and if statements
        if cmd == "define":
            return self.eval_and_exec_define(cmd, args)
        elif cmd == "if_else":
            return self.eval_and_exec_if_else(cmd, args)
        else:
            return self.eval_and_exec_general(cmd, args)

    def analyze(self, input_string):
        # Parse statement into its component statements, then recursively analyze each one
        # and finally return a lambda function that evaluates all parameters and executes commands
        exprs = self.parse(input_string)
        exprs_processed = []
        for expr in exprs:
            if self.is_number(expr):
                # Numbers are our most basic primitive; we return a lambda function that replaces the string
                # with the corresponding number
                exprs_processed.append(lambda: self.get_number_value(expr))
            elif self.is_symbol(expr):
                # For strings ("symbols"), the returned function simply keeps them as is. Their value (if defined)
                # will be evaluated later as part of the execution
                exprs_processed.append(lambda: expr)
            elif self.is_command(expr):
                # For commands we first recursively analyze the arguments, then verify correct syntax,
                # and finally return a lambda function that evaluates all arguments and executes the command
                # (note that the arguments themselves may be commands, which get executed as part of the evaluation
                # process as well)
                cmd = self.get_cmd(expr)
                args_unevaluated = self.get_args(expr)
                args = []
                for arg in args_unevaluated:
                    args.append(self.analyze(arg))

                if cmd == "if":
                    cmd = "if_else"
                    args.append(lambda: 0)
                # Special case handling for "if" statement, which transforms it into an if_else statement with a
                # blank else clause. This saves us from having to implement both functions, as well as avoids problems
                # with the "if" command shadowing python's

                if cmd == "and":
                    cmd = "i_and"
                if cmd == "or":
                    cmd = "i_or"
                # Avoid shadowing with and/or commands
                CommandsInspector.verify_commands(self.commands, cmd, args)
                # self.commands.verify_command(cmd, args)
                exprs_processed.append((lambda xcmd, xargs: lambda: self.eval_and_exec(xcmd, xargs))(cmd, args))
                # Important: This double-lambda construct is here because python evaluates variables on execution
                # and not on definition. Without this, other processed statements which return a lambda function will
                # refer to the same cmd and arg, which will only be evaluated in the end. In other words, instead of
                # analyzing all statements, only the last one will be analyzed (multiple times). To work our way around
                # this, we construct a lambda that constructs the lambda we actually want, and immediately call it.
                # Another way around this would be to define default arguments cmd=cmd, args=args since default
                # arguments are evaluated on definition.
            else:
                raise Exception("Syntax error in expression " + str(expr))

        return lambda: self.execute_multiple(exprs_processed)
