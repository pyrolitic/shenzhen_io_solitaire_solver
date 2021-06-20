Shenzhen I/O solitaire solver
=============================

Expects the game to be windowed and running at 1600x1024. If running at a different resolution the values in `constants.py` probably need tweaking.
If launched as a module the solver will try to solve 20 games, clicking "new game" automatically. Control of the mouse will be taken and the game game window will stay in focus. Press `q` to kill the solver early.

Most games can be solved within about a minute on my machine, but there is a timeout of 100 seconds.
Uses [pywinauto](https://pywinauto.readthedocs.io/en/latest/) for process interaction, [astar](https://github.com/jrialland/python-astar) for solving the game, and [system_hotkey](https://github.com/timeyyy/system_hotkey) for hotkey control while the game is in focus.

Installation
------------
`pip install -r requirements.txt` should install all necessary modules.

Issues
------
- After some moves the game will make one or more automatic moves which are redundantly repeated by the solver. The logic it currently has is "a revealed card will be automatically moved if no other card can be stacked unto it" but this doesn't seem to cover all cases.
- The template matching is quite slow. I tried using ImageHash but couldn't get it accurate enough. There might also be some edge cases where vision doesn't work.