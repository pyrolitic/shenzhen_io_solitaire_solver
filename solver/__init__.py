import os
import sys
import time
import atexit
import json
from pathlib import Path
from threading import Lock, Event

import numpy as np

import pywinauto
import pywinauto.mouse

# Fix system_hotkey compatibility issue with win32con
try:
    import win32con
    if not hasattr(win32con, 'VK_MEDIA_STOP'):
        win32con.VK_MEDIA_STOP = 0xB3
except ImportError:
    pass

from system_hotkey import SystemHotkey
hk = SystemHotkey()

from .vision import extract_cap
from .solve import solve_game
from .constants import newgame, dragon_x, dragon_y, valid_cards, DRAGONS

# Progress tracking
PROGRESS_FILE = Path(__file__).parent.parent / "progress.json"
TOTAL_GAMES = 100

def load_progress():
    """Load progress from file"""
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('completed_games', 0)
        except Exception as e:
            print(f"⚠ Failed to load progress: {e}")
            return 0
    return 0

def save_progress(completed):
    """Save progress to file"""
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({'completed_games': completed}, f)
    except Exception as e:
        print(f"⚠ Failed to save progress: {e}")

# Load current progress
completed_games = load_progress()

# Lazy initialization - connect to window when needed
app = None
win = None

def init_window():
    """Initialize connection to SHENZHEN I/O window"""
    global app, win
    if app is None or win is None:
        try:
            app = pywinauto.Application().connect(title_re="SHENZHEN I/O")
            win = app.top_window()
            print("✓ Connected to SHENZHEN I/O window")
        except Exception as e:
            print(f"✗ Error: Could not connect to SHENZHEN I/O window. Make sure the game is running.")
            print(f"  Details: {e}")
            raise

def cleanup():
    """Cleanup function called on exit"""
    print("\n✓ Solver exiting cleanly...")

def screengrab():
    init_window()
    win.set_focus()
    return win.capture_as_image()

def click(x, y):
    init_window()
    win.set_focus()
    time.sleep(0.05)
    pos = win.rectangle()
    #pywinauto.mouse.click doesn't work
    pywinauto.mouse.press(coords=(pos.left + x, pos.top + y))
    time.sleep(0.05)
    pywinauto.mouse.release(coords=(pos.left + x, pos.top + y))
    time.sleep(0.05)

def drag_drop(x0, y0, x1, y1):
    init_window()
    win.set_focus()
    time.sleep(0.05)
    pos = win.rectangle()
    a = np.array([x0, y0])
    b = np.array([x1, y1])
    dt = 0.015
    steps = 2

    pywinauto.mouse.press(coords=(pos.left + x0, pos.top + y0))
    for i in range(steps):
        time.sleep(dt)
        p = (a + (b-a) * ((i+1) / steps)).astype(int)
        pywinauto.mouse.move(coords=(pos.left + p[0], pos.top + p[1]))
    time.sleep(dt)
    pywinauto.mouse.release(coords=(pos.left + x1, pos.top + y1))
    time.sleep(0.04)

move_lock = Lock()
should_exit = Event()  # For thread-safe exit signaling

moves = None
move_id = 0

# Register cleanup on exit
atexit.register(cleanup)

def solve_new():
    global moves, move_id
    cap = screengrab()
    side, rose, dst, cols, dragons = extract_cap(cap)
    if any(side) or any(any(col) for col in cols):
        moves = solve_game(side, rose, dst, cols, dragons)
        move_id = 0
    else:
        #board is empty
        moves = None
        move_id = 0
        
def solve_step(singlestep):
    global moves, move_id
    if not moves:
        return

    mv = moves[move_id]
    move_id += 1
    if move_id == len(moves):
        moves = None

    if mv is None:
        if not singlestep:
            time.sleep(0.25)
    else:
        a, b = mv
        if b is None:
            click(a[0], a[1])
        else:
            drag_drop(a[0], a[1], b[0], b[1])

continuous = False
def new_game(x):
    with move_lock:
        solve_new()

def step_handler(x):
    global continuous
    continuous = False
    with move_lock:
        solve_step(True)

def continue_handler(x):
    with move_lock:
        global continuous
        continuous = not continuous

def quit_handler(x):
    """Force exit when 'q' is pressed"""
    print("\n⚠ Exit signal received (q pressed)")
    should_exit.set()  # Signal all threads to exit
    # Give it a moment for cleanup, then force exit
    time.sleep(0.5)
    print("⚠ Force exiting...")
    os._exit(0)  # Forceful exit, bypassing normal shutdown

def interactive():
    hk.register(('q',), callback=quit_handler)
    hk.register(('tab',), callback=new_game)
    hk.register(('space',), callback=step_handler)
    hk.register(('c',), callback=continue_handler)
    
    print("\n📋 Interactive mode started")
    print("  Tab   - New game")
    print("  Space - Step")
    print("  C     - Continuous/Pause")
    print("  Q     - Quit")
    print()
    
    # The hotkey handlers will fire asynchronously
    while not should_exit.is_set():
        try:
            with move_lock:
                if continuous and not should_exit.is_set():
                    solve_step(False)
            time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n✓ Interrupted by user")
            break
        except Exception as e:
            print(f"✗ Error in interactive loop: {e}")
            break

def auto():
    global completed_games
    hk.register(('q',), callback=quit_handler)
    
    remaining_games = TOTAL_GAMES - completed_games
    print(f"\n🎮 Auto mode started")
    print(f"  Completed: {completed_games}/{TOTAL_GAMES} games")
    print(f"  Remaining: {remaining_games} games")
    print("  Press Q to force quit") 
    print()
    
    
    while completed_games < TOTAL_GAMES:
        if should_exit.is_set():
            print(f"\n⚠ Quit by user - completed {completed_games} games")
            break

        remaining = TOTAL_GAMES - completed_games
        print(f"🔄 Playing game {completed_games+1}/{TOTAL_GAMES} (remaining {remaining} games)")
        try:
            click(newgame[0], newgame[1])
            time.sleep(6)
            
            if should_exit.is_set():
                break
                
            solve_new()
            
            move_count = 0
            while moves and not should_exit.is_set():
                solve_step(False)
                move_count += 1
                time.sleep(0.1)
            
            if should_exit.is_set():
                break

            # Update progress after successful game
            completed_games += 1
            save_progress(completed_games)
            print(f"✓ Finished game {completed_games}/{TOTAL_GAMES} ({move_count} moves) - Progress: {completed_games}/{TOTAL_GAMES}")
            time.sleep(6)
            
        except KeyboardInterrupt:
            print(f"\n⚠ Interrupted by user")
            break
        except Exception as e:
            print(f"✗ Error in game {completed_games+1}: {e}")
            continue
    
    if not should_exit.is_set() and completed_games == TOTAL_GAMES:
        print(f"\n🎉 Congrats! Completed all {TOTAL_GAMES} games!")
    print(f"\n📊 Final progress: {completed_games}/{TOTAL_GAMES}")
    print("✓ Solver finished")