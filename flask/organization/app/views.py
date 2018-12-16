from flask import render_template, request, flash, redirect, url_for
from app import *
import os
from app.file_model import FileData
import requests
import ipfsapi

CONTRACT_ADDRESS = None
CONTRACT_ABI = None
MODEL_DIRECTORY = 'models'
valid_contract_addresses = []


def deploy_contract():
    global CONTRACT_ABI, CONTRACT_ADDRESS

    os.chdir('../../')
    print(os.path.abspath(os.curdir))
    os.system('./compile.sh > /dev/null')

    with open('build/contracts/LearningContract.json') as f:
        contract_data = json.load(f)

    with open('dump.txt') as f:
        content = f.readlines()
    content = [x.strip() for x in content]

    CONTRACT_ADDRESS = server.toChecksumAddress(content[12].split(': ')[1].strip())

    valid_contract_addresses.append(CONTRACT_ADDRESS)

    CONTRACT_ABI = contract_data['abi']

    session['abi'] = CONTRACT_ABI
    session['contract_address'] = CONTRACT_ADDRESS

    os.chdir('flask/organization')


def fetch_file_data():
    contract = server.eth.contract(address=CONTRACT_ADDRESS,
                                   abi=CONTRACT_ABI)

    # Get all registered users
    users = contract.call().getRegisteredUsers()

    fileData = []

    for i in users:
        ipfsHash = contract.call().getIpfsHashForUser(i)
        fileName = contract.call().getFileNameForUser(i)
        print(fileName)
        model_number = contract.call().getModelNumberForUser(i)
        fileData.append(FileData(fileName, ipfsHash, model_number, i))

    return fileData


def fetch_models_from_ipfs(fileData):
    if not os.path.exists('models'):
        os.mkdir('models')

    for file in fileData:
        req = requests.get("http://localhost:8080/ipfs/" + file.ipfsHash)

        if req.status_code != 200:
            print("Failed to retrieve", file.fileName)

        else:
            with open("models/" + file.accountNumber, "wb") as f:
                f.write(req.content)


def bytes32_to_string(x):
    output = x.hex().rstrip("0")
    if len(output) % 2 != 0:
        output = output + '0'
    output = bytes.fromhex(output).decode('utf8')
    return output


@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == 'GET':
        print(valid_contract_addresses)
        if len(valid_contract_addresses) == 0:
            return render_template('homepage.html')
        else:
            return render_template("homepage.html", deployed=True, address=CONTRACT_ADDRESS)
    else:
        deploy_contract()
        return render_template("homepage.html", deployed=True, address=CONTRACT_ADDRESS)


@app.route('/choose', defaults={'account_no': None}, methods=['GET', 'POST'])
@app.route('/account/set/<string:account_no>', methods=['POST'])
def choose_account(account_no):
    if request.method == 'GET':
        accounts = [server.toChecksumAddress(i) for i in server.eth.accounts]
        return render_template('account.html', accounts=accounts)
    elif request.method == 'POST':
        session['account'] = account_no
        return redirect(url_for('homepage'))


@app.route('/display_files', methods=['GET'])
def display():
    if request.method == 'GET':
        fileData = fetch_file_data()
        accounts = [server.toChecksumAddress(i) for i in server.eth.accounts]
        #print(get_accuracy('models/model.pkl',0))
        return render_template('files.html', fileData=fileData)


@app.route('/download', methods=['GET', 'POST'])
def download():
    if request.method == 'POST':
        fetch_models_from_ipfs(fetch_file_data())
        print("Done")
        return redirect(url_for('display'))


@app.route('/average', methods=['POST'])
def average():
    os.chdir('../ai')
    print(os.path.abspath(os.curdir))
    os.system('python3 ai.py org ../organization/models/model.pkl > /dev/null')
    os.chdir('../organization')

    return redirect(url_for('display'))


@app.route('/publish', methods=['POST'])
def publish():
    api = ipfsapi.connect('127.0.0.1', 5001)
    res = api.add('models/model.pkl')
    ipfsHash = res['Hash']
    print(ipfsHash)
    contract = server.eth.contract(address=CONTRACT_ADDRESS,
                                   abi=CONTRACT_ABI)

    account = session.get('account', DEFAULT_ACCOUNT)
    print(account)
    if account is not None:
        tx_hash = contract.functions.setCheckPointIpfsHash(ipfsHash).transact(
            {'from': account})
        receipt = server.eth.waitForTransactionReceipt(tx_hash)
        print("Gas Used ", receipt.gasUsed)

    return redirect(url_for('display'))
