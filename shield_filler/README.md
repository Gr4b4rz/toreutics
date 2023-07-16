# Shield Filler

Program to fill shield-like images with text.
It reads .txt file in which every line is a text input i.e. name and surname.
Each input line is used to fill one of shield templates in a best possible way to match cruicial requirements:
- text needs to be readable
- text cannot touch shield's border and other artefacts inside the shield
- there have to be clear spacing between the lines


## Usage

```console
./shield_filler.py names_example.txt templates/shield.bmp --height-offset=80
```
or
```console
./shield_filler.py names_for_nail.txt templates/nail_01.bmp --font-size=52 --font-name=fonts/seagull.ttf --output-file shields
```
