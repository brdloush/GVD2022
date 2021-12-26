#!/bin/sh

cd src

python3 gvd.py
python3 res.py
python3 gtfs.py

#cd ../gtfs
#feedvalidator.py vlakyCR.zip
