from flask import render_template, request, flash, redirect, url_for
from app import *
import ipfsapi
import os, time, requests


def bytes32_to_string(x):
    output = x.hex().rstrip("0")
    if len(output) % 2 != 0:
        output = output + '0'
    output = bytes.fromhex(output).decode('utf8')
    return output


def get_accuracy():
    file = open('../ai/accuracy.txt', 'r')
    accuracy = file.read()

    return accuracy

def fetch_model_from_ipfs(ipfsHash):
    if not os.path.exists('models'):
        os.mkdir('models')

    req = requests.get("http://localhost:8080/ipfs/" + ipfsHash)

    if req.status_code != 200:
        print("Failed to retrieve checkpoint")

    else:
        with open("models/model.pkl", "wb") as f:
            f.write(req.content)


@app.route('/', defaults={'account_no': None}, methods=['GET', 'POST'])
@app.route('/account/set/<string:account_no>', methods=['POST'])
def homepage(account_no):
    if request.method == 'GET':
        accounts = [server.toChecksumAddress(i) for i in server.eth.accounts]
        return render_template('homepage.html', accounts=accounts)
    elif request.method == 'POST':
        session['account'] = account_no
        return redirect(url_for('contract_operations'))


@app.route('/functions', methods=['GET', 'POST'])
def contract_operations():
    if request.method == 'GET':
        account = session.get('account', DEFAULT_ACCOUNT)
        return render_template('functions.html', account=account, accuracy = get_accuracy())
    else:
        return None


@app.route('/addFileToIPFS', methods=['GET', 'POST'])
def addFileToIPFS():
    if request.method == 'POST':

        upload_file = None

        if 'file' not in request.files:
            upload_file = 'temp.txt'
        else:
            upload_file = request.files['file']

        if upload_file.filename == '':
            error = "File wasn't selected!"
            print("File wasn't selected")
            return render_template('functions.html', error=error)

        elif upload_file and allowed_file(upload_file.filename):
            upload_file_filename_secure = secure_filename(upload_file.filename)
            upload_file.save(os.path.join(app.config['UPLOAD_FOLDER'], upload_file_filename_secure))
            print("Uploaded file successfully")
            result = upload_file_sync(upload_file_filename_secure)

            model_number = int(request.form['model_number'])
            filename = upload_file.filename

            api = ipfsapi.connect('127.0.0.1', 5001)
            res = api.add(str(os.path.join(app.config['UPLOAD_FOLDER'], upload_file_filename_secure)))
            ipfsHash = res['Hash']

            contract = server.eth.contract(address=CONTRACT_ADDRESS,
                                           abi=CONTRACT_ABI)

            account = session.get('account', DEFAULT_ACCOUNT)

            if account is not None:
                tx_hash = contract.functions.addFile(model_number, filename, ipfsHash).transact(
                    {'from': account})
                receipt = server.eth.waitForTransactionReceipt(tx_hash)
                print("Gas Used ", receipt.gasUsed)
                return render_template('functions.html', account=account, success=True, accuracy = get_accuracy())
            else:
                flash('No account was chosen')
                return render_template('functions.html', account=account, success=False, accuracy = get_accuracy())

        return render_template('functions.html', error="Something went wrong.")

    account = session.get('account', DEFAULT_ACCOUNT)
    return render_template('functions.html', account=account , accuracy = get_accuracy())


def upload_file_sync(upload_file_filename_secure):
    with app.app_context():
        print("Started")
        path = os.path.join(app.config['UPLOAD_FOLDER'], upload_file_filename_secure)
        while not os.path.exists(path):
            print("Waiting for file to be visible")
            time.sleep(1)

            if os.path.isfile(path):
                print("Now the file is available")

            else:
                raise ValueError("%s isn't a file!" % path)

    print("Finished")
    return True


@app.route('/model_pull', methods=['POST'])
def checkpoint_model_pull():
    contract = server.eth.contract(address=CONTRACT_ADDRESS,
                                   abi=CONTRACT_ABI)

    account = session.get('account', DEFAULT_ACCOUNT)

    ipfsHash = contract.call().getCheckPointIpfsHash()

    print("IPFS Hash", ipfsHash)

    fetch_model_from_ipfs(ipfsHash)

    return redirect(url_for('addFileToIPFS'))


@app.route('/train', methods=['POST'])
def train():
    os.chdir('../ai')
    print(os.path.abspath(os.curdir))
    os.system('python3 ai.py client ../client/models/model.pkl ../client/models/model.pkl')
    os.chdir('../client')

    account = session.get('account', DEFAULT_ACCOUNT)
    return render_template('functions.html', account=account, accuracy=get_accuracy())
