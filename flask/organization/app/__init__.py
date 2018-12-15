from flask import Flask, session
import web3
from web3 import Web3, HTTPProvider
import json
from flask_session import Session
from flask_qrcode import QRcode

# Flask App initialization
app = Flask(__name__)
app.secret_key = 'secret_key'

SESSION_TYPE = 'redis'
app.config.from_object(__name__)
Session(app)
QRcode(app)

server = Web3(HTTPProvider('http://localhost:7545'))

DEFAULT_ACCOUNT = server.toChecksumAddress("0xf847465aaC31C383540B56eb2B5a57f2C8192172")


from app import views
