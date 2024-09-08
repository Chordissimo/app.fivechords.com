#!/bin/bash
  
echo "You must run this script as follows:" 
echo "   sudo bash ./create_users.sh"
echo
 
echo
echo "--> Creating users for staing and production environments..."
adduser ci_user --disabled-password --gecos ""
usermod -aG sudo ci_user
sudo echo 'ci_user ALL=(ALL) NOPASSWD: ALL' | sudo EDITOR='tee -a' visudo
echo "--> Done"
echo

echo
echo "--> Generating keys..."
ssh-keygen -q -t rsa -b 4096 -N '' -f ci_user_key  <<<y
echo "--> Done"
echo

echo
echo "--> Installing public keys..."
su $USER -c "mkdir /home/ci_user/.ssh"
su $USER -c "cat >> /home/ci_user/.ssh/authorized_keys < ci_user_key.pub"
echo "--> Done"
echo

echo /home/$SUDO_USER/.ci_user_keys
mkdir -p /home/$SUDO_USER/.ci_user_keys
mv ci_user_key.pub ci_user_key /home/$SUDO_USER/.ci_user_keys/

echo
echo "Private key for staging_user for GitHub (secret)"
echo
cat /home/$SUDO_USER/.ci_user_keys/ci_user_key
echo
