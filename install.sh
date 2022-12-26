echo >> Updating server
sudo apt-get update
echo >> Installing pip
sudo apt install pip -y
echo >> Installing required packages
pip install -r live_tools/requirements.txt
touch cronlog.log
echo >> Done
