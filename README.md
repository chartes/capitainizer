Capitainizer
===
## General info
Conversion d’un corpus selon les [guidelines Capitains](https://github.com/Capitains/guidelines).

## Setup
Create a virtual environment, source it

```
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirement.txt

```

## Usage 
```
capitainier.py --help 

Usage: capitainizer.py [OPTIONS] INPUT OUTPUT TEMPLATE

  INPUT: Enter the name of the folder who contains the XML files or the
  differents folders who contains the XML files

  OUTPUT: Enter the destination path

  TEMPLATE: Enter the template for the collections entry

Options:
  --metadata TEXT  Enter the metadata files of the XML files
  --help           Show this message and exit.

```
