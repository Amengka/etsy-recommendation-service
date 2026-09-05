import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Folder holding one file per Etsy search query
folder_path = DATA_DIR / "raw"

# Get list of all filenames in the folder
file_list = sorted(os.listdir(folder_path))

with open(DATA_DIR / "listingNames.txt", "w") as file:
    for i in range(len(file_list)): 
        file.write(file_list[i])
        if i < len(file_list) - 1: file.write("\n")