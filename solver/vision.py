from collections import defaultdict

import PIL.Image as Im
import numpy as np

from .constants import *

def extract_table(table, origin):
    out = []
    for ri in range(num_rows*2):
        row = []
        for ci in range(num_cols):
            x, y = origin[0] + table_offset_x * ci, origin[1] + table_offset_y * ri
            img = table.crop((x, y, x+symbol_width, y+symbol_height))
            row.append(img)
        out.append(row)
    return out

def cmp_hist(a, b):
    assert len(a) == len(b)
    return sum(abs(x-y) for x,y in zip(a, b))

def match(im, wiggle=False):
    im = np.array(im).astype(int)
    mx, my = (4, 6) if wiggle else (0, 0)
    def dif(a, b):
        bs = float("inf")
        for dy in range(-my, my+1):
            for dx in range(-mx, mx+1):
                fi, li = max(0, dy), min(symbol_height, symbol_height + dy)
                fj, lj = max(0, dx), min(symbol_width, symbol_width + dx)
                h, w = li-fi, lj-fj

                sa = a[fi:li, fj:lj]
                sb = b[0:h, 0:w]
                d = np.sum((sa-sb)**2)

                f = d / (w*h)
                bs = min(bs, f)
        return bs

    #d = sorted([(dif(im, sm), sym) for sym, sm in gnd.items()])
    #sym = d[0][1]
    sym = min(gnd.items(), key=lambda sym_im: dif(im, sym_im[1]))[0]
    if sym[0] == "B" or sym == "ES":
        sym = 'BL'
    return sym


def extract_cap(cap):
    tab = extract_table(cap, table_top_left)
    cols = [[] for _ in range(num_cols)]
    for ci in range(num_cols):
        for ri in range(len(tab)):
            m = match(tab[ri][ci])
            if m != "BL":
                assert m in valid_cards
                cols[ci].append(m)
            else:
                break
        print("column %d done, %d cards" % (ci, len(cols[ci])))
    
    #pdb.set_trace()
    rose = cap.crop((rose_x, rose_y, rose_x+symbol_width, rose_y+symbol_height))
    rose = match(rose, wiggle=True)
    print("rose done")
    
    side, dst = [], []
    for i in range(3):
        x = table_top_left[0] + table_offset_x * i
        img = cap.crop((x, rose_y, x+symbol_width, rose_y+symbol_height))
        sym = match(img, wiggle=True)
        assert sym in (valid_cards | set(['BL', 'XX']))
        side.append(sym)
    print("side done")

    for i in range(3):
        x = table_top_left[0] + table_offset_x * (5 + i)
        img = cap.crop((x, rose_y, x+symbol_width, rose_y+symbol_height))
        sym = match(img, wiggle=True)
        assert sym in (valid_cards | set(['BL']))
        dst.append(sym)
    print("dest done")
    #pdb.set_trace()

    #sanity
    #assert not any(len(col) > 5 for col in cols)
    occ = defaultdict(int)
    for col in cols:
        for sym in col:
            occ[sym] += 1
    for sym in side:
        occ[sym] += 1
        
    for sym, oc in occ.items():
        if sym in DRAGONS:
            assert oc == 0 or oc == 4
        elif sym != "BL" and sym != "XX":
            assert oc == 1
    
    for sym in dst:
        if sym != 'BL':
            c = sym[1]
            v = int(sym[0])
            for lv in range(1, v):
                assert occ["%d%s" % (lv, c)] == 0
    
    #dragons
    drag = []
    for sym in DRAGONS:
        if occ[sym] == 0:
            drag.append(True)
        else:
            drag.append(False)

    print("extraction finished")
    return side, rose, dst, cols, drag

def load_ground():
    syms = """\
    1b 1g 1r 2b 2g 2r 3b 3g
    3r 4b 4g 4r 5b 5g 5r 6b
    6g 6r 7b 7g 7r 8b 8g 8r
    9b 9g 9r BL Bl ES GR RE
    RO WH XX B0""".replace("\t", "")
    syms = [l.split(' ') for l in syms.split('\n')]
    
    ground_im = Im.open("shenzhen_ground.png").convert("RGB")
    
    map = {}
    for ri, row in enumerate(syms):
        for ci, sym in enumerate(row):
            img = ground_im.crop((ci*symbol_width, ri*symbol_height, (ci+1)*symbol_width, (ri+1)*symbol_height))
            map[sym] = img
            
    return map

def make_quilt(table):
    quilt = Im.new("RGB", (num_cols*symbol_width, num_rows*symbol_height))
    ri, ci = 0, 0
    txt = ""
    for sym, im in table:
        quilt.paste(im, box=(ci*symbol_width, ri*symbol_height))
        txt += sym + " "
        ci += 1
        if ci == num_cols:
            ci, ri = 0, ri+1
            txt += '\n'
        
    return quilt, txt

gnd = load_ground()
gnd = {sym: np.array(im).astype(int) for sym, im in gnd.items()}