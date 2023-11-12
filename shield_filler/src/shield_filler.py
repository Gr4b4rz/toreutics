import itertools
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
from src.line_lengths import line_limits, max_line_len_for_pos


@dataclass
class Nail:
    idx: int
    text: str
    formatted_text: list[str]
    output_path: str
    font_size: int
    spacing: int
    center: tuple

    def bmp_filename(self, directory: str):
        return directory + "/" + str(self.idx) + "_" + "_".join(self.text.split()) + ".bmp"


class GlobalOptions:
    """
    Global options that usually depend on nail type
    """

    def __init__(self, tmp_output_dir: str, no_border_tmp_dir: str, templ_file: str,
                 list_filename: str, font_name: str):
        self.tmpl_filename = templ_file
        self.list_filename = list_filename
        self.tmp_output_dir = tmp_output_dir
        self.no_border_tmp_dir = no_border_tmp_dir
        self.shield_template = Image.open(templ_file)
        self.shield_template = self.shield_template.resize(
            (self.shield_template.size[0] * 3, self.shield_template.size[1] * 3))
        self.center = (self.shield_template.size[0] / 2, self.shield_template.size[1] / 2)
        self.nail_type = self.get_nail_type(templ_file)
        self.max_chars, self.max_lines = line_limits(self.nail_type)
        self.font_size = self.get_font_size(self.nail_type)
        self.font_name = font_name
        self.spacing = 50

    def get_nail_type(self, filename: str):
        if "nail_01" in filename:
            return 1
        if "nail_02" in filename:
            return 2
        if "nail_03" in filename:
            return 3
        return 0

    def get_font_size(self, nail_type: int):
        if nail_type == 1:
            return 52
        if nail_type == 2:
            return 45
        if nail_type == 3:
            return 70
        return 52


def fill_shield(nail: Nail, global_opts: GlobalOptions):
    """
    Fill shield with given name in correct format
    """
    output_path = nail.bmp_filename(global_opts.tmp_output_dir)
    no_border_output_path = nail.bmp_filename(global_opts.no_border_tmp_dir)
    font = ImageFont.truetype(global_opts.font_name, size=nail.font_size * 3)

    font_size_reduction = 0
    if not nail.formatted_text:
        nail.formatted_text = split_name(nail.text, global_opts.max_lines, global_opts.max_chars,
                                         global_opts.nail_type)
        cor_x, cor_y = nail.center
        if len(nail.formatted_text) > global_opts.max_lines + 2:
            print("Warning: Far too many lines!:", nail.formatted_text)
            font_size_reduction = 10
            nail.spacing = 15
        elif len(nail.formatted_text) > global_opts.max_lines + 1:
            print("Warning: Too many lines!:", nail.formatted_text)
            font_size_reduction = 7
            nail.spacing = 27
        elif len(nail.formatted_text) > global_opts.max_lines:
            print("Warning: long one!:", nail.formatted_text)
            font_size_reduction = 5
            nail.spacing = 40
            nail.center = (cor_x, cor_y - 20)
        elif len(nail.formatted_text) < 4:
            nail.spacing = 60

        #  if len(nail.formatted_text) == 2:
            #  # font_size_reduction = -5
            #  coords = (cor_x, cor_y - 30)

        #  if len(nail.formatted_text) == 3:
            #  # font_size_reduction = -3
            #  coords = (cor_x, cor_y - 30)

        if len(nail.formatted_text) in {2, 3, 4, 5}:
            nail.center = (cor_x, cor_y - 20)

        if len(nail.formatted_text) in {6}:
            print("max lines: ", nail.formatted_text)
            nail.center = (cor_x, cor_y - 40)

        if any(len(line) > global_opts.max_chars for line in nail.formatted_text):
            print("Warning: wide one!:", nail.formatted_text)
            font_size_reduction = 5

        if global_opts.nail_type == 3:
            nail.center = (cor_x, cor_y - 60)
        if font_size_reduction:
            nail.font_size -= font_size_reduction
            font = ImageFont.truetype(global_opts.font_name, size=nail.font_size * 3)

    draw_on_shield(global_opts.shield_template.copy(), nail.formatted_text, nail.spacing,
                   nail.center, font, output_path, True)
    draw_on_shield(global_opts.shield_template.copy(), nail.formatted_text, nail.spacing,
                   nail.center, font, no_border_output_path, False)


# Single line village
single_line_village = ["Leska", "Solina", "Cisna", "Sanoka", "Lesko"]
first_in_line_words = {"i", "w", "Prezes", "Członek", "Proboszcz"}
always_in_one_line = {"sp. z o.o.", "Sp. z o.o.", "sp.z o.o.", "sp. j.", "Sp. J."}


def split_name(name: str, max_linex: int, max_line_len: int, nail_type: int) -> list[str]:
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
        lines = [_split_too_long(line, max_line_len_for_pos(idx, len(lines), nail_type))
                 for idx, line in enumerate(lines)]
        lines = list(itertools.chain.from_iterable(lines))

    if len(lines) < 3:
        more_lines = [_split_too_short(line) for line in lines]
        more_lines = list(itertools.chain.from_iterable(more_lines))
        if len(more_lines) < 5:
            lines = more_lines

    return lines


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
    filled_shield.save(output_path)
