# bot-battle-board
## What is it?
Bot-Battle-Board (name tentative) is a programming game, where two or more players compete to see whose bots can beat the others'. The players do not manually control these bots. Instead, they write a set of instructions for them using a simple programming language, and these bots simply perform the instructions given to them.
## How do I play?
The rules are very simple. Each player starts with 1 bot, randomly placed somewhere on the board (default board size is 20 by 20 tiles, but may be changed as desired). Each bot begins with 3 points of health (hp). The bots take turns performing the instructions given to them by the players. The game ends either when only one player has any remaining bots, or when the turn limit has passed (default is 10,000 turns total among all bots, but this is also configurable). If the turn limit is reached, the player with the most active bots wins.

There are a few important things to know. The first is that the edges of the board wrap around. A bot on the leftmost side of the board taking a step to the left will emerge on the right side of the board. A unit on the top-left corner of the board may attack a unit on the bottom-right, as it is considered adjacent to it (since it is only one diagonal move away).

Another important thing is that you do not have full control of your bots. Most commands contain some element of randomness. The move() command will move the bot to a **random** adjacent tile (if there is at least one free such tile). The attack() command will attack one random adjacent enemy (if there is more than one), etc. It is advised to think of your bots as an erratic swarm of living cells, and write a strategy that leverages this.

Your bots may also spawn new bots via the spawn() command (see below for a full explanation), but beware that there is a limit to the amount of bots on the board per player. By default, the limit is set to 5% of the board capacity (for a 20 by 20 board with 400 tiles total, this means 20 bots per player).

You can start a game by running the game.py file, followed by "-f path_1 path_2 ... path_n", with the paths of the files containing the instructions for the bots. The number of players will be determined by the number of files provided. Note that a single path may be provided more than once, meaning the same strategy will be used by more than one player. The game will then begin, and a turn-by-turn record of the battle (and its conclusion) will be displayed. 

You may disable action messages and board display in game.py by setting the log to the desired level as explained in the file. You may also choose to write the match record to a file by setting write_to_file to True and supplying a path. Beware that the resulting text file may be large, depending on the turn limit and the size of the board. This also slows the program considerably.
## How do I tell the bots what to do?
You must write the instructions yourself in a text file. The syntax of the language is very simple. To execute a command, simply type it, followed by parentheses with the arguments for the function. Multiple whitespaces and linebreaks are ignored. The only valid input is either commands, numbers, or symbols which you define yourself (see the "define" command in the next section). For example, the following is a valid command:
> attack()

This will make the bot perform an attack against one random adjacent enemy, if one exists. No arguments are needed.
> add(3, 2) 

Is also a valid command, which returns the value of 3 + 2. This can be used as an argument for other functions.
> attack

Is not a valid command, because the command must end with parentheses.
> add(5, 1, 8) 

Is **also not a valid command**, because the add function expects exactly two arguments.

Commands are split into two categories: critical and non-critical commands. Critical commands, such as attack(), may only be performed once per turn. Once they are performed, the bot may not take any further action until the next turn. Non-critical commands may be used as many times as desired. Examples of such commands are the aforementioned add(a, b) which simply returns the value of a + b, and distance_from_closest_enemy() which returns the distance between the bot and its closest enemy (a bot belonging to a different player).
An example strategy would be:
```
define(x, distance_from_closest_enemy())
if(eq(x, 1), attack())
if(gt(x, 3), spawn())
move()
```
This simple strategy first defines a new variable called x, and determines its value to be the distance from the closest enemy. It then checks if x = 1 (i.e. we are adjacent to an enemy). If true, then it attacks. If x > 3, meaning the closest enemy is more than three tiles away, then spawn a new unit (the spawn command disables the bot for three turns, after which a new bot is spawned next to it). Finally, if x is not 1, but also not larger than 3 (i.e. if x is 2 or 3), then move to a random adjacent tile.
Note that even though the move() command is not inside an 'if' statement, it will only be performed if the previous two conditions are not met. This is because attack(), spawn() and move() are all critical commands, and so if for example x = 1 and the unit attacks, it will not be able to move in the same turn.
## What commands are available to my bots?
Following is a list of commands available to the player:
### Critical commands
After executing one of these commands, no others may be used in the same turn. Non-critical commands may still be used.

> attack()

This command attacks a random adjacent enemy (if one exists) for 1 point of damage. A unit whose hp reaches 0 is destroyed.

> move()

The bot moves to one random free adjacent tile (if one exists; note that bots may move diagonally).

> spawn()

Forfeit the current turn and the next two turns. In the beginning of the first turn after that, a new bot (with 3 hp) is spawned in an adjacent free tile (if one exists). The new bot is placed at the end of the turn queue, meaning it will only have its first turn at the end of the round. Note that this will only spawn new bots up to the bot limit (by default, 5% of the number of total tiles on the board per player). Past that limit, no new units will be spawned (but the bot will still forfeit three turns, so beware)!

> charge_attack(num)

The bot forfeits num turns, and charges an attack. After num turns have passed, it will attack for high damage. Each turn waited increased the damage by 1 point more than the previous turn. For example, charge_attack(1) will cause the bot to forfeit one turn and attack on the second turn for 1 + 2 = 3 damage. charge_attack(2) forfeits two turns, and attacks on the third turn for 1 + 2 + 3 = 6 points of damage. charge_attack(3) forfeits three turns, and attacks on the fourth turn for 1 + 2 + 3 + 4 = 10 points of damage, and so on.

> defend()

If the bot is attacked between now and its next turn, it will block the first attack made against it (regardless of how much damage it might inflict). If the bot is attacked more than once, only the first attack is blocked.

> fortify()

The bot gains 1 hp. There is no upper limit to the total hp allowed for a bot.

> wait()

Forfeit the current turn.
### Non-critical commands
These commands perform logic/arithmetic operations (such as addition), or return information such as the number of enemies surrounding the bot or the total number of allies it has (other bots owned by the same player). They do not perform any "action", such as attacking or defending. 

> define(variable_name, value)

Define a new variable with some value. The "value" may also be the return value of a different function. Note that **variables are "remembered" by each unit separately**. If a bot efines a variable with some value, and later a different bot defines the variable with a different value (for example, if both define a variable x with the value num_adjacent_allies() which is different for each bot), each will have their own "version" of the variable. Variable values are remembered across turns of the same unit, as long as it is not redefined. Repeated calls of define with the same variable name will simply overwrite the existing value. Variable names must be alphanumeric.

Clever usage along with the get_turn_number() function described below will allow bots to account for change in their state between turns, but be careful not to attempt to use the value of a variable that has not yet been defined as this will result in your script failing and returning an error.

> get_turn_number()

Return the number of turns that this bot has had. Returns 1 in the bot's first turn, 2 in its second, etc. May be used to avoid referring to variables which might not have been defined in the first turn.

> if(predicate, if_true)

This command checks if the predicate is true, and executes the if_true argument if it is. Note that the if_true argument may contain several commands! For example, the following is a valid usage of if:
```
if(eq(x, 1),
	define(y, add(x, 2))
	move() )
```
This code checks if the variable x is equal to 1, and if it is then it defines a new variable y equal to x + 2, and then executes the move command. The tabs and linebreaks are purely for readability. The code is equivalent to 
```
if(eq(x, 1), define(y, add(x, 2)) move())
```

> if_else(predicate, if_true, if_false)

Exactly the same as the if() command, but takes another argument if_false which is executed if the predicate is false.

> and(a, b)

Returns the logical and operation of a and b.

> or(a, b)

Returns the logical or operation of a and b.

> get_unit_limit()

Returns the maximum allowed number of bots per player.

> num_adjacent_allies()

Returns the number of adjacent (one tile away) bots owned by the same player.

> num_adjacent_enemies()

Returns the number of adjacent (one tile away) bots owned by a different player.

> num_total_allies()

Returns the total number of bots owned by the same player (minus one, since it does not include the bot itself).

> num_total_enemies()

Returns the total number of bots owned by a different player.

> distance_from_closest_ally()

Returns the distance from the closest bot owned by the same player. Distance is defined as the minimum number of tiles required to move in order to reach the other unit. A unit 3 tiles away vertically and 8 tiles away horizontally, for example, would be at a distance of 8 since it cannot be reached in less than 8 moves. If no ally exists on the board, this command returns a number larger than the board itself.

> distance_from_closest_enemy()

Returns the distance from the closest bot owned by a different player. Distance is defined the same as for distance_from_closest_ally().

> add(a, b)

Returns the value of a + b.

> sub(a, b)

Returns the value of a - b.

> mul(a, b)

Returns the value of a * b.

> div(a, b)

Returns the value of a / b. May be a floating point number.

> eq(a, b)

Returns true if a = b, false otherwise.

> gt(a, b)

Returns true if a > b, false otherwise.

> gqt(a, b)

Returns true if a >= b, false otherwise.

> lt(a, b)

Returns true if a < b, false otherwise.

> lqt(a, b)

Returns true if a <= b, false otherwise.

> neg(a)

Returns true if a is false, or false if a is true. For example neg(gt(a, b)) checks if a is NOT greater than b, and is equivalent to lqt(a, b).
