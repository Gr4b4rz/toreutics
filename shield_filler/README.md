# Shield Filler

Program to fill shield-like images with text.
It reads .txt file in which every line is a text input i.e. name and surname.
Each input line is used to fill one of shield templates in a best possible way to match cruicial requirements:
- text needs to be readable
- text cannot touch shield's border and other artefacts inside the shield


## Usage

./shield_filler.py names_example.txt templates/shield.bmp --height-offset=80
