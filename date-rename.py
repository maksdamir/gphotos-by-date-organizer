#!/usr/bin/env python3

import os
import subprocess
import datetime
import json
from typing import Optional, Any
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("google_takeouts_dir", type=str, help="Google Photos takeouts dir")
parser.add_argument("--rename", action="store_true", help="Actually perform rename")
parser.add_argument(
    "--progress-report", action="store_true", help="Report each 1000 processed files"
)
args = parser.parse_args()

dirname = args.google_takeouts_dir
should_rename = args.rename
should_progress_report = args.progress_report

print("google takeouts dir:", dirname)
if should_rename:
    print("should rename:", should_rename)
else:
    print("should rename:", should_rename, "(dry run)")
print("progress report:", should_progress_report)
print()

# file path -> creation timestamp (utc)
media_file_full_paths: dict[str, Any] = {}
json_file_full_paths: dict[str, Any] = {}

for root, dirs, files in os.walk(dirname):
    for file in files:
        if file == ".DS_Store":
            continue

        full_path = f"{root}/{file}"
        if file[-5:] == ".json":
            json_file_full_paths[full_path] = None
        else:
            media_file_full_paths[full_path] = None

date_create_tags = [
    "DateTimeOriginal",
    "SubSecDateTimeOriginal",
    "DateTimeCreated",
    "CreationDate",
    "CreateDate",
    "SubSecCreateDate",
    "DateCreated",
    "MediaCreateDate",
]
date_update_tags = [
    "SubSecModifyDate",
    "ModifyDate",
    "MediaModifyDate",
    "MetadataDate",
]
date_gps_tags = [
    "GPSDateTime",
]

files_processed = 0
files_total = len(media_file_full_paths)


def get_json_file_path(media_file: str) -> Optional[str]:
    # Most usual case
    # media: IMG_100.JPG
    # meta : IMG_100.JPG.json
    json_file = media_file + ".json"
    if json_file in json_file_full_paths:
        return json_file

    # Long names (name gets cut at 46 chars)
    # media: PXL_20340101_011252088._exported_755_1628556579337.jpg
    # meta : PXL_20340101_011252088._exported_755_162855657.json
    base_file_name = os.path.basename(media_file)[:46]
    dir_name = os.path.dirname(media_file)
    json_file = f"{dir_name}/{base_file_name}.json"
    if json_file in json_file_full_paths:
        return json_file

    # Indexed naming weirdness
    # media: IMG_3214(1).JPG
    # meta : IMG_3214.JPG(1).json
    moved_id_file_name = re.sub(r"(\(\d*\)).(\w*)$", r".\2\1", base_file_name)
    json_file = f"{dir_name}/{moved_id_file_name}.json"
    if json_file in json_file_full_paths:
        return json_file

    # Edited files usually come with non-edited version, and both share same metadata
    # media: IMG_100-edited.jpg
    # media: IMG_100.jpg
    # meta : IMG_100.jpg.json
    edited_removed_file_name = re.sub(r"(-edited).(\w*)$", r".\2", base_file_name)
    json_file = f"{dir_name}/{edited_removed_file_name}.json"
    if json_file in json_file_full_paths:
        return json_file

    # Pixel motion photos
    # media: PXL_20220617_184545136.MP
    # media: PXL_20220617_184545136.MP.jpg
    # meta : PXL_20220617_184545136.MP.jpg.json
    file_name, file_ext = os.path.splitext(base_file_name)
    if file_ext == ".MP":
        json_file = f"{dir_name}/{base_file_name}.jpg.json"
        if json_file in json_file_full_paths:
            return json_file

    # iOS HEIC + MP4 pair
    # media: IMG_1637.MP4
    # media: IMG_1637.HEIC
    # meta : IMG_1637.HEIC.json
    # Same, but combined with indexed naming:
    # media: IMG_0002(1).MP4
    # media: IMG_0002(1).HEIC
    # meta : IMG_0002.HEIC(1).json
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
            photo_taken_timestamp = json_data["photoTakenTime"]["timestamp"]
            return float(photo_taken_timestamp)
    except Exception as e:
        print(f"  Failed to extract photoTakenTime from metadata json={json_file}")
        raise e


# Set of media files missing json metadata file,
# (or we failed to find one due to edge case Google Photos json naming)
json_missing_files = set()
# Set of media files missing createdate / gpsdate / updatedate tags in exif info
exif_create_date_tag_missing_files = set()

for media_file in media_file_full_paths:
    try:
        if should_progress_report and files_processed % 1000 == 0:
            print(f"  Processed {files_processed}/{files_total} media files")
        files_processed += 1

        # Try metadata stored in corresponding json metadata file first
        json_file = get_json_file_path(media_file=media_file)
        if json_file is not None:
            creation_timestamp = read_create_timestamp_from_json(json_file=json_file)
            json_file_full_paths[json_file] = creation_timestamp
            media_file_full_paths[media_file] = creation_timestamp
            continue

        print(f"  json file not found for media file={media_file}, trying exiftool")
        json_missing_files.add(media_file)

        # Fallback to exiftool
        exiftool_result = subprocess.run(
            ["exiftool", "-json", media_file], capture_output=True, text=True
        )
        if exiftool_result.returncode == 0:
            exiftool_json = json.loads(exiftool_result.stdout)[0]

            creation_date: Optional[str] = None
            creation_tag_used: Optional[str] = None
            # Any create date tag set?
            for date_tag in date_create_tags:
                if date_tag in exiftool_json:
                    creation_date = exiftool_json[date_tag]
                    creation_tag_used = date_tag
                    break
            # Any gps date set?
            if creation_date is None:
                for date_tag in date_gps_tags:
                    if date_tag in exiftool_json:
                        creation_date = exiftool_json[date_tag]
                        creation_tag_used = date_tag
                        break
            # Final try - if update date is set, use that
            if creation_date is None:
                for date_tag in date_update_tags:
                    if date_tag in exiftool_json:
                        creation_date = exiftool_json[date_tag]
                        creation_tag_used = date_tag
                        break
            if creation_date is None:
                print(f"  No create date tag found for media file={media_file}")

            if creation_date is None:
                exif_create_date_tag_missing_files.add(media_file)
                continue

            creation_timestamp = datetime.datetime.strptime(
                creation_date[:19], "%Y:%m:%d %H:%M:%S"
            ).timestamp()
        else:
            print(
                f"  exiftool run failed for media file={media_file}, err={exiftool_result}"
            )
    except Exception as e:
        print(f"  Failed to process media file={media_file}")
        raise e

print()
print(f"Processed {files_processed}/{files_total} media files")
print()

if len(exif_create_date_tag_missing_files) > 0:
    print("=== Following media files lack both a corresponding JSON metadata file")
    print("=== and date information in the EXIF data.")
    print("=== As a result, they will not be renamed and require manual processing.")
    for media_file in exif_create_date_tag_missing_files:
        print(f"    {media_file}")

print()

# Now actually rename media files
if should_rename:
    print("Renaming files")
    for media_file, creation_timestamp in {
        **media_file_full_paths,
        **json_file_full_paths,
    }.items():
        if creation_timestamp is None:
            continue

        base_file_name = os.path.basename(media_file)
        file_name, file_ext = os.path.splitext(base_file_name)
        dir_name = os.path.dirname(media_file)

        date_str = datetime.datetime.utcfromtimestamp(creation_timestamp).strftime(
            "%Y_%m_%d__%H_%M_%S__"
        )
        if file_ext == ".json":
            new_media_file = f"{dir_name}/meta/{date_str}{base_file_name}"
            try:
                os.rename(media_file, new_media_file)
            except FileNotFoundError:
                os.makedirs(os.path.dirname(new_media_file))
                os.rename(media_file, new_media_file)
        else:
            new_media_file = f"{dir_name}/{date_str}{base_file_name}"
            os.rename(media_file, new_media_file)

else:
    print("Renaming files skipped (dry run)")
