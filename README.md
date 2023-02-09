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
