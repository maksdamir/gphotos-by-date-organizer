#!/usr/bin/env python3

import sys
import os

if len(sys.argv) == 1:
    exit("usage: combine-year-foldres.py <google-photos-takeouts-dir>")

dirname = sys.argv[1]
output_dirname = f"{dirname}_out"

print("input directory", dirname)
print("output directory", output_dirname)

files_total = 0
for root, dirs, files in os.walk(dirname):
    files = [f for f in files if f not in {".DS_Store", "archive_browser.html"}]
    files_total += len(files)
print(f"{files_total} files to move")

files_copied = 0
for root, dirs, files in os.walk(dirname):
    # Convert ".../Google Photos/Photos from 2022" -> "2022"
    year_dirname_components = root.split("Photos from ")
    if len(year_dirname_components) == 1:
        continue
    year_dirname = year_dirname_components[1]
    full_year_dirname = f"{output_dirname}/{year_dirname}"
    if not os.path.exists(full_year_dirname):
        os.makedirs(full_year_dirname)

    for file in files:
        if file in {".DS_Store"}:
            continue

        new_path = f"{full_year_dirname}/{file}"
        if os.path.exists(new_path):
            exit(f"File already exists! {new_path}. Trying to move from: {root}")
        os.rename(f"{root}/{file}", new_path)

        files_copied += 1
        if files_copied % 1000 == 0:
            print(f"Processed {files_copied}/{files_total} files")

print(f"Processed {files_copied}/{files_total} files")
