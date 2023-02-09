# gphotos-date-restore

## Problem

When you download your media files from Google Photos Takeout, they come in per-year folders with all files mixed together, making it difficult to understand when each photo/movie was taken:

```
Takeout/
  Google Photos/
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
  Google Photos/
    ...
    Photos from 2022/
      2022_07_04__15_12_00__IMG_6342.JPG
      2022_12_01__13_15_02__DSC01234.JPG
      ...
```

## Scripts

### combine-year-folders.py

This is a helper script used to combine multiple per-year sub-folders, from multiple Google Photos Takeout archives into a single per-year folder.

In case you have multiple Google Photos Takeout archives, the files might be split across different folders, like this:

```
Takeout_combine/
  Takeout/
    Google Photos/
      ...
      Photos from 2022/
        DSC01234.JPG
        IMG_6342.JPG.json # Metadata
        ...

  Takeout 2/
    Google Photos/
      ...
      Photos from 2022/
        DSC01234.JPG.json # Metadata
        IMG_6342.JPG
        ...
```

This makes it harder for the main script (`date-rename.py`) to find metadata files.

So, to combine the folders together, run:

```
./combine-year-folders.py /path/to/Takeout_combine
```

which ends up collecting the folders together:

```
Takeout_combine_out/
  2022/
    DSC01234.JPG
    DSC01234.JPG.json 
    IMG_6342.JPG
    IMG_6342.JPG.json
    ...
```

### date-rename.py
Once you have your media files and corresponding metadata json files in place (either through the aforementioned script or any other method), it's time to proceed with renaming the files.

To preview the changes without actually changing anything, use the following command:

```
# dry run
./date-rename.py --google-takeouts-dir /path/to/Takeout
```

This will process each media file in the directory and retrieve the creation date from the corresponding metadata file or, if missing, the EXIF data.
Any files where the creation date cannot be determined (due to missing both metadata and EXIF data) will be reported (you will have to manually process those, unfortunately). 

If everything looks good and you're fine with skipped files, run the following command:

```
./date-rename.py --google-takeouts-dir /path/to/Takeout --rename
```
