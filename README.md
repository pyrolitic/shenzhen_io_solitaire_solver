Shenzhen I/O solitaire solver
=============================

If launched as a module the solver will try to solve 15 games. Control of the mouse will be taken. Press `q` to kill the solver early.

Most games can be solved within about a minute on my machine, but there is a timeout of 100 seconds.
Uses [pywinauto](https://pywinauto.readthedocs.io/en/latest/) for process interaction, [astar](https://github.com/jrialland/python-astar) for solving the game, and [system_hotkey](https://github.com/timeyyy/system_hotkey) for hotkey control while the game is in focus.

Issues
------
- After some moves the game will make one or more automatic moves which are redundantly repeated by the solver. The logic it currently has is "a revealed card will be automatically moved if no other card can be stacked unto it" but this doesn't seem to cover all cases.
- The template matching is quite slow. I tried using ImageHash but couldn't get it accurate enough. There might also be some edge cases where vision doesn't work.