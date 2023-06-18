#!/usr/bin/python3
import argparse
import shutil
import os

from PIL import Image, ImageDraw, ImageFont

MAX_NAME_LEN = 13


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

    args = parser.parse_args()
    return args


def split_name(name: str, coords):
    "Split name than update coords and font size depending on name parts"
    width, height = coords
    font_size_reduction = None
    name_parts = name.split()
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
    return "\n".join(name_parts), (width, height), font_size_reduction


def main():
    arguments = parse_args()
    shield_template = Image.open(arguments.template)
    tmp_output_dir = "tmp_output"
    os.mkdir(tmp_output_dir)
    width, height = shield_template.size
    center = (width/2 + arguments.width_offset, height/2 + arguments.height_offset)

    with open(arguments.input_file, "r") as f:
        names = f.read().splitlines()

    for idx, name in enumerate(names, start=1):
        coords = center
        filled_shield = shield_template.copy()
        font = ImageFont.truetype(arguments.font_name, size=arguments.font_size)
        output_name = tmp_output_dir + "/" + str(idx) + "_" + "_".join(name.split())

        # split too long ones
        if len(name) > MAX_NAME_LEN:
            name, coords, font_size_reduction = split_name(name, coords)
            if font_size_reduction:
                font = ImageFont.truetype(
                    arguments.font_name, size=arguments.font_size - font_size_reduction)
        elif len(name) > MAX_NAME_LEN - 1:
            font = ImageFont.truetype(arguments.font_name, size=arguments.font_size - 10)

        draw = ImageDraw.Draw(filled_shield)
        draw.fontmode = "L"
        draw.multiline_text(coords, anchor="mm", text=name, font=font, align="center")
        filled_shield.save(f"{output_name}.bmp")

    print(f"Filled {len(names)} shields and saved them in {arguments.output_file}.zip")
    shutil.make_archive(arguments.output_file, 'zip', tmp_output_dir)
    shutil.rmtree(tmp_output_dir)


if __name__ == '__main__':
    main()
