#!/usr/bin/env python
import sys
from pathlib import Path
import PySimpleGUI as sg
import os
from PIL import Image, ImageTk
import io
import shutil
from src.shield_filler import fill_shield, GlobalOptions, Nail


def get_img_data(filename: str, maxsize=(1200, 850), first=False):
    """
    Generate image for image viewer
    """
    img = Image.open(filename)
    img.thumbnail(maxsize)
    if first:                     # tkinter is inactive the first time
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
                63, 20), key='-LISTBOX-', font='_ 13')],
            [sg.Column([[sg.Text("Ustawienia globalne:", font='_ 13')]]),
             sg.Column([[sg.Text("Rozmiar czcionki", font='_ 13')]]),
                sg.Column([[sg.InputText(global_opts.font_size, key="-DEFAULT-FONT-SIZE-",
                                         size=(5, 1), font='_ 13')]]),
             sg.Column([[sg.Button("Odśwież wszystkie", key="-REFRESH-ALL-", font='_ 13')]]),
             ],
            [sg.Text("Rozbity tekst:", font='_ 13')],
            [sg.Multiline(key="-FORMATTED-TEXT-", size=(63, 10), expand_y=True, font='_ 13')],
            [sg.Column([[sg.Text("Rozmiar czcionki", font='_ 13')]]),
             sg.Column([[sg.InputText(global_opts.font_size, key="-FONT-SIZE-",
                                      size=(5, 1), font='_ 13')]]),
             sg.Column([[sg.VSeperator(pad=(0, 0))]]),
             sg.Column([[sg.Text("Interlinia", font='_ 13')]]),
             sg.Column(
                 [[sg.InputText(global_opts.spacing, key="-SPACING-", size=(5, 1), font='_ 13')]]),
             sg.Column([[sg.VSeperator(pad=(0, 0))]]),
             sg.Column([[sg.Text("Translacja (oś Y)", font='_ 13')]]),
             sg.Column([[sg.InputText(0, key="-TRANSLATION-", size=(5, 1), font='_ 13')]]),
             ],
            [sg.Column([[sg.Button("Odśwież", key="-REFRESH-", font='_ 13')]]),
             sg.Column([[sg.VSeperator(pad=(0, 0))]]),
             sg.Column([[sg.Button("Zapisz i zakończ", key="-SAVE-CLOSE-", font='_ 13')]]),
             ]
            # TODO: opcja wczytywania zformatowanych - ten as_is
            # TODO: Zapis pliku ze sformatowanym tekstem - jakieś _formatted.txt czy coś
        ], expand_x=True),
            sg.VSeperator(pad=(0, 0)),
            # TODO: we should have it rendered and start from first one here
            sg.Column([[sg.Image(data=get_img_data(global_opts.tmpl_filename,
                                                   first=True), key="-IMAGE-")]], expand_x=True)
        ]
    ]
    return layout


def main_window(nails: list[Nail], global_opts: GlobalOptions):
    layout = create_layout([nail.text for nail in nails], global_opts)
    window = sg.Window('Shield filler', layout, return_keyboard_events=True,
                       location=(0, 0), use_default_focus=False, resizable=True,
                       finalize=True)
    window.Maximize()
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            shutil.rmtree(global_opts.no_border_tmp_dir)
            shutil.rmtree(global_opts.tmp_output_dir)
            sys.exit()
        elif event == '-LISTBOX-':
            row: int = window["-LISTBOX-"].get_indexes()[0]
            window["-FORMATTED-TEXT-"].update(value="\n".join(nails[row].formatted_text))
            window["-IMAGE-"].update(data=get_img_data(nails[row].bmp_filename(
                global_opts.tmp_output_dir)))
            window["-SPACING-"].update(value=nails[row].spacing)
            window["-FONT-SIZE-"].update(value=nails[row].font_size)
            window["-TRANSLATION-"].update(value=nails[row].center[1] - global_opts.center[1])
        elif event == '-REFRESH-':
            row: int = window["-LISTBOX-"].get_indexes()[0]
            nails[row].formatted_text = values["-FORMATTED-TEXT-"].splitlines()
            nails[row].font_size = int(values["-FONT-SIZE-"])
            nails[row].spacing = int(values["-SPACING-"])
            (x, y) = global_opts.center
            nails[row].center = (x, y + float(values["-TRANSLATION-"]))
            fill_shield(nails[row], global_opts=global_opts)
            window["-IMAGE-"].update(data=get_img_data(nails[row].bmp_filename(
                global_opts.tmp_output_dir)))
        elif event == '-REFRESH-ALL-':
            row: int = window["-LISTBOX-"].get_indexes()[0]
            global_opts.font_size = int(values["-DEFAULT-FONT-SIZE-"])
            format_nails(nails, global_opts, True)
            window["-IMAGE-"].update(data=get_img_data(nails[row].bmp_filename(
                global_opts.tmp_output_dir)))
        elif event == '-SAVE-CLOSE-':
            list_base_name = Path(global_opts.list_filename).stem
            shutil.make_archive(list_base_name, 'zip', global_opts.no_border_tmp_dir)
            shutil.make_archive(list_base_name + "_kontur", 'zip', global_opts.tmp_output_dir)
            shutil.rmtree(global_opts.no_border_tmp_dir)
            sys.exit()

        else:
            pass


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


def format_nails(nails: list[Nail], global_options: GlobalOptions, update_global_opt=False):
    """
    Run formatting and filling on all nails
    """
    for nail in nails:
        if update_global_opt:
            nail.font_size = global_options.font_size
        fill_shield(nail, global_options)


def main():
    list_filename, templ_filename = initial_window()
    tmp_output_dir = create_tmp_output_dir("tmp_output")
    no_border_tmp_dir = create_tmp_output_dir("no_border_tmp_output")
    # TODO: configurable font_name. Dunno how it will work on windows
    font_name = "fonts/seagull.ttf"
    global_options = GlobalOptions(tmp_output_dir, no_border_tmp_dir, templ_filename, list_filename,
                                   font_name)
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

    format_nails(nails, global_options)
    main_window(nails, global_options)


if __name__ == '__main__':
    sg.theme('Dark Blue 13')
    main()
