# DPD label printer for the Insert CRM (SubiektGT & GestorGT)

## Credentials
DPD credentials should be provided in the first login window. They are then
decrypted with symetric key which is defined on the top of src/dpd.py file.
This key should be changed before using this program to make this solution secure.
There also credentials to Insert MSSQL database. For now they are hardcoded in
get_active_transactions() function from src/mssql.py file. But its a high priority TODO.

## Usage

### As a Python script
```
pipenv shell
pipenv install
python3 label_printer.py
```

### As a windows .exe
It needs to be compiled. For example with: pyinstaller.
Pyinstaller doesn't support cross-compilation, so .exe file has to be created on Windows.
Python and pipenv needs to be setup. Also, on windows, pyinstaller might need pillow, pywin32-ctypes and pefile.
They can be installed with pip.
Running pyinstaller:
```
pipenv run pyinstaller --windowed --icon=dpd.png --onefile label_printer.py
```
If it finished sucessfully, exe file can be found in dist directory.
