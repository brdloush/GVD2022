#!/bin/bash
wget https://github.com/babashka/babashka/releases/download/v1.0.166/babashka-1.0.166-linux-amd64-static.tar.gz
tar xvvzf babashka-1.0.166-linux-amd64-static.tar.gz
chmod +x ./bb
rm babashka-1.0.166-linux-amd64-static.tar.gz
wget https://raw.githubusercontent.com/brdloush/download-dirlisting/master/download_dirlisting.clj
