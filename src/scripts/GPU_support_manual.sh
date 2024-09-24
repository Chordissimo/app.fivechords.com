# Prrequisites: Ubuntu 22.04
# https://hostkey.com/documentation/technical/gpu/nvidia_gpu_linux/#installing-nvidia-modules-for-docker

sudo apt update && sudo apt full-upgrade -y
#sudo apt install ubuntu-drivers-common
#ubuntu-drivers devices

sudo apt install nvidia-driver-560
sudo apt install gcc

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install cuda -y

echo 'export PATH="/sbin:/bin:/usr/sbin:/usr/bin:${PATH}:/usr/local/cuda/bin"' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}' >> ~/.bashrc
source ~/.bashrc

sudo apt install -y nvidia-docker2

echo "REBOOT THE SYSTEM"
