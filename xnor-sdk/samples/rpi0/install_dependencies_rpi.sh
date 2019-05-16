#!/bin/bash
set -e

sudo apt-get update
sudo apt-get install -y libpython3-dev python3-pip libjpeg-dev
python3 -m pip install --user -r requirements.txt

echo -n "Enabling picamera... "
if grep -q "start_x" /boot/config.txt
then
# While this may seem dangerous, it is almost exactly what raspi-config does to
# enable the picamera. See for yourself at /usr/bin/raspi-config
sudo sed -i "s/start_x=0/start_x=1/g" /boot/config.txt
else
# If the camera has not been used before, these variables may not have been set.
sudo echo "start_x=1" >> /boot/config.txt
sudo echo "gpu_mem=128" >> /boot/config.txt
fi
echo "Done"
read -p "The system will now need to reboot in order to use the picamera.
Reboot now? [Y/N]
" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
sudo reboot
fi
