#!/usr/bin/env python3

import sys
import os
import filecmp
import shutil

if len(sys.argv) == 1:
    exit ("Input dirname is required for processing.")

dirname = sys.argv[1]
output_dirname = f"{dirname}_out"

print (f"dirname: {dirname}")
print (f"output: {output_dirname}")

try:
    shutil.rmtree(output_dirname)
except FileNotFoundError:
    pass

files_total = 0
for root, dirs, files in os.walk(dirname):
    files = [f for f in files if f not in {".DS_Store"}]
    files_total += len(files)
print (f"{files_total} files to copy")

files_copied = 0
files_hits_input = {}
for root, dirs, files in os.walk(dirname):
    # Convert ".../Google Photos/Photos from 2022" -> "2022"
    year_dirname_components = root.split('Photos from ')
    if len(year_dirname_components) == 1:
        continue
    year_dirname = year_dirname_components[1]
    full_year_dirname = f"{output_dirname}/{year_dirname}"
    if not os.path.exists(full_year_dirname):
        os.makedirs(full_year_dirname)

    for file in files:
        if file in {".DS_Store"}:
            continue

        copied_path = f"{full_year_dirname}/{file}"
        if os.path.exists(copied_path):
            exit (f"File already exists! {copied_path}. Trying to copy from: {root}")
        shutil.copy(f"{root}/{file}", copied_path)
        
        if file not in files_hits_input:
            files_hits_input[file] = 0
        files_hits_input[file] += 1
        files_copied += 1
        if files_copied % 1000 == 0:
            print (f"Processed {files_copied}/{files_total} files")

print (f"Processed {files_copied}/{files_total} files")
print ("Copied files validation...")

files_hits_output = {}
for root, dirs, files in os.walk(output_dirname):
    for file in files:
        if file in {".DS_Store"}:
            continue
        
        if file not in files_hits_output:
            files_hits_output[file] = 0
        files_hits_output[file] += 1

if len(files_hits_input) != len(files_hits_output):
    exit(f"Size mismatch for files: {len(files_hits_input)}, {len(files_hits_output)}")

for file, hits in files_hits_input.items():
    if hits != files_hits_output[file]:
        exit(f"Hits mismatch for file {file}")