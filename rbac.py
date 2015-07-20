#!/usr/bin/python

# based on https://github.com/23andMe/api-example-flask

import requests
import flask
from flask import request, config

ancestry_threshold = 0.75  # standard ancestry speculation

# app.config.from_object('yourapplication.default_settings')

PORT = 5000
API_SERVER = "api.23andme.com"
BASE_API_URL = "https://%s/" % API_SERVER
BASE_CLIENT_URL = 'http://localhost:%s/'% PORT
REDIRECT_URI = '%sreceive_code/'  % BASE_CLIENT_URL
DEFAULT_SCOPE = "ancestry"

app = flask.Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('rbac.cfg', silent=False)

# required config
CLIENT_ID = app.config['CLIENT_ID']
CLIENT_SECRET = app.config['CLIENT_SECRET']

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
        print response.json()

        headers = {'Authorization': 'Bearer %s' % access_token}
        ancestry_response = requests.get("%s%s" % (BASE_API_URL, "1/ancestry/"),
                                         params = {'threshold': ancestry_threshold},
                                         headers= headers,
                                         verify = False)
        if ancestry_response.status_code == 200:
            return flask.render_template('receive_code.html', response_json = ancestry_response.json())
        else:
            reponse_text = ancestry_response.text
            response.raise_for_status()
    else:
        response.raise_for_status()


if __name__ == '__main__':
    app.run(debug=True, port=PORT)