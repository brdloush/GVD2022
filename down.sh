#!/bin/bash
#wget --remote-encoding=cp1250 -r -N --cut-dirs=2 -nH --accept="zip,ZIP" --reject-regex='2021-12/*|2022-01/*' ftp://ftp.cisjr.cz/draha/celostatni/szdc/2022
TARGET_DIR=`pwd`/szdc/2022
bb dl_http_folders.clj https://portal.cisjr.cz /pub/draha/celostatni/szdc/2022 $TARGET_DIR
