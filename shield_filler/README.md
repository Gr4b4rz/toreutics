# Shield Filler

Program to fill shield-like images with text.
It reads .txt file in which every line is a text input i.e. name and surname.
Each input line is used to fill one of shield templates in a best possible way to match cruicial requirements:
- text needs to be readable
- text cannot touch shield's border and other artefacts inside the shield
- there have to be clear spacing between the lines

## GUI

### As a Python script
```
pipenv shell
pipenv install
python3 shield_filler.py
```

### As a windows .exe
It needs to be compiled. For example with: pyinstaller.
Pyinstaller doesn't support cross-compilation, so .exe file has to be created on Windows.
Python and pipenv needs to be setup. Also, on windows, pyinstaller might need pillow, pywin32-ctypes and pefile.
They can be installed with pip.
Running pyinstaller:
```
pipenv run pyinstaller --windowed --icon=nail_icon.jpg --onefile shield_filler.py
```
If it finished sucessfully, exe file can be found in dist directory.


## Old approach

```console
./shield_filler.py names_example.txt templates/shield.bmp --height-offset=80
```
or
```console
./shield_filler.py names_for_nail.txt templates/nail_01.bmp --font-size=52 --font-name=fonts/seagull.ttf --output-file shields
```
