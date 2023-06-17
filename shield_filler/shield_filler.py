#!/usr/bin/python3
import shutil
import os

from PIL import Image, ImageDraw, ImageFont

MAX_NAME_LEN = 13
FONT_SIZE = 110


def split_name(name: str, coords):
    "Split name than update coords and font size depending on name parts"
    width, height = coords
    font_size_reduction = None
    name_parts = name.split()
    if len(name_parts[0]) > MAX_NAME_LEN:
        print("more splitting for name: ", name)
    if len(name_parts[-1]) > MAX_NAME_LEN and "-" in name_parts[-1]:
        surname_parts = name_parts[-1].split("-")
        name_parts = name_parts[:-1] + \
            [surname_parts[0]] + ["-" + surname_parts[1]]
    if len(name_parts) == 2:
        height -= 30
    elif len(name_parts) == 3:
        if len(name_parts[0]) + len(name_parts[1]) < MAX_NAME_LEN - 1:
            name_parts = [name_parts[0] + " " + name_parts[1]] + name_parts[2:]
        height -= 20
    if any(name for name in name_parts if len(name) > MAX_NAME_LEN - 2):
        font_size_reduction = 10
    return "\n".join(name_parts), (width, height), font_size_reduction


shield_template = Image.open('templates/shield.bmp')
font_name = 'fonts/Times_New_Roman_Bold_Italic.ttf'
input_file = "names_example.txt"
os.mkdir("output")
width, height = shield_template.size
# this + 70 is because empty field is usually below img center
center = (width/2, height/2 + 70)

with open(input_file, "r") as f:
    names = f.read().splitlines()
duplicates_count = {}

for idx, name in enumerate(names, start=1):
    coords = center
    filled_shield = shield_template.copy()
    font = ImageFont.truetype(font_name, size=FONT_SIZE)
    output_name = "output/" + str(idx) + "_" + "_".join(name.split())

    # split too long ones
    if len(name) > MAX_NAME_LEN:
        name, coords, font_size_reduction = split_name(name, coords)
        if font_size_reduction:
            font = ImageFont.truetype(font_name, size=FONT_SIZE - font_size_reduction)
    elif len(name) > MAX_NAME_LEN - 1:
        font = ImageFont.truetype(font_name, size=FONT_SIZE - 10)

    draw = ImageDraw.Draw(filled_shield)
    draw.fontmode = "L"
    draw.multiline_text(coords, anchor="mm", text=name,
                        font=font, align="center")
    filled_shield.save(f"{output_name}.bmp")


print(f"Filled {len(names)} shields and saved them in output.zip")
shutil.make_archive("tarcze", 'zip', "output")
# shutil.rmtree("output")
