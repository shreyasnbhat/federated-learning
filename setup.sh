echo "Setting up dependencies"
cd flask/client
pip3 install --user -r requirements.txt
cd ../organization
pip3 install --user -r requirements.txt
cd ../..
npm install -g truffle
npm install -g ganache-cli
echo "Suggest to install Ganache Client App" 
