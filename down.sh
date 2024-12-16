#!/bin/bash
#wget --remote-encoding=cp1250 -r -N --cut-dirs=2 -nH --accept="zip,ZIP" --reject-regex='2021-12/*|2022-01/*' ftp://ftp.cisjr.cz/draha/celostatni/szdc/2022
#TARGET_DIR=`pwd`/szdc/2022
#./bb download_dirlisting.clj -b https://portal.cisjr.cz -p /pub/draha/celostatni/szdc/2022 -d $TARGET_DIR -t 50
#TARGET_DIR=`pwd`/szdc/2023
#./bb download_dirlisting.clj -b https://portal.cisjr.cz -p /pub/draha/celostatni/szdc/2023 -d $TARGET_DIR -t 50

TARGET_DIR=`pwd`/szdc/2024
./bb download_dirlisting.clj -b https://portal.cisjr.cz -p /pub/draha/celostatni/szdc/2024 -d $TARGET_DIR -t 50
TARGET_DIR=`pwd`/szdc/2025
./bb download_dirlisting.clj -b https://portal.cisjr.cz -p /pub/draha/celostatni/szdc/2025 -d $TARGET_DIR -t 50

