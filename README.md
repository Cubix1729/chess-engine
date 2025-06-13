# Python Chess Engine

This project is a small Python chess engine with a UCI interface, made for fun.

> This program is very minimalistic and its level isn't very high. Its purpose is only to be a simple and fun project.

## Usage

You can play games against the engine on [lichess.org](https://lichess.org).
In order to do that, just challenge [@SomePythonBot](https://lichess.org/@/SomePythonBot), and enjoy the game!
Currently, it is rated at around 1450~1650 elo.
Note that the bot does not accept correspondence games.

If you are curious, you can also clone the repo, install `python-chess`, and run the engine locally,
e.g. with a GUI like `Arena` or `CuteChess`.

## Implementation details

The goal was to make a tiny, single-file chess AI in Python. I used the library `python-chess`, which allowed me not to
have to implement the board and pieces representation, the move generation logic, etc...

It uses a simple evaluation function, which considers:

 - **Material**: standard piece value evaluation
 - **Piece-square tables** (mostly taken from the [Simplified Evaluation Function](https://www.chessprogramming.org/Simplified_Evaluation_Function) presented in the Chess Programming Wiki)
 - **King safety** using “attack units”, as described [here](https://www.chessprogramming.org/King_Safety#Attack_Units) in the Chess Programming Wiki
 - **Activity/mobility** of the pieces: number of legal moves, with weights for piece type
 - **Center control**: points for the control of the center squares
 - **Pawn structure**:
     - Negative points for doubled pawns
     - Negative points for isolated pawns
     - Bonuses for passed pawns


Regarding the search logic, it uses:

 - [Negamax](https://www.chessprogramming.org/Negamax) search with [alpha-beta pruning](https://www.chessprogramming.org/Alpha-Beta)
 - [Quiescence search](https://www.chessprogramming.org/Quiescence_Search) for captures, checks and promotions
 - A [transposition table](https://www.chessprogramming.org/Transposition_Table) for caching previous search results
 - [Null-move pruning](https://www.chessprogramming.org/Null_Move_Pruning)
 - **Move ordering**:
     - Captures sorting with [MVV-LVA](https://www.chessprogramming.org/MVV-LVA) (Most Valuable Victim - Least Valuable Attacker)
     - [Killer move heuristic](https://www.chessprogramming.org/Killer_Heuristic)
     - [History heuristic](https://www.chessprogramming.org/History_Heuristic)
     - Transposition table move first
     - A bonus for checks
 - [Iterative deepening](https://www.chessprogramming.org/Iterative_Deepening), as the main search loop


The engine implements a basic UCI interface, but with no configuration options.
However, you can still change manually the constants defined in the first few lines of the file.

By default, the program uses no opening book, but you can specify one by setting `PATH_TO_OPENING_BOOK`
to some opening book in the Polyglot format. The version running on Lichess uses one called `komobo.bin`,
taken from [this repo](https://github.com/gmcheems-org/free-opening-books).


## My thoughts

My bot cannot compare with the vast majority of other bots, as it is quite weak. So what could be improved?

I think the main issue is the depth it searches at on average, which is only about 2~5 for rapid or classical games.
This is very low, and causes the engine to miss most long-term strategies.

According to me, the main two reasons the depth is quite low are:

 - **The lack of pruning**: techniques like [Late move reduction (LMR)](https://www.chessprogramming.org/Late_Move_Reductions) or [Principal variation search (PVS)](https://www.chessprogramming.org/Principal_Variation_Search)
 could probably increase the search efficiency
 - **The lack of optmisation**: Python isn't particularly fast (even if the Lichess version runs on PyPy),
 and the engine does not use efficient techniques like bitboards

Still, I am happy with my engine. After all, a level around 1500 elo isn't so bad.
Anyway, it destroys me whenever I play against it (even if that's not significant given my chess level).

## Contributing

I know this is only a small personal project, but if you find a bug, have an idea or make an improvement,
I'd appreciate it if you opened an issue or a pull request.
