#!/usr/bin/python

# based on https://github.com/23andMe/api-example-flask

import requests
import flask
import os
import sys
import json
from flask import request, config

allowed_population_threshold = 0.51    # minimum allowed match %
ancestry_speculation_threshold = 0.75  # standard ancestry speculation
ancestry_allowed_populations = [ 'French & German', 'British & Irish', 'Finnish', 
    'Scandinavian', 'Northern European', 'Eastern European', 'Balkan', 'Iberian', 
    'Italian', 'Sardinian', 'Southern European' ]
# note: does not include "Ashkenazi" or "European"

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
DEBUG=os.getenv('DEBUG')

@app.route('/')
def index():
    return flask.render_template('index.html', client_id=CLIENT_ID)

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
        if len(profiles):
            profiles = [p for p in profiles if p.genotyped]
            if len(profiles):
                profile_id = profiles[0]['id'] # assume first genotyped profile
                ancestry_res = api_req(access_token, "/ancestry/%s/" % profile_id, {'threshold': ancestry_speculation_threshold})
                ancestry = ancestry_res.json()['ancestry']
                # check if ancestry is valid
                match_total = ancestor_match_pct()
                valid = match_total >= allowed_population_threshold
                return flask.render_template('auth_status.html', valid=valid,match_total=match_total*100)

        return "Error: could not locate any valid profiles with ancestry data"

def api_req(token, path, params):
    headers = {'Authorization': 'Bearer %s' % token}
    res = requests.get("%s/1%s" % (BASE_API_URL, path), # /profileid
                                     params = params,
                                     headers= headers,
                                     verify = False)
    if res.status_code == 200:
        return res
    else:
        reponse_text = res.text
        print "API error to %s: %s" % (path, reponse_text)
        res.raise_for_status()  

# returns percentage of allowed ancestor geographies
def ancestor_match_pct(ancestry, total=0.0):
    # see if we match a desired pop, if so add it to total
    if 'label' in ancestry:
        if ancestry['label'] in ancestry_allowed_populations:
            proportion = ancestry['proportion']
            return proportion

    # if no desired pop, recurse into sub-populations
    if 'sub_populations' in ancestry:
        subtotal = 0.0
        for subpop in ancestry['sub_populations']:
            subtotal += ancestor_match_pct(subpop, total)
        return subtotal

    return total

if __name__ == '__main__':
    app.run(debug=DEBUG)