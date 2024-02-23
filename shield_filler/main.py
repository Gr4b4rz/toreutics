#!/usr/bin/env python
import json
import sys
import os
import io
import shutil
import subprocess
from pathlib import Path
from dataclasses import asdict
import PySimpleGUI as sg
from PIL import Image, ImageTk
from src.shield_filler import fill_shield, GlobalOptions, Nail


def get_img_data(filename: str, maxsize=(1200, 850), first=False):
    """
    Generate image for image viewer
    """
    img = Image.open(filename)
    img.thumbnail(maxsize)
    if first:  # tkinter is inactive the first time
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        del img
        return bio.getvalue()
    return ImageTk.PhotoImage(img)


def create_layout(names: list, global_opts: GlobalOptions):
    sg.theme('Dark Blue 13')
    layout = [
        [sg.Column([
            [sg.Text(global_opts.list_filename, font='_ 13')],
            [sg.Listbox(values=names, change_submits=True, size=(
                80, 20), key='-LISTBOX-', font='_ 13')],
            [
                sg.Column([[sg.Text("Ustawienia globalne:", font='_ 13')]]),
                sg.Column([[sg.VSeperator(pad=(0, 0))]]),
                sg.Column([[sg.Button("Odśwież wszystkie", key="-REFRESH-ALL-", font='_ 13')]]),
            ],
            [
                sg.Column([[sg.Text("Rozmiar czcionki", font='_ 13')]]),
                sg.Column([[sg.InputText(str(global_opts.font_size), key="-DEFAULT-FONT-SIZE-",
                                         size=(5, 1), font='_ 13')]]),
                sg.Column([[sg.VSeperator(pad=(0, 0))]]),
                sg.Column([[sg.Text("Interlinia", font='_ 13')]]),
                sg.Column([[sg.InputText(str(global_opts.spacing), key="-GLOBAL-SPACING-",
                                         size=(5, 1), font='_ 13')]]),
                sg.Column([[sg.VSeperator(pad=(0, 0))]]),
                sg.Column([[sg.Text("Translacja (oś Y)", font='_ 13')]]),
                sg.Column([[sg.InputText(str(global_opts.translation), key="-GLOBAL-TRANSLATION-",
                                         size=(5, 1), font='_ 13')]]),
            ],
            [sg.Text("Rozbity tekst:", font='_ 13')],
            [sg.Multiline(key="-FORMATTED-TEXT-", size=(80, 10), expand_y=True, font='_ 13')],
            [sg.Column([[sg.Text("Rozmiar czcionki", font='_ 13')]]),
             sg.Column([[sg.InputText(str(global_opts.font_size), key="-FONT-SIZE-",
                                      size=(5, 1), font='_ 13')]]),
             sg.Column([[sg.VSeperator(pad=(0, 0))]]),
             sg.Column([[sg.Text("Interlinia", font='_ 13')]]),
             sg.Column(
                 [[sg.InputText(str(global_opts.spacing),
                                key="-SPACING-", size=(5, 1), font='_ 13')]]),
             sg.Column([[sg.VSeperator(pad=(0, 0))]]),
             sg.Column([[sg.Text("Translacja (oś Y)", font='_ 13')]]),
             sg.Column([[sg.InputText("0", key="-TRANSLATION-", size=(5, 1), font='_ 13')]]),
             ],
            [sg.Column([[sg.Button("Zapisz i Odśwież", key="-REFRESH-", font='_ 13')]]),
             sg.Column([[sg.VSeperator(pad=(0, 0))]]),
             sg.Column([[sg.Button("Zapisz i zakończ", key="-SAVE-CLOSE-", font='_ 13')]]),
             ]
        ], expand_x=False),
            sg.VSeperator(pad=(0, 0)),
            sg.Column([[sg.Image(data=get_img_data(global_opts.tmpl_filename,
                                                   first=True), key="-IMAGE-")]], expand_x=True)
        ]
    ]
    return layout


def update_view(window: sg.Window, nails: list[Nail], global_opts: GlobalOptions):
    """
    Update view after clicking on a row, or after changing current row with an arrow button
    """
    row: int = window["-LISTBOX-"].get_indexes()[0]
    window["-FORMATTED-TEXT-"].update(value="\n".join(nails[row].formatted_text))
    window["-IMAGE-"].update(data=get_img_data(nails[row].bmp_filename(
        global_opts.tmp_output_dir)))
    window["-SPACING-"].update(value=nails[row].spacing or global_opts.spacing)
    window["-FONT-SIZE-"].update(value=nails[row].font_size)
    window["-TRANSLATION-"].update(value=nails[row].translation)


def main_window(nails: list[Nail], global_opts: GlobalOptions):
    layout = create_layout([nail.text for nail in nails], global_opts)
    window = sg.Window('Shield filler', layout, return_keyboard_events=True,
                       location=(0, 0), use_default_focus=False, resizable=True,
                       finalize=True)
    window.Maximize()
    window['-LISTBOX-'].update(set_to_index=0)
    update_view(window, nails, global_opts)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            shutil.rmtree(global_opts.no_border_tmp_dir)
            shutil.rmtree(global_opts.tmp_output_dir)
            sys.exit()
        elif event == "Down:116":
            row: int = window["-LISTBOX-"].get_indexes()[0]
            if row < len(nails) - 1:
                window['-LISTBOX-'].update(set_to_index=row+1)
            update_view(window, nails, global_opts)
        elif event == "Up:111":
            row: int = window["-LISTBOX-"].get_indexes()[0]
            if row > 0:
                window['-LISTBOX-'].update(set_to_index=row-1)
            update_view(window, nails, global_opts)
        elif event == '-LISTBOX-':
            update_view(window, nails, global_opts)
        elif event == '-REFRESH-':
            row: int = window["-LISTBOX-"].get_indexes()[0]
            nails[row].formatted_text = values["-FORMATTED-TEXT-"].splitlines()
            nails[row].font_size = int(values["-FONT-SIZE-"])
            if int(values["-SPACING-"]) != global_opts.spacing:
                nails[row].spacing = int(values["-SPACING-"])
            nails[row].translation = float(values["-TRANSLATION-"])
            fill_shield(nails[row], global_opts=global_opts)
            window["-IMAGE-"].update(data=get_img_data(nails[row].bmp_filename(
                global_opts.tmp_output_dir)))
        elif event == '-REFRESH-ALL-':
            row: int = window["-LISTBOX-"].get_indexes()[0]
            global_opts.font_size = int(values["-DEFAULT-FONT-SIZE-"])
            global_opts.translation = float(values["-GLOBAL-TRANSLATION-"])
            global_opts.spacing = int(values["-GLOBAL-SPACING-"])
            format_nails(nails, global_opts, True)
            window["-IMAGE-"].update(data=get_img_data(nails[row].bmp_filename(
                global_opts.tmp_output_dir)))
        elif event == '-SAVE-CLOSE-':
            list_base_name = Path(global_opts.list_filename).stem
            final_dir = os.path.join("projekty", list_base_name)
            os.makedirs(final_dir, exist_ok=True)
            save_current_state(final_dir, nails, global_opts)
            shutil.make_archive(os.path.join(final_dir, list_base_name),
                                'zip', global_opts.no_border_tmp_dir)
            shutil.make_archive(os.path.join(final_dir, list_base_name + "_kontur"),
                                'zip', global_opts.tmp_output_dir)
            shutil.rmtree(global_opts.no_border_tmp_dir)
            open_folder(final_dir)
            sys.exit()

        else:
            pass


def open_folder(dirname: str):
    """
    Open folder on a windows/mac/linux file browser
    """
    if sys.platform == 'win32':
        subprocess.Popen(['start', os.path.abspath(dirname)], shell=True)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', os.path.abspath(dirname)])
    else:
        subprocess.Popen(['xdg-open', os.path.abspath(dirname)])


def read_cache(directory: str) -> tuple[list[dict], dict]:
    """
    Read settings cache from json files
    """
    with open(os.path.join(directory, "nails.json"), "r", encoding="UTF-8") as f:
        nails_json = json.load(f)
    with open(os.path.join(directory, "global_opts.json"), "r", encoding="UTF-8") as f:
        global_opts_json = json.load(f)

    return nails_json, global_opts_json


def save_current_state(directory, nails: list[Nail], global_opts: GlobalOptions):
    """
    Save current state (each nail and global settings) in the .json files
    """
    nails_filename = os.path.join(directory, "nails.json")
    global_opts_filename = os.path.join(directory, "global_opts.json")
    with open(nails_filename, "w", encoding="UTF-8") as f:
        nails_dict = [asdict(nail) for nail in nails]
        json.dump(nails_dict, f)
    with open(global_opts_filename, "w", encoding="UTF-8") as f:
        json.dump(global_opts.get_cache(), f)


def create_tmp_output_dir(dir_name: str):
    "Create temporary output directory and remove it if it already exists"
    shutil.rmtree(dir_name, ignore_errors=True)
    os.mkdir(dir_name)
    return dir_name


def initial_window() -> tuple:
    """
    Open login window. Load remembered credentials from secrets.json file.
    """
    layout = [
        [[sg.Text("Lista", size=7), sg.Input(),
            sg.FileBrowse(key="-NAMES-FILE-", initial_folder=os.path.abspath("listy"))]],
        [[sg.Text("Szablon", size=7), sg.Input(),
            sg.FileBrowse(key="-TEMPLATE-FILE-", initial_folder=os.path.abspath("szablony"))]],
        [[sg.Text("Projekt", size=7), sg.Input("Wybierz projekt, "
                                               "jeśli chcesz kontynuować pracę"),
            sg.FolderBrowse(key="-PROJECTS-DIR-", initial_folder=os.path.abspath("projekty"),
                            tooltip="Wybierz folder, by kontynuować pracę")]],
        [sg.Submit('OK', key='-OK-'), sg.Cancel(key='-CANCEL-')],
    ]

    window = sg.Window('Wybór listy gwoździ i szablonu', layout,
                       return_keyboard_events=True,
                       grab_anywhere=False, finalize=True)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            sys.exit()
        elif event == "-OK-":
            window.close()
            return (values["-NAMES-FILE-"], values["-TEMPLATE-FILE-"], values["-PROJECTS-DIR-"])

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


def format_nails(nails: list[Nail], global_options: GlobalOptions, update_global_opt=False):
    """
    Run formatting and filling on all nails
    """
    for nail in nails:
        if update_global_opt:
            nail.font_size = global_options.font_size
        fill_shield(nail, global_options)


def main():
    list_filename, templ_filename, project_dir = initial_window()
    tmp_output_dir = create_tmp_output_dir("tmp_output")
    no_border_tmp_dir = create_tmp_output_dir("no_border_tmp_output")
    # TODO: configurable font_name. Dunno how it will work on windows
    font_name = "fonts/seagull.ttf"
    global_options = GlobalOptions(tmp_output_dir, no_border_tmp_dir, templ_filename, list_filename,
                                   font_name)
    try:
        with open(list_filename, "r", encoding="utf-8") as file:
            names = file.read().splitlines()
    except UnicodeDecodeError:
        with open(list_filename, "r", encoding="cp1250") as file:
            names = file.read().splitlines()

    nails = [Nail(
        idx=idx,
        text=name.strip(),
        formatted_text=[],
        font_size=global_options.font_size,
        translation=global_options.translation,
    ) for idx, name in enumerate(names, start=1) if name]

    if project_dir:
        nails_cache, global_cache = read_cache(project_dir)
        nails = [nail.apply_cache(nails_cache) for nail in nails]
        global_options.load_cache(global_cache)

    format_nails(nails, global_options)
    main_window(nails, global_options)


if __name__ == '__main__':
    sg.theme('Dark Blue 13')
    main()
