# Prrequisites: Ubuntu 22.04
# https://hostkey.com/documentation/technical/gpu/nvidia_gpu_linux/#installing-nvidia-modules-for-docker

sudo ubuntu-drivers install --gpgpu nvidia:535-server
sudo apt-get install -y nvidia-driver-535
sudo apt-get install nvidia-utils-535-server
