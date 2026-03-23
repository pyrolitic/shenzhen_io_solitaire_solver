Shenzhen I/O solitaire solver
=============================

Expects the game to be windowed and running at 1600x1024. If running at a different resolution the values in `constants.py` probably need tweaking.
If launched as a module the solver will try to solve 100 games (or resume from previous progress), clicking "new game" automatically. Control of the mouse will be taken and the game window will stay in focus. Press `q` to force-quit the solver early.

Most games can be solved within about a minute on my machine, but there is a timeout of 100 seconds.
Uses [pywinauto](https://pywinauto.readthedocs.io/en/latest/) for process interaction, [astar](https://github.com/jrialland/python-astar) for solving the game, and [system_hotkey](https://github.com/timeyyy/system_hotkey) for hotkey control while the game is in focus.

Installation and usage
------------
1. Install dependencies into the project's virtual environment:

```bash
pip install -r requirements.txt
```

2. Start the Shenzhen I/O game window (windowed, ideally 1600x1024). The solver will connect to that window.

3. Run the solver (from project root, with the virtualenv active):

```bash
.venv\Scripts\python -m solver
```

The solver will attempt to complete 100 games. Progress is saved to `progress.json` in the project root so you can stop and resume later. Press `q` to force-quit immediately.

Issues
------
- After some moves the game will make one or more automatic moves which are redundantly repeated by the solver. The logic it currently has is "a revealed card will be automatically moved if no other card can be stacked unto it" but this doesn't seem to cover all cases.
- The template matching is quite slow. I tried using ImageHash but couldn't get it accurate enough. There might also be some edge cases where vision doesn't work.