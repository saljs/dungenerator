import argparse
import pickle
from pathlib import Path

parser = argparse.ArgumentParser(description="List level notes for v1 savefiles")
parser.add_argument(
    "savefile",
    help = "Savefile to list notes from",
    type = Path,
)
args = parser.parse_args()

with args.savefile.open("rb") as sf:
    savefile = pickle.load(sf)

for _, note in savefile.level_notes.items():
    print(note)
