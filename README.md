# gphotos-date-organize

## Problem

When you download your media files from Google Photos Takeout, they come in per-year folders with all files mixed together, making it difficult to understand when each photo/movie was taken:

```
Takeout/
  Google Photos/
    Photos from 2021/
      ...
    Photos from 2022/
      DSC01234.JPG # When was this taken?
      IMG_6342.JPG # Or this? Which one comes first?
      ...
```

## A solution

Luckily, most of these files are provided with a corresponding metadata JSON file that includes information on the date and location (GPS coordinates) of when and where the image was taken.

These scripts extract the creation date from either the metadata file or the media file's EXIF data, and then rename each media file to the format `YYYY_MM_DD__HH_mm_ss__<old_name>`, making it easier to organize and browse the library.

```
Takeout/
  2021/
    ...
  2022/
    2022_07_04__15_12_00__IMG_6342.JPG
    2022_12_01__13_15_02__DSC01234.JPG
    ...
```

## Scripts

### combine-year-folders.py

This is a helper script used to combine multiple per-year sub-folders, from multiple Google Photos Takeout archives into a single per-year folder.

In case you have multiple Google Photos Takeout archives, the media and metadata files might be split across different folders, like this:

```
Takeouts/
  Takeout/
    Google Photos/
      ...
      Photos from 2022/
        DSC01234.JPG
        IMG_6342.JPG.json # Metadata for IMG_6342.JPG
        ...

  Takeout 2/
    Google Photos/
      ...
      Photos from 2022/
        DSC01234.JPG.json # Metadata for DSC01234.JPG
        IMG_6342.JPG
        ...
```

This makes it harder for the main script (`date-rename.py`) to find metadata files.

So, to combine the folders together, run:

```
$ ./combine-year-folders.py /path/to/Takeouts
```

which ends up collecting the folders together:

```
Takeouts_out/
  2022/
    DSC01234.JPG
    DSC01234.JPG.json 
    IMG_6342.JPG
    IMG_6342.JPG.json
```

### date-rename.py
Once you have your media files and corresponding metadata json files in place (either through the aforementioned script or any other method), it's time to proceed with renaming the files.

To preview the changes without actually renaming any file, use the following command:

```
# dry run
$ ./date-rename.py /path/to/Takeout
google takeouts dir: /path/to/Takeout
should rename: False
progress report: False

  json file not found for media file=/path/to/Takeout/2019/unknown.jpg, trying exiftool
  No create date tag found for media file=/path/to/Takeout/2019/unknown.jpg

Processed 17514/17514 media files

=== Following media files lack both a corresponding JSON metadata file
=== and date information in the EXIF data.
=== As a result, they will not be renamed and require manual processing.
    /path/to/Takeout/2019/unknown.jpg

Renaming files skipped (dry run)
```

This will process each media file in the directory and retrieve the creation date from the corresponding metadata file or, if missing, the EXIF data.
Any files where the creation date cannot be determined (due to missing both metadata and EXIF data) will be reported (you will have to manually process those, unfortunately). 

If everything looks good and you're fine with skipped files, run the following command:

```
$ ./date-rename.py /path/to/Takeout --rename
```

Resulting in:

```
Takeout/
  2022/
    2022_07_04__15_12_00__IMG_6342.JPG
    2022_12_01__13_15_02__DSC01234.JPG
    meta/
      2022_07_04__15_12_00__IMG_6342.JPG.json
      2022_12_01__13_15_02__DSC01234.JPG.json
```
