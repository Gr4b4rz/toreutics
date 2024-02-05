import os
import sys
import subprocess
from typing import Optional
from collections import defaultdict
import PySimpleGUI as sg
from src.dpd import generate_labels, Shipment, ShipmentDetails, Credentials
from src.mssql import get_active_transactions, refresh_transaction

BLANK_BOX = '☐'
CHECKED_BOX = '🗹'


def create_layout(table_data: list, table_headings: list):
    sg.theme('Dark Blue 13')
    layout = [
        [sg.Table(table_data, table_headings, size=(80, 40), key="-TRANS-", max_col_width=35,
                  display_row_numbers=True, justification='center', expand_x=False, expand_y=False,
                  vertical_scroll_only=False, enable_click_events=True, font='_ 13', num_rows=20)],
        [
            sg.Column([
                [sg.Column([[sg.Checkbox("Przesyłka pobraniowa", enable_events=True, key="-COD-",
                                         font='_ 13')]]),
                 sg.VSeperator(pad=(0, 0)),
                 sg.Column([[sg.Checkbox("Przesyłka NEXTDAY", enable_events=True,
                                         key="-NEXTDAY-", font='_ 13')]]),
                 sg.VSeperator(pad=(0, 0)),
                 sg.Column([[sg.Text("Waga [kg]:", font='_ 13')]]),
                 sg.Column([[sg.InputText("1.0", key="-WEIGHT-", font='_ 13', size=(5, 1))]]),
                 sg.VSeperator(pad=(0, 0)),
                 sg.Column([[sg.Button("Odśwież wiersz", enable_events=True, key="-REFRESH-ONE-",
                                       font='_ 13')]]),
                 ],
                [sg.Column([[sg.Text("Imię i nazwisko odbiorcy:", font='_ 13')]]),
                 sg.Column([[sg.InputText(key="-RECEIVER NAME-", font='_ 13')]])],
                [sg.Column([[sg.Button("Geneneruj Etykiety DPD", enable_events=True,
                           key="-PRINT LABEL-", font='_ 13')]]),
                 sg.Column([[sg.Button("Folder z etykietami", font='_ 13', key="-OPEN FOLDER-",
                                       enable_events=True)]]),
                 sg.Column([[sg.Button("Odśwież tabelę", enable_events=True, key="-REFRESH-",
                                       font='_ 13')]]),
                 sg.Column([[sg.Button("Odznacz wszystkie", enable_events=True, key="-UNCHECK-",
                                       font='_ 13')]]),
                 ],
                [sg.Text(size=(100, 1), key="-INFO2-", font='_ 15', text_color="red")],
                [sg.Text(size=(100, 9), key="-INFO1-", font='_ 14')],
            ], size=(1000, 450), vertical_alignment="top"),
            sg.VSeperator(pad=(0, 0)),
            sg.Column([
                [sg.Image(data=b'', key="-PDF-")]
            ])

        ]
    ]

    return layout


def dpd_login():
    """
    Open login window. Load remembered credentials from secrets.json file.
    """
    last_credentials = Credentials.from_file(os.path.abspath("secrets.json"), True)
    layout = [
        [sg.Text('Logowanie do DPD', size=(16, 1), font='Any 15')],
        [sg.Text('Login'), sg.Input(default_text=last_credentials.login, key='-LOGIN-')],
        [sg.Text('Hasło'), sg.Input(default_text=last_credentials.password,
                                    key='-PASSWORD-', password_char="*")],
        [sg.Text('Numer klienta'), sg.Input(default_text=last_credentials.fid, key='-FID-')],
        [sg.Text('BUCODE'), sg.Input(default_text=last_credentials.bucode, key='-BUCODE-')],
        [sg.Submit('OK', key='-OK-'), sg.Cancel(key='-CANCEL-')],
    ]

    window = sg.Window('Logowanie do DPD', layout, icon="dpd.png",
                       auto_size_text=False,
                       default_element_size=(12, 1),
                       text_justification='r',
                       return_keyboard_events=True,
                       grab_anywhere=False)

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            exit()
        elif event == "-OK-":
            window.close()
            # TODO: configurable prod/preprod toggle
            credentials = Credentials(True, values["-LOGIN-"], values["-PASSWORD-"],
                                      values["-FID-"], values["-BUCODE-"])
            if credentials != last_credentials:
                credentials.to_file(os.path.abspath("secrets.json"))
                return credentials
            else:
                return last_credentials
        elif event == "-CANCEL-":
            exit()


def remove_ticks(table_data: list[list]):
    for row in table_data:
        row[0] = BLANK_BOX


def main_window(dpd_creds: Credentials):
    """
    Run main PySimpleGUI window. It handles events in while(True) loop.
    """
    transactions = get_active_transactions()
    table_data = [[BLANK_BOX, trans.name, trans.value, trans.client_symbol, trans.client_name,
                   trans.email, trans.tel, trans.address, trans.city, trans.zip_code]
                  for trans in transactions]
    table_headings = [" ✔️ ", "Nazwa", "Wartość brutto", "Symbol", "Klient",
                      "Email", "Tel", "Ulica", "Miasto", "Kod pocztowy"]
    selected = {i for i, row in enumerate(table_data[1:][:]) if row[0] == CHECKED_BOX}
    details = defaultdict(ShipmentDetails)
    layout = create_layout(table_data, table_headings)
    last_selected_row: Optional[int] = None

    window = sg.Window('Listbox with Search', layout, icon="dpd.png", resizable=True, finalize=True)

    # TODO: There is sometimes name/surname in the phone number. It should be handled gracefully.

    # TODO: Przydałoby się pewnie zmieniać status tych zamówień po wygenerowaniu etykiety
    # Tylko jeśli ustawi się status to musi on być niższy niż
    # ten, który ustawiamy, bo inaczej zrobimy cofkę.
    while True:
        event, values = window.read()
        # Exit
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        # Clicking on checkbox
        elif event[0] == "-TRANS-" and event[2][0] not in (None, -1) and event[2][1] == 0:
            window["-INFO2-"].update(value="")
            window["-PDF-"].update(data=b'')
            row: int = event[2][0]
            # update weight and secondary name of the last selected row
            # TODO: validate lengths
            if values["-WEIGHT-"] and last_selected_row is not None:
                details[last_selected_row].weight = values["-WEIGHT-"]
            if values["-RECEIVER NAME-"] and last_selected_row is not None:
                details[last_selected_row].receiver_second_name = values["-RECEIVER NAME-"]
            last_selected_row = row
            window['-COD-'].update(value=details[row].cod)
            window['-NEXTDAY-'].update(value=details[row].next_day)
            window["-WEIGHT-"].update(value=details[row].weight)
            window['-RECEIVER NAME-'].update(value=details[row].receiver_second_name)
            if table_data[row][0] == CHECKED_BOX:  # Going from Checked to Unchecked
                selected.remove(row)
                table_data[row][0] = BLANK_BOX
            else:  # Going from Unchecked to Checked
                if transactions[row].validate() and (transactions[row].value or not
                                                     details[row].cod):
                    selected.add(row)
                    table_data[row][0] = CHECKED_BOX
                else:
                    window["-INFO2-"].update(value="Ta transakcja nie ma wszystkich wymaganych "
                                             "pól do wygenerowania etykiety!")

            # Update the table and the selected rows
            window['-TRANS-'].update(values=table_data[:][:], select_rows=[last_selected_row])
            selected_desc = [
                str(i) + ": " + transactions[i].client_symbol for i in sorted(selected)]
            if selected_desc:
                window["-INFO1-"].update(
                    value=f"Wybrane transakcje:\n{chr(10).join(selected_desc)}")
            else:
                window["-INFO1-"].update(value="")

        # Clicking on row but not on checkbox
        elif event[0] == "-TRANS-" and event[2][0] not in (None, -1):
            row: int = event[2][0]

            # update weight and secondary name of the last selected row
            # TODO: validate lengths
            if values["-WEIGHT-"] and last_selected_row is not None:
                details[last_selected_row].weight = values["-WEIGHT-"]
            if values["-RECEIVER NAME-"] and last_selected_row is not None:
                details[last_selected_row].receiver_second_name = values["-RECEIVER NAME-"]

            window["-WEIGHT-"].update(value=details[row].weight)
            window['-COD-'].update(value=details[row].cod)
            window['-NEXTDAY-'].update(value=details[row].next_day)
            window['-RECEIVER NAME-'].update(value=details[row].receiver_second_name)
            last_selected_row = row
        elif event == "-COD-" and last_selected_row is not None:
            # Set COD only if transaction value is greater than 0
            if transactions[last_selected_row].value:
                details[last_selected_row].cod = values["-COD-"]
            else:
                window["-INFO2-"].update(value="Przesyłka pobraniowa musi mieć wartość!")
                window['-COD-'].update(value=details[last_selected_row].cod)
        elif event == "-NEXTDAY-" and last_selected_row is not None:
            details[last_selected_row].next_day = values["-NEXTDAY-"]
        elif event == "-PRINT LABEL-":
            window["-INFO2-"].update(value="")
            if not selected:
                window["-INFO2-"].update(value="Nie wybrano żadnej transakcji!")
                continue

            if values["-WEIGHT-"]:
                details[last_selected_row].weight = values["-WEIGHT-"]
            if values["-RECEIVER NAME-"]:
                details[last_selected_row].receiver_second_name = values["-RECEIVER NAME-"]

            window["-INFO1-"].update(value=f"Generowanie etykiet ...")
            shipments = [Shipment.from_transaction(trans, details[idx]).to_dpd_json(dpd_creds.fid)
                         for idx, trans in enumerate(transactions) if idx in selected]
            data, filepath = generate_labels(shipments, dpd_creds)
            window["-INFO1-"].update(value="Pomyślnie wygenerowano etykiety dla transakcji "
                                     f"o {'numerach' if len(selected) > 1 else 'numerze'}: {', '.join(map(str, sorted(selected)))}\n"
                                     f"Etykiety zapisano w pliku: {filepath}")
            window["-PDF-"].update(data=data)
            window['-TRANS-'].update(values=table_data[:][:], select_rows=[last_selected_row])
            sg.FolderBrowse(initial_folder=filepath)
        elif event == "-OPEN FOLDER-":
            if sys.platform == 'win32':
                subprocess.Popen(['start', os.path.abspath("labels")], shell=True)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', os.path.abspath("labels")])
            else:
                subprocess.Popen(['xdg-open', os.path.abspath("labels")])
        elif event == "-REFRESH-":
            transactions = get_active_transactions()
            table_data = [[BLANK_BOX, trans.name, trans.value, trans.client_symbol,
                           trans.client_name, trans.email, trans.tel, trans.address,
                          trans.city, trans.zip_code] for trans in transactions]
            selected = {i for i, row in enumerate(table_data[1:][:]) if row[0] == CHECKED_BOX}
            details = defaultdict(ShipmentDetails)
            window['-TRANS-'].update(values=table_data, select_rows=[])
            window['-INFO1-'].update(value="")
            window['-INFO2-'].update(value="")
            window.read()
            window.refresh()
        elif event == "-UNCHECK-":
            remove_ticks(table_data)
            window['-TRANS-'].update(values=table_data[:][:], select_rows=[last_selected_row])
            window['-INFO1-'].update(value="")
        elif event == "-REFRESH-ONE-":
            if last_selected_row is None:
                continue
            trans = transactions[last_selected_row]
            new_trans = refresh_transaction(trans)
            transactions[last_selected_row] = new_trans
            table_data[last_selected_row] = [
                table_data[last_selected_row][0], new_trans.name, new_trans.value,
                trans.client_symbol, new_trans.client_name, new_trans.email,
                new_trans.tel, new_trans.address, new_trans.city, new_trans.zip_code
            ]
            window['-TRANS-'].update(values=table_data[:][:], select_rows=[last_selected_row])

    window.close()


def main():
    dpd_creds = dpd_login()
    os.makedirs(os.path.abspath("labels"), exist_ok=True)
    main_window(dpd_creds)


if __name__ == '__main__':
    sg.theme('Dark Blue 13')
    main()
