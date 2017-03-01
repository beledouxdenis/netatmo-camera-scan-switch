#!/usr/bin/env python
import datetime
import json
import getpass
import os
import pprint
import sys
import time
import urllib
import urllib2

API_URL = 'https://api.netatmo.com/api'
OAUTH_TOKEN_URL = 'https://api.netatmo.com/oauth2/token'
OAUTH_CLIENT_ID = ''
OAUTH_CLIENT_SECRET = ''

HOME_ID = ''
CAMERA_IDS = []

DEVICES = {
    'sarah': {
        'ip': '192.168.1.10',
    },
    'john': {
        'ip': '192.168.1.11',
        'ip': '192.168.1.12'
    }
}

TIME_BEFORE_ENABLE = 300

FILE_BASE = '%s/.netatmo' % os.path.expanduser('~')
FILE_TOKENS = '%s/tokens' % FILE_BASE
FILE_STATE = '%s/camera_state' % FILE_BASE

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class util:

    @staticmethod
    def request(url, get={}, post={}):
        if get:
            url = '%s?%s' % (url, urllib.urlencode(get))
        req = urllib2.Request(url, urllib.urlencode(post))
        return urllib2.urlopen(req).read()

    @staticmethod
    def scan_ip(ips):
        return [ip for ip in ips if os.system("ping -c 1 -W 30 " + ip) == 0]


class netatmo:

    @staticmethod
    def save_tokens(tokens):
        tokens['expires_on'] = (datetime.datetime.now() + datetime.timedelta(seconds=tokens.get('expires_in'))).strftime(DATETIME_FORMAT)
        with open(FILE_TOKENS, 'w') as fp:
            fp.write(json.dumps(tokens))

    @staticmethod
    def authenticate():
        username, password = raw_input("Netatmo username (login/email):"), getpass.getpass("Netatmo password:")
        values = {
            'grant_type': 'password',
            'client_id': OAUTH_CLIENT_ID,
            'client_secret': OAUTH_CLIENT_SECRET,
            'username': username,
            'password': password,
            'scope': 'read_camera access_camera',
        }

        try:
            tokens = json.loads(util.request(OAUTH_TOKEN_URL, post=values))
            netatmo.save_tokens(tokens)
        except urllib2.HTTPError:
            sys.exit('Cannot authenticate to Netatmo services.')
        return tokens

    @staticmethod
    def refresh_access_token(refresh_token):
        values = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': OAUTH_CLIENT_ID,
            'client_secret': OAUTH_CLIENT_SECRET,
        }
        try:
            tokens = json.loads(util.request(OAUTH_TOKEN_URL, post=values))
            netatmo.save_tokens(tokens)
        except urllib2.HTTPError:
            sys.exit('Cannot refresh access token.')
        return tokens

    @staticmethod
    def get_access_token():
        tokens = None
        with open(FILE_TOKENS, 'r') as fp:
            saved_tokens = fp.read()
        if saved_tokens:
            tokens = json.loads(saved_tokens)
            if datetime.datetime.now() > datetime.datetime.strptime(tokens['expires_on'], DATETIME_FORMAT):
                tokens = netatmo.refresh_access_token(tokens['refresh_token'])
        if not tokens:
            tokens = netatmo.authenticate()
        return tokens['access_token']

    @staticmethod
    def get_home_data():
        access_token = netatmo.get_access_token()
        params = {'access_token': access_token}
        if HOME_ID:
            params['home_id'] = HOME_ID
        return json.loads(util.request('%s/gethomedata' % API_URL, get=params))

    @staticmethod
    def cameras_change_status(status):
        change = False
        if os.path.exists(FILE_STATE):
            with open(FILE_STATE, 'r') as fp:
                try:
                    last_status, last_status_time = fp.read().split(',')
                    if last_status != status:
                        if last_status == 'on' or time.time() - float(last_status_time) > TIME_BEFORE_ENABLE:
                            change = True
                except Exception:
                    change = True
        else:
            change = True
        if change:
            home_data = netatmo.get_home_data()
            pprint.pprint(home_data)
            homes = home_data.get('body', {}).get('homes', [])
            for home in homes:
                cameras = home.get('cameras')
                for camera in cameras:
                    if camera['id'] in CAMERA_IDS and camera['status'] != status:
                        res = json.loads(util.request('%s/command/ping' % (camera['vpn_url'],), get={'status': status}))
                        util.request('%s/command/changestatus' % res['local_url'], get={'status': status})

        if change or status == 'off':
            with open(FILE_STATE, 'w') as fp:
                fp.write('%s,%s' % (status, time.time()))

if __name__ == "__main__":
    if not os.path.exists(FILE_BASE):
        os.makedirs(FILE_BASE)
    if not os.path.exists(FILE_TOKENS):
        netatmo.authenticate()

    scans = set(prop for device, properties in DEVICES.items() for prop in properties)
    presence = {}

    for scan in scans:
        scan_method = getattr(util, 'scan_%s' % scan)
        if scan_method:
            ips = [properties[scan] for device, properties in DEVICES.items() if scan in properties]
            presence[scan] = scan_method(ips)

    for device, properties in DEVICES.items():
        if all(value in presence.get(prop, []) for prop, value in properties.items()):
            netatmo.cameras_change_status('off')
            break
    else:
        netatmo.cameras_change_status('on')
