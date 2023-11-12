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

# TODO: this needs to be a function of max_size
POS_TO_LEN_MAP_2 = {
    1: 15,
    2: 15,
    3: 14,
    4: 15,
    5: 15,
    6: 15,
    7: 15,
    8: 15,
    9: 14,
    10: 14,
    11: 13,
}

# TODO: This is a copypaste, but similar to second one
POS_TO_LEN_MAP_3 = {
    1: 14,
    2: 14,
    3: 13,
    4: 14,
    5: 14,
    6: 14,
    7: 14,
    8: 14,
    9: 14,
    10: 14,
    11: 12,
}


def line_limits(nail_type: int) -> tuple[int, int]:
    """
    Hardcoded max_line_len and max_lines for default font size. Different foreach nail type.
    """
    if nail_type == 1:
        return 14, 6  # maybe 15, 7 here
    # TODO: depends on font
    if nail_type == 2:
        return 14, 6
    if nail_type == 3:
        return 14, 6

    print("Unknown nail type, maybe shield? Using max_line_len=13")
    return 15, 6


def max_line_len_for_pos(idx: int, lines_nb: int, nail_type: int):
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

    if nail_type == 1:
        return POS_TO_LEN_MAP_1[pos]
    if nail_type == 2:
        return POS_TO_LEN_MAP_2[pos]
    if nail_type == 3:
        return POS_TO_LEN_MAP_3[pos]

    print("Unknown nail type, maybe shield? Using max_line_lens from nail_02")
    return POS_TO_LEN_MAP_1[pos]
