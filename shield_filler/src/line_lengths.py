POS_TO_LEN_MAP_1 = {
    1: 15,
    2: 15,
    3: 14,
    4: 15,
    5: 15,
    6: 15,
    7: 15,
    8: 15,
    9: 14,
    10: 13,
    11: 13,
}

# TODO: fix this one
POS_TO_LEN_MAP_2 = {
    1: 13,
    2: 13,
    3: 12,
    4: 13,
    5: 13,
    6: 13,
    7: 13,
    8: 13,
    9: 12,
    10: 11,
    11: 11,
}

# TODO: This is a copypaste, but similar to second one
POS_TO_LEN_MAP_3 = {
    1: 13,
    2: 13,
    3: 12,
    4: 13,
    5: 13,
    6: 13,
    7: 13,
    8: 13,
    9: 12,
    10: 11,
    11: 11,
}


def line_limits(nail_type: str) -> tuple[int, int]:
    """
    Hardcoded max_line_len and max_lines for default font size. Different foreach nail type.
    """
    if nail_type == "templates/nail_01.bmp":
        return 15, 6  # maybe 15, 7 here
    if nail_type == "templates/nail_02.bmp":
        return 13, 6
    if nail_type == "templates/nail_03.bmp":
        return 13, 6

    print("Unknown nail type, maybe shield? Using max_line_len=13")
    return 13, 6


def max_line_len_for_pos(idx: int, lines_nb: int, nail_type: str):
    """
    Get max line len depending on line idx. Its different for each type of nail because of
    its various non-rectangular shapes.
    """
    pos = 6
    if lines_nb == 1:
        pos = 6
    if lines_nb == 2:
        if idx == 0:
            pos = 5
        elif idx == 1:
            pos = 7
    if lines_nb == 3:
        if idx == 0:
            pos = 4
        elif idx == 1:
            pos = 6
        elif idx == 2:
            pos = 8
    if lines_nb == 4:
        if idx == 0:
            pos = 3
        elif idx == 1:
            pos = 5
        elif idx == 2:
            pos = 7
        elif idx == 3:
            pos = 9
    if lines_nb == 5:
        if idx == 0:
            pos = 2
        elif idx == 1:
            pos = 4
        elif idx == 2:
            pos = 6
        elif idx == 3:
            pos = 8
        elif idx == 4:
            pos = 10
    if lines_nb == 6:
        if idx == 0:
            pos = 1
        elif idx == 1:
            pos = 3
        elif idx == 2:
            pos = 5
        elif idx == 3:
            pos = 7
        elif idx == 4:
            pos = 9
        elif idx == 5:
            pos = 11

    if nail_type == "templates/nail_01.bmp":
        return POS_TO_LEN_MAP_1[pos]
    if nail_type == "templates/nail_02.bmp":
        return POS_TO_LEN_MAP_2[pos]
    if nail_type == "templates/nail_03.bmp":
        return POS_TO_LEN_MAP_3[pos]

    print("Unknown nail type, maybe shield? Using max_line_lens from nail_02")
    return POS_TO_LEN_MAP_1[pos]
