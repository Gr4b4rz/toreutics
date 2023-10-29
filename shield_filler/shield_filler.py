#!/usr/bin/python3
import argparse
import itertools
import shutil
import os
import re

from PIL import Image, ImageDraw, ImageFont
from src.line_lengths import line_limits, max_line_len_for_pos


def parse_args():
    "Parse arguments passed by cli"
    parser = argparse.ArgumentParser(prog="Shield Filler",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input_file", action="store", type=str, help="Input file name")
    parser.add_argument("template", action="store", type=str, help="Choose template from "
                        "templates direcotry")
    parser.add_argument("--font-size", action="store", type=int, help="Override default font size",
                        default=110)
    parser.add_argument("--output-file", action="store", type=str, help="Output file name",
                        default="tarcze")
    parser.add_argument("--height-offset", action="store", type=int,
                        help="Height offset from the centre. Negative value means up, positive"
                        " means down", default=0)
    parser.add_argument("--width-offset", action="store", type=int,
                        help="Width offset from the centre. Negative value means left, positive"
                        " means right.", default=0)
    parser.add_argument("--font-name", action="store", type=str, help="Font name. Preferably path "
                        "to the .ttf file.", default='fonts/Times_New_Roman_Bold_Italic.ttf')
    parser.add_argument("--as-is", action="store_true", help="Fill exactly as in file")

    args = parser.parse_args()
    return args


# TODO: tidy this, its from shield_filler 1.0 but should be usefull for custom shields
def apply_name_heuristics(name_parts):
    print(name_parts)
    if len(name_parts[0]) > MAX_NAME_LEN:
        print("more splitting for name: ", name)
    if len(name_parts[-1]) > MAX_NAME_LEN and "-" in name_parts[-1]:
        surname_parts = name_parts[-1].split("-")
        name_parts = name_parts[:-1] + [surname_parts[0]] + ["-" + surname_parts[1]]
    if len(name_parts) == 2:
        height -= 30
    elif len(name_parts) == 3:
        if len(name_parts[0]) + len(name_parts[1]) < MAX_NAME_LEN - 1:
            name_parts = [name_parts[0] + " " + name_parts[1]] + name_parts[2:]
        height -= 20

    if any(name for name in name_parts if len(name) > MAX_NAME_LEN - 2):
        font_size_reduction = 10


# Single line village
single_line_village = ["Leska", "Solina", "Cisna", "Sanoka", "Lesko"]
first_in_line_words = {"i", "w", "Prezes", "Członek", "Proboszcz"}
always_in_one_line = {"sp. z o.o.", "Sp. z o.o.", "sp.z o.o.", "sp. j.", "Sp. J."}


def split_name(name: str, max_linex: int, max_line_len: int, template_name: str) -> list[str]:
    "Split name than update coords and font size depending on name parts"
    name_parts = name.split()
    name_parts = [name for name in name_parts if name not in {"–", "-"}]
    lines = []
    line = ""
    # TODO: before only 2 parts per line were allowed
    for name in name_parts:
        if (len(line) + len(name) + 1 <= max_line_len and
                (not line or name not in first_in_line_words)):
            if line:
                line += " "
            line += name
        else:
            # TODO: here or below sometimes empty string occurs
            if line and line != " ":
                lines.append(line)
            line = name
            if line in single_line_village:
                lines.append(line)
                line = ""
    if line and line != " ":
        lines.append(line)

    def _split_too_long(line: str, max_len) -> list[str]:
        if len(line) > max_len:
            if " " in line:
                return line.split()
            elif "-" in line:
                surname_parts = line.split("-")
                return [surname_parts[0],  "-" + surname_parts[1]]
            else:
                print("Unsplittable line: ", line)
                return [line]
        return [line]

    def _split_too_short(line: str) -> list[str]:
        if line in always_in_one_line:
            return [line]
        if len(line.split()) == 2 and "i" in line.split():
            return [line]
        return line.split(maxsplit=1)

    if len(lines) < max_linex:
        lines = [_split_too_long(line, max_line_len_for_pos(idx, len(lines), template_name))
                 for idx, line in enumerate(lines)]
        lines = list(itertools.chain.from_iterable(lines))

    if len(lines) < 3:
        more_lines = [_split_too_short(line) for line in lines]
        more_lines = list(itertools.chain.from_iterable(more_lines))
        if len(more_lines) < 5:
            lines = more_lines

    return lines


def create_tmp_output_dir(dir_name: str):
    "Create temporary output directory and remove it if it already exists"
    shutil.rmtree(dir_name, ignore_errors=True)
    os.mkdir(dir_name)
    return dir_name


def draw_on_shield(shield, lines: list[str], spacing: int, coords: tuple,
                   font: ImageFont.FreeTypeFont, output_path: str, border: bool):
    "Draw text on shield, with border or without"
    width, height = shield.size
    draw = ImageDraw.Draw(shield, mode="1")
    if not border:
        draw.rectangle((0, 0, width, height), fill="white")
    draw.fontmode = "1"
    draw.multiline_text(coords, anchor="mm", text="\n".join(lines),
                        font=font, align="center", spacing=spacing)
    filled_shield = shield.resize((width // 3, height // 3))
    filled_shield.save(f"{output_path}.bmp")


def fill_shield(name: str, output_path: str, no_border_output_path: str, coords: tuple,
                shield_template, arguments, max_name_len: int, max_lines: int, as_is=False):
    """
    Fill shield with given name in correct format
    """
    font = ImageFont.truetype(arguments.font_name, size=arguments.font_size * 3)

    # split too long ones
    font_size_reduction = 0
    spacing = 50
    if as_is:
        lines = name.splitlines()
    else:
        lines = split_name(name, max_lines, max_name_len, arguments.template)
    cor_x, cor_y = coords
    if len(lines) > max_lines + 2:
        print("Warning: Far too many lines!:", lines)
        font_size_reduction = 10
        spacing = 15
        coords = (cor_x, cor_y)
    elif len(lines) > max_lines + 1:
        print("Warning: Too many lines!:", lines)
        font_size_reduction = 7
        spacing = 27
        coords = (cor_x, cor_y)
    elif len(lines) > max_lines:
        print("Warning: long one!:", lines)
        font_size_reduction = 5
        spacing = 40
        coords = (cor_x, cor_y - 20)
    elif len(lines) < 4:
        spacing = 60

    #  if len(lines) == 2:
        #  # font_size_reduction = -5
        #  coords = (cor_x, cor_y - 30)

    #  if len(lines) == 3:
        #  # font_size_reduction = -3
        #  coords = (cor_x, cor_y - 30)

    if len(lines) in {2, 3, 4, 5}:
        coords = (cor_x, cor_y - 20)

    if len(lines) in {6}:
        print("max lines: ", lines)
        coords = (cor_x, cor_y - 40)

    if any(len(line) > max_name_len for line in lines):
        print("Warning: wide one!:", lines)
        font_size_reduction = 5

    if arguments.template == "szablony/nail_03.bmp":
        coords = (cor_x, cor_y - 60)
    if font_size_reduction:
        font = ImageFont.truetype(
            arguments.font_name, size=arguments.font_size * 3 - font_size_reduction * 3)

    draw_on_shield(shield_template.copy(), lines, spacing, coords, font, output_path, True)
    draw_on_shield(shield_template.copy(), lines, spacing,
                   coords, font, no_border_output_path, False)


def main():
    arguments = parse_args()

    # Create shield template and resize it 3 times for better quality
    shield_template = Image.open(arguments.template)
    shield_template = shield_template.resize(
        (shield_template.size[0] * 3, shield_template.size[1] * 3))
    width, height = shield_template.size
    center = (width/2 + arguments.width_offset, height/2 + arguments.height_offset)

    tmp_output_dir = create_tmp_output_dir("tmp_output")
    no_border_tmp_dir = create_tmp_output_dir("no_border_tmp_output")
    max_name_len, max_lines = line_limits(arguments.template)

    with open(arguments.input_file, "r", encoding="utf-8") as file:
        if arguments.as_is:
            data = file.read()
            names = re.split(r"(?:\r?\n){2,}", data.strip())
        else:
            names = file.read().splitlines()
        names = [name.strip() for name in names if name]

    for idx, name in enumerate(names, start=1):
        output_path = tmp_output_dir + "/" + str(idx) + "_" + "_".join(name.split())
        no_border_output_path = no_border_tmp_dir + "/" + str(idx) + "_" + "_".join(name.split())
        fill_shield(name, output_path, no_border_output_path, center, shield_template,
                    arguments, max_name_len, max_lines, arguments.as_is)

    print(f"Filled {len(names)} shields and saved them in {arguments.output_file}.zip")
    shutil.make_archive(arguments.output_file, 'zip', no_border_tmp_dir)
    shutil.make_archive(arguments.output_file + "_kontur", 'zip', tmp_output_dir)
    shutil.rmtree(no_border_tmp_dir)


if __name__ == '__main__':
    main()
