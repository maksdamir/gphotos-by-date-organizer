import sys
import os
import filecmp
import shutil

dirname = sys.argv[1]
output_dirname = f"{dirname}_out"

print (f"dirname: {dirname}, output: {output_dirname}")

try:
    shutil.rmtree(output_dirname)
except FileNotFoundError:
    pass

files_originally = {}
for root, dirs, files in os.walk(dirname):
    for file in files:
        if file in {".DS_Store"}:
            continue
        # Convert ".../Google Photos/Photos from 2022" -> "2022"
        year_dirname_components = root.split('Photos from ')
        if len(year_dirname_components) == 1:
            continue
        year_dirname = year_dirname_components[1]
        full_year_dirname = f"{output_dirname}/{year_dirname}"

        if not os.path.exists(full_year_dirname):
            os.makedirs(full_year_dirname)

        copied_path = f"{full_year_dirname}/{file}"
        if os.path.exists(copied_path):
            exit (f"File already exists! {copied_path}. Trying to copy from: {root}")
        shutil.copy(f"{root}/{file}", copied_path)
        
        if file not in files_originally:
            files_originally[file] = 0
        files_originally[file] += 1

print ("Copied files validation...")

files_copied = {}
for root, dirs, files in os.walk(output_dirname):
    for file in files:
        if file in {".DS_Store"}:
            continue
        
        if file not in files_copied:
            files_copied[file] = 0
        
        files_copied[file] += 1

if len(files_originally) != len(files_copied):
    exit(f"Size mismatch for files: {len(files_originally)}, {len(files_copied)}")

for file, hits in files_originally.items():
    if hits != files_copied[file]:
        exit(f"Hits mismatch for file {file}")

print ("All files copied...")