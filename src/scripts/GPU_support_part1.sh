sudo apt-get -y remove --purge '^cuda-.*' && \
sudo apt-get -y remove --purge '^libnvidia-.*' && \
sudo apt-get -y remove --purge '^nvidia-.*' && \
sudo apt-get -y autoremove

sudo ubuntu-drivers autoinstall

sudo reboot
