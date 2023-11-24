import os
import time
from threading import Lock

import numpy as np

import pywinauto
import pywinauto.mouse

from system_hotkey import SystemHotkey
hk = SystemHotkey()

from .vision import extract_cap
from .solve import solve_game
from .constants import *

app = pywinauto.Application().connect(title_re="SHENZHEN I/O")
win = app.top_window()
def screengrab():
    win.set_focus()
    return win.capture_as_image()

def click(x, y):
    win.set_focus()
    time.sleep(0.05)
    pos = win.rectangle()
    #pywinauto.mouse.click doesn't work
    pywinauto.mouse.press(coords=(pos.left + x, pos.top + y))
    time.sleep(0.05)
    pywinauto.mouse.release(coords=(pos.left + x, pos.top + y))
    time.sleep(0.05)

def drag_drop(x0, y0, x1, y1):
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

moves = None
move_id = 0

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

running = True
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
    os._exit(1)

def interactive():
    hk.register(('q',), callback=quit_handler)
    hk.register(('tab',), callback=new_game)
    hk.register(('space',), callback=step_handler)
    hk.register(('c',), callback=continue_handler)
    # The hotkey handlers will fire asynchronously
    while running:
        with move_lock:
            if continuous:
                solve_step(False)
        time.sleep(0.1)

def auto():
    hk.register(('q',), callback=quit_handler)
    for i in range(20):
        print("playing game %d" % (i+1))
        try:
            click(newgame[0], newgame[1])
            time.sleep(6)
            solve_new()
            while moves:
                solve_step(False)
                time.sleep(0.1)
            print("finished game %d" % (i+1))
            time.sleep(6)
        except:
            continue