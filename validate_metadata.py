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

files_copied_full_paths = set()
for root, dirs, files in os.walk(output_dirname):
    for file in files:        
        files_copied_full_paths.add(f"{root}/{file}")

skipped_metadata_files = []
print ("Validate each json file has corresponding media file...")
for file in files_copied_full_paths:
    if file[-5:] != ".json":
        continue
    media_file = file[:-5]
    if media_file not in files_copied_full_paths:
        # Metadata file has different index-suffix placement:
        # media: IMG_01(1).JPG
        # json : IMG_01.JPG(1).json
        if media_file[-1] == ")":
            media_file_components = media_file.split(".")

            ext_components = media_file_components[-1].split('(')
            index = "(" + ext_components[-1]
            ext = ext_components[0]

            media_file_restored = ".".join(media_file_components[:-1]) + index + "." + ext

            if media_file_restored not in files_copied_full_paths:
                print(f"Media file (restored)={media_file_restored} not found for json metadata {file}")
                skipped_metadata_files.append(file)
        else:
            print(f"Media file not found for json metadata {file}")
            skipped_metadata_files.append(file)

# TODO: Handle -edited files
# TODO: Handle all (n) files
