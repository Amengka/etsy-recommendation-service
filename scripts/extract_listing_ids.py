import re
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

with open(DATA_DIR / "listingNames.txt", "r") as file:
    listingNames = file.read().split("\n")

for name in listingNames: 
    filePath = DATA_DIR / "raw" / name
    with open(filePath, "r") as file: 
        data = file.read()
        listings = re.findall(r'\((\d+)\)', data)
        listings = [int(item) for item in listings][1:]
    destPath = DATA_DIR / "listings" / name
    with open(destPath, "w") as file: 
        for i in range(len(listings)): 
            file.write(str(listings[i]))
            if i < len(listings) - 1 : file.write("\n")