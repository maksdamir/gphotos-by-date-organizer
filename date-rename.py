#!/usr/bin/env python3

import sys
import os
import subprocess
import datetime
import json
from typing import Optional
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--google-takeout-dirs', required=True, type=str, help="Google Photos takeouts dir")
parser.add_argument('--rename', action="store_true", help="Actually perform rename")
args = parser.parse_args()

dirname = args.google_takeout_dirs
should_rename = args.rename

print (f"google takeouts dir: {dirname}; should rename: {should_rename}")

media_file_full_paths = {} # Media file path -> creation timestamp (utc)
json_file_full_paths = set()

for root, dirs, files in os.walk(dirname):
    for file in files:        
        if file == ".DS_Store":
            continue

        full_path = f"{root}/{file}"
        if file[-5:] == ".json":
            json_file_full_paths.add(full_path)
        else:
            media_file_full_paths[full_path] = None

date_create_tags = [
    'DateTimeOriginal',
    "SubSecDateTimeOriginal",
    "DateTimeCreated",
    "CreationDate", 
    'CreateDate', 
    "SubSecCreateDate",
    'DateCreated',
    "MediaCreateDate",
]
date_update_tags = [
    "SubSecModifyDate",
    'ModifyDate',
    "MediaModifyDate",
    'MetadataDate',
]
date_gps_tags = [
    'GPSDateTime',
]

files_processed = 0
files_total = len(media_file_full_paths)


def get_json_file_path(media_file: str) -> Optional[str]:
    # IMG_100.JPG
    # IMG_100.JPG.json
    json_file = media_file + ".json"
    if json_file in json_file_full_paths:
        return json_file
    
    # long names:
    # PXL_20340101_011252088._exported_755_1628556579337.jpg
    # PXL_20340101_011252088._exported_755_162855657.json
    base_file_name = os.path.basename(media_file)[:46]
    dir_name = os.path.dirname(media_file)
    json_file = f"{dir_name}/{base_file_name}.json"
    if json_file in json_file_full_paths:
        return json_file

    # IMG_3214(1).JPG
    # IMG_3214.JPG(1).json
    moved_id_file_name = re.sub(r"(\(\d*\)).(\w*)$", r".\2\1", base_file_name)
    json_file = f"{dir_name}/{moved_id_file_name}.json"
    if json_file in json_file_full_paths:
        return json_file

    # IMG_100-edited.jpg
    # IMG_100.jpg.json
    edited_removed_file_name = re.sub(r"(-edited).(\w*)$", r".\2", base_file_name)
    json_file = f"{dir_name}/{edited_removed_file_name}.json"
    if json_file in json_file_full_paths:
        return json_file

    # Pixel motion photos
    # PXL_20220617_184545136.MP
    # PXL_20220617_184545136.MP.jpg
    # PXL_20220617_184545136.MP.jpg.json
    file_name, file_ext = os.path.splitext(base_file_name)
    if file_ext == ".MP":
        json_file = f"{dir_name}/{base_file_name}.jpg.json"
        if json_file in json_file_full_paths:
            return json_file    
            
    # iOS HEIC + MP4 pair
    # IMG_1637.MP4
    # IMG_1637.HEIC
    # IMG_1637.HEIC.json
    # Also:
    # IMG_0002(1).MP4
    # IMG_0002(1).HEIC
    # IMG_0002.HEIC(1).json
    if file_ext == ".MP4":
        heic_file = f"{dir_name}/{file_name}.HEIC"
        if heic_file in media_file_full_paths:
            json_file = f"{heic_file}.json"
            if json_file in json_file_full_paths:
                return json_file
            moved_id_file_name = re.sub(r"(\(\d*\)).(\w*)$", r".\2\1", heic_file)
            json_file = f"{moved_id_file_name}.json"
            if json_file in json_file_full_paths:
                return json_file

    return None
    
def read_create_timestamp_from_json(json_file: str) -> float:
    try:
        with open(json_file, "r") as json_f:
            json_data = json.load(json_f)
            photo_taken_timestamp = json_data['photoTakenTime']['timestamp']
            return float(photo_taken_timestamp)
    except Exception as e:
        print (f"Failed to fetch photoTakenTime from json={json_file}")
        raise e

exif_create_date_tag_missing_files = set()
json_missing_files = set()

for media_file in media_file_full_paths:
    try:
        if files_processed % 1000 == 0:
            print (f"Processed {files_processed}/{files_total} media files")

        files_processed += 1

        # Try metadata stored in corresponding json file first
        json_file = get_json_file_path(media_file=media_file)
        if json_file is not None:
            creation_timestamp = read_create_timestamp_from_json(json_file=json_file)
            media_file_full_paths[media_file] = creation_timestamp
            continue

        print (f"json file not found for media file={media_file}, trying exiftool")
        json_missing_files.add(media_file)
        
        # Fallback to exiftool
        exiftool_result = subprocess.run(["exiftool", "-json", media_file], capture_output=True, text=True)
        if exiftool_result.returncode == 0:
            exiftool_json = json.loads(exiftool_result.stdout)[0]

            creation_date = None
            gps_date = None
            update_date = None
            for date_tag in date_create_tags:
                if date_tag in exiftool_json:
                    creation_date = exiftool_json[date_tag]
                    creation_tag_used = date_tag
                    break
            for date_tag in date_gps_tags:
                if date_tag in exiftool_json:
                    gps_date = exiftool_json[date_tag]
                    gps_tag_used = date_tag
                    break
            for date_tag in date_update_tags:
                if date_tag in exiftool_json:
                    update_date = exiftool_json[date_tag]
                    update_tag_used = date_tag
                    break
            if creation_date is None:
                exif_create_date_tag_missing_files.add(media_file)
                print (f"No create date tag found for media file={media_file}, update_date={update_date}, gps_date={gps_date}")
                if update_date is None and gps_date is None:
                    continue

            date_to_use = creation_date
            if date_to_use is None:
                date_to_use = gps_date
            if date_to_use is None:
                date_to_use = update_date
            
            creation_timestamp = datetime.datetime.strptime(date_to_use[:19], "%Y:%m:%d %H:%M:%S").timestamp()
        else:
            print (f"exiftool run failed for media file={media_file}, err={exiftool_result}")
    except Exception as e:
        print (media_file)
        raise e

print (f"Processed {files_processed}/{files_total} media files")

# Now actually rename media files
if should_rename:
    for media_file, creation_timestamp in media_file_full_paths.items():
        if creation_timestamp is None:
            continue

        base_file_name = os.path.basename(media_file)
        dir_name = os.path.dirname(media_file)

        date_str = datetime.datetime.utcfromtimestamp(creation_timestamp).strftime("%Y_%m_%d__%H_%M_%S__")
        new_media_file = f"{dir_name}/{date_str}{base_file_name}"

        os.rename(media_file, new_media_file)



