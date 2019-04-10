#!/bin/bash
# Install apt packages for both Python and C
sudo apt-get update
sudo apt-get install -y build-essential libgstreamer1.0-0 \
                        libgtk-3-0 libgtk-3-dev libgstreamer1.0-dev \
                        gstreamer1.0-plugins-base \
                        gstreamer1.0-plugins-good \
                        libgstreamer-plugins-base1.0-dev \
                        libgstreamer-plugins-good1.0-dev \
                        libgirepository1.0-dev python3-pip
# Install Python dependencies
pushd $(dirname "$0")/python
python3 -m pip install --user -r requirements.txt
python3 setup.py install --user
popd
