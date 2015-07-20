#!/usr/bin/python

# based on https://github.com/23andMe/api-example-flask

import requests
import flask
import os
import sys
from flask import request, config
# import urllib3.contrib.pyopenssl
# urllib3.contrib.pyopenssl.inject_into_urllib3()

ancestry_threshold = 0.75  # standard ancestry speculation

# app.config.from_object('yourapplication.default_settings')

API_SERVER = "api.23andme.com"
BASE_API_URL = "https://%s" % API_SERVER
DEFAULT_SCOPE = "basic ancestry"

app = flask.Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('rbac.cfg', silent=True)

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
        "%s%s" % (BASE_API_URL, "/token"),
        data = parameters,
        verify = False
    )

    if response.status_code == 200:
        access_token = response.json()['access_token']
        # fetch profile ids
        user_res = api_req(access_token, "/user/", {})
        profiles = user_res.json()['profiles']
        print "profiles: %s" % profiles
        print user_res.text
        if len(profiles):
            print "got profiles!"
            profile_id = profiles[0]['id']
            ancestry_res = api_req(access_token, "/ancestry/%s/" % profile_id, {'threshold': ancestry_threshold})
            print ancestry_res.text
            return flask.render_template('receive_code.html', res = ancestry_response.text)

def api_req(token, path, params):
    headers = {'Authorization': 'Bearer %s' % token}
    res = requests.get("%s/1%s" % (BASE_API_URL, path), # /profileid
                                     params = params,
                                     headers= headers,
                                     verify = False)
    print res.text
    if res.status_code == 200:
        return res
    else:
        reponse_text = res.text
        print "API error to %s: %s" % (path, reponse_text)
        res.raise_for_status()        

if __name__ == '__main__':
    app.run(debug=DEBUG)