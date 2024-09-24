sudo apt-get remove --purge '^cuda-.*' && \
sudo apt-get remove --purge '^libnvidia-.*' && \
sudo apt-get remove --purge '^nvidia-.*' && \
sudo apt-get autoremove

sudo ubuntu-drivers autoinstall

sudo reboot
