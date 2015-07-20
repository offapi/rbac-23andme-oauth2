#!/usr/bin/python

# based on https://github.com/23andMe/api-example-flask

import requests
import flask
import os
import sys
from flask import request, config

ancestry_threshold = 0.75  # standard ancestry speculation

# app.config.from_object('yourapplication.default_settings')

API_SERVER = "api.23andme.com"
BASE_API_URL = "https://%s/" % API_SERVER
DEFAULT_SCOPE = "ancestry"

app = flask.Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('rbac.cfg', silent=False)

def load_config(key):
    if not key in app.config:
        app.config[key] = os.getenv(key)
    if not app.config[key]:
        print "Config %s missing" % key
        sys.exit(1)
    return app.config[key]

# required config
CLIENT_ID=load_config('CLIENT_ID')
CLIENT_SECRET=load_config('CLIENT_SECRET')
REDIRECT_URI=load_config('REDIRECT_URI')
DEBUG=True #os.getenv('DEBUG')

@app.route('/')
def index():
    return flask.render_template('index.html', client_id = CLIENT_ID)

@app.route('/receive_code/')
def receive_code():
    parameters = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': request.args.get('code'),
        'redirect_uri': REDIRECT_URI,
        'scope': DEFAULT_SCOPE
    }
    response = requests.post(
        "%s%s" % (BASE_API_URL, "token/"),
        data = parameters,
        verify = False
    )

    if response.status_code == 200:
        #print response.JSON
        access_token = response.json()['access_token']
        #print "Access token: %s\n" % (access_token)

        ## NEED TO FETCH PROFILE ID

        headers = {'Authorization': 'Bearer %s' % access_token}
        ancestry_response = requests.get("%s%s" % (BASE_API_URL, "1/ancestry/"), # /profileid
                                         params = {'threshold': ancestry_threshold},
                                         headers= headers,
                                         verify = False)
        if ancestry_response.status_code == 200:
            return flask.render_template('receive_code.html', res = ancestry_response.text)
        else:
            reponse_text = ancestry_response.text
            print "error %s" % reponse_text
            response.raise_for_status()
    else:
        print "error %s" % response.text
        response.raise_for_status()


if __name__ == '__main__':
    app.run(debug=DEBUG)