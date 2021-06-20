#UI
newgame = (1363, 933)
dragon_x = 732
dragon_y = (159, 241, 324)
table_top_left, table_top_right = (254, 394), (1337, 542) #of starting 8*5 table
table_width, table_height = table_top_right[0]-table_top_left[0], table_top_right[1]-table_top_left[1]
symbol_width, symbol_height = 19, 25 #(1337-1318, 542-517)
table_offset_x, table_offset_y = 152, 31
rose_x, rose_y = 822, 129
num_rows, num_cols = 5, 8
table_card_drag_pos = (303, 392+12)
top_card_drag_pos = (table_card_drag_pos[0], rose_y+symbol_height//2)

DRAGONS = ["RE", "GR", "WH"]
valid_cards = {'%d%s' % (i, c) for i in range(1, 10) for c in "rgb"} | set(DRAGONS + ['RO'])