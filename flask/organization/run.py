#!/usr/bin/python3

from app import app
import sys

if __name__ == '__main__':

    deploy_mode = str(sys.argv[1])
    port = int(sys.argv[2])

    if deploy_mode == 'd':
        app.debug = True
        app.run(host='localhost', port=port)

    elif deploy_mode == 'p':
        # Needs pyopenssl package
        app.run(host='0.0.0.0', port=port, ssl_context='adhoc')

    else:
        print("Usage: python run.py <d/p> port_number")
