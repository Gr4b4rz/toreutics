#!/usr/bin/env python
import sys
from enum import Enum
from dataclasses import dataclass
import PySimpleGUI as sg
import os
from PIL import Image, ImageTk
import io
import shutil
from src.line_lengths import line_limits, max_line_len_for_pos

"""
Simple Image Browser based on PySimpleGUI
--------------------------------------------
There are some improvements compared to the PNG browser of the repository:
1. Paging is cyclic, i.e. automatically wraps around if file index is outside
2. Supports all file types that are valid PIL images
3. Limits the maximum form size to the physical screen
4. When selecting an image from the listbox, subsequent paging uses its index
5. Paging performance improved significantly because of using PIL

Dependecies
------------
Python3
PIL
"""


def get_img_data(filename: str, maxsize=(1200, 850), first=False):
    """Generate image data using PIL
    """
    img = Image.open(filename)
    img.thumbnail(maxsize)
    if first:                     # tkinter is inactive the first time
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()
    return ImageTk.PhotoImage(img)
# ------------------------------------------------------------------------------


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
        return directory + "/" + str(self.idx) + "_" + "_".join(self.text.split())


class GlobalOptions:
    """
    Global options that usually depend on nail type
    """

    def __init__(self, tmp_output_dir: str, no_border_tmp_dir: str, templ_file: str):
        self.tmpl_filename = templ_file
        self.tmp_output_dir = tmp_output_dir
        self.no_border_tmp_dir = no_border_tmp_dir
        self.shield_template = Image.open(templ_file)
        self.center = (self.shield_template.size[0] / 2, self.shield_template.size[1] / 2)
        self.nail_type = self.get_nail_type(templ_file)
        self.max_chars, self.max_lines = line_limits(templ_file)
        self.font_size = self.get_font_size(self.nail_type)
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


def create_layout(names: list, global_opts: GlobalOptions):
    sg.theme('Dark Blue 13')
    layout = [
        [sg.Column([
            [sg.Text("Rozbity tekst:", font='_ 13')],
            [sg.Listbox(values=names, change_submits=True, size=(60, 30), key='-LISTBOX-')],
            [sg.Text("Rozbity tekst:", font='_ 13')],
            [sg.Multiline(key="-FORMATTED-TEXT-", size=(45, 10), expand_y=True, font='_ 13')],
            [sg.Column([[sg.Text("Rozmiar czcionki", font='_ 13')]]),
             sg.Column([[sg.InputText(key="-FONT SIZE-", size=(5, 1), font='_ 13')]]),
             sg.Column([[sg.VSeperator(pad=(0, 0))]]),
             sg.Column([[sg.Text("Interlinia", font='_ 13')]]),
             sg.Column([[sg.InputText(key="-SPACING-", size=(5, 1), font='_ 13')]]),
             sg.Column([[sg.VSeperator(pad=(0, 0))]]),
             sg.Column([[sg.Text("Translacja (oś Y)", font='_ 13')]]),
             sg.Column([[sg.InputText(key="-TRANSLATION-", size=(5, 1), font='_ 13')]]),
        ]),
            sg.VSeperator(pad=(0, 0)),
            sg.Column([[sg.Image(data=get_img_data(global_opts.tmpl_filename,
                                                   first=True), key="-IMAGE-")]])
        ]
    ]
    return layout


def main_window(nails: list[Nail], global_opts: GlobalOptions):
    # TODO: some structure for name. With raw_text, formatted, filename, font, spacing etc
    layout = create_layout([nail.text for nail in nails], global_opts)
    window = sg.Window('Shield filler', layout, return_keyboard_events=True,
                       location=(0, 0), use_default_focus=False, resizable=True,
                       finalize=True)
    i = 0
    while True:
        # read the form
        event, values = window.read()
        print(event, values)
        # perform button and keyboard operations
        if event == sg.WIN_CLOSED:
            break
        elif event in ('Down:40', 'Next:34'):
            i += 1
            if i >= len(nails):
                i -= len(nails)
            filename = os.path.join(tmp_dir, nails[i])
        elif event in ('Up:38', 'Prior:33'):
            i -= 1
            if i < 0:
                i = len(nails) + i
            filename = os.path.join(tmp_dir, nails[i])
        elif event == '-LISTBOX-':            # something from the listbox
            f = values["-LISTBOX-"][0]            # selected filename
            filename = os.path.join(tmp_dir, f)  # read this file
            i = names.index(f)                 # update running index
        else:
            pass

        # update window with new image
        # TODO: it needs event or sth
        # window["-IMAGE-"].update(data=get_img_data(filename, first=False))

    window.close()


def create_tmp_output_dir(dir_name: str):
    "Create temporary output directory and remove it if it already exists"
    shutil.rmtree(dir_name, ignore_errors=True)
    os.mkdir(dir_name)
    return dir_name


def initial_window():
    """
    Open login window. Load remembered credentials from secrets.json file.
    """
    layout = [
        [[sg.Text("Lista", size=7), sg.Input(),
            sg.FileBrowse(key="-NAMES-FILE-", initial_folder=os.path.abspath("listy"))]],
        [[sg.Text("Szablon", size=7), sg.Input(),
            sg.FileBrowse(key="-TEMPLATE-FILE-", initial_folder=os.path.abspath("szablony"))]],
        [sg.Submit('OK', key='-OK-'), sg.Cancel(key='-CANCEL-')],
    ]

    window = sg.Window('Wybór listy gwoździ i szablonu', layout,
                       return_keyboard_events=True,
                       grab_anywhere=False)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            sys.exit()
        elif event == "-OK-":
            window.close()
            return (values["-NAMES-FILE-"], values["-TEMPLATE-FILE-"])

        elif event == "-CANCEL-":
            sys.exit()


def get_nail_type(filename: str):
    if "nail_01" in filename:
        return 1
    if "nail_02" in filename:
        return 2
    if "nail_03" in filename:
        return 3
    return 0


def main():
    tmp_output_dir = create_tmp_output_dir("tmp_output")
    no_border_tmp_dir = create_tmp_output_dir("no_border_tmp_output")
    # list_filename, templ_filename = initial_window()
    list_filename = "listy/bór.txt"
    templ_filename = "szablony/nail_01.bmp"
    global_options = GlobalOptions(tmp_output_dir, no_border_tmp_dir, templ_filename)
    with open(list_filename, "r", encoding="utf-8") as file:
        names = file.read().splitlines()

    nails = [Nail(
        idx=idx,
        text=name.strip(),
        formatted_text=[],
        output_path=templ_filename,
        font_size=global_options.font_size,
        spacing=global_options.spacing,
        center=global_options.center
    ) for idx, name in enumerate(names, start=1) if name]

    main_window(nails, global_options)


if __name__ == '__main__':
    sg.theme('Dark Blue 13')
    main()
