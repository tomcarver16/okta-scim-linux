#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright © 2016-2017, Okta, Inc.
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import os
import re
import uuid
import pwd
import sys
import traceback

from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask_socketio import SocketIO
from flask_socketio import emit
from flask_sqlalchemy import SQLAlchemy
import flask

app = Flask(__name__)
database_url = os.getenv('DATABASE_URL', 'sqlite:///test-users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
db = SQLAlchemy(app)
socketio = SocketIO(app)


class ListResponse():
    def __init__(self, list, start_index=1, count=None, total_results=0):
        self.list = list
        self.start_index = start_index
        self.count = count
        self.total_results = total_results

    def to_scim_resource(self):
        rv = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": self.total_results,
            "startIndex": self.start_index,
            "Resources": []
        }
        resources = []
        for item in self.list:
            resources.append(item.to_scim_resource())
        if self.count:
            rv['itemsPerPage'] = self.count
        rv['Resources'] = resources
        return rv


class User():
    def __init__(self, userName, firstName, lastName, middleName=None, password="password1", active=True, uid=uuid.uuid4()):
        self.active = active
        self.userName = userName
        self.givenName = firstName
        self.familyName = lastName
        self.middleName = middleName
        self.id = uid
        user_file.append_file(self.userName, self.id)

    @staticmethod
    def run_command(command):
        os.system("{0}".format(command))
        return 

    def to_scim_resource(self):
        rv = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": self.id,
            "userName": self.userName,
            "name": {
                "familyName": self.familyName,
                "middleName": self.middleName,
                "givenName": self.givenName,
            },
            "active": self.active,
            "meta": {
                "resourceType": "User",
                "location": url_for('user_get',
                                    user_id=self.id,
                                    _external=True),
                # "created": "2010-01-23T04:56:22Z",
                # "lastModified": "2011-05-13T04:42:34Z",
            }
        }
        return rv

class ServiceProviderConfigs():
    def __init__(self, implemented_capabilities=None):
        self.list = implemented_capabilities

    def to_scim_resource(self):
        rv = {
            "urn:okta:schemas:scim:providerconfig:1.0":{
                "userManagementCapabilities": [
                    "GROUP_PUSH",
                    "IMPORT_NEW_USERS",
                    "IMPORT_PROFILE_UPDATES",
                    "PUSH_NEW_USERS",
                    "PUSH_PASSWORD_UPDATES",
                    "PUSH_PENDING_USERS",
                    "PUSH_PROFILE_UPDATES",
                    "PUSH_USER_DEACTIVATION",
                    "REACTIVATE_USERS"
                ]
            }
        }
        return rv

class ScimFile():
    def __init__(self, fileName):
        self.fileName = fileName
        f = open(fileName, "w+")
        f.close()
        self.dict = {}
    
    def append_file(self, user, uid):
        with open(self.fileName, "w+") as f:
            f.write("{0} : {1}\n".format(uid, user))
        return 
    
    def get_dictonary(self):
        with open(self.fileName, "r+") as f:
            for line in f:
                if line != None:
                    (key, val) = line.split(":")
                    self.dict[key] = val
                else:
                    return self.dict
        return self.dict

    def update_dictonary(self):
        return self.get_dictonary()
        

    

def scim_error(message, status_code=500):
    rv = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "detail": message,
        "status": str(status_code)
    }
    return flask.jsonify(rv), status_code


def send_to_browser(obj):
    socketio.emit('user',
                  {'data': obj},
                  broadcast=True,
                  namespace='/test')


def render_json(obj):
    rv = obj.to_scim_resource()
    send_to_browser(rv)
    return flask.jsonify(rv)


@socketio.on('connect', namespace='/test')
def test_connect():
    return
    # for user in User.query.filter_by(active=True).all():
    #     emit('user', {'data': user.to_scim_resource()})


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    print('Client disconnected')


@app.route('/')
def hello():
    return render_template('base.html')


@app.route("/scim/v2/Users/<user_id>", methods=['GET'])
def user_get(user_id):
    return
    # try:
    #     user = User.query.filter_by(id=user_id).one()
    # except:
    #     return scim_error("User not found", 404)
    # return render_json(user)

# def encode_utf8(toBeEncoded):
#     print(toBeEncoded)
#     if type(toBeEncoded) == list:
#         for item in toBeEncoded: 
#             if type(item) == dict:
#                 encode_utf8(item)
#             item = item.encode('utf-8')
#     else:
#         for key in list(toBeEncoded.keys()):
#             if type(toBeEncoded[key]) == list or type(toBeEncoded[key]) == dict:
#                 encode_utf8(toBeEncoded[key])
#             toBeEncoded[key] = toBeEncoded[key].encode('utf-8')
#     return toBeEncoded

@app.route("/scim/v2/ServiceProviderConfigs", methods=['GET'])
def implemented_capabilities():
    print("/ServiceProviderConfigs GET")
    data = ServiceProviderConfigs()
    return render_json(data)

@app.route("/scim/v2/Users", methods=['POST'])
def users_post():
    print("/Users POST")
    user_resource = request.get_json(force=True)
    userName = user_resource["userName"].split("@")[0]
    firstName = user_resource["name"]["givenName"]
    lastName = user_resource["name"]["familyName"]
    password = user_resource["password"]
    active = user_resource["active"]
    user = User(userName, firstName, lastName, password=password, active=active, uid=uuid.uuid4())
    print('useradd -p {0} -c "{1}" -s {2} {3}'.format(password, firstName + ", " + lastName + ", " + uuid.uuid4(), "/bin/bash", userName))
    User.run_command('useradd -p {0} -c "{1}" -s {2} {3}'.format(password, firstName + ", " + lastName + ", " + uuid.uuid4(), "/bin/bash", userName))
    rv = user.to_scim_resource()
    send_to_browser(rv)
    resp = flask.jsonify(rv)
    resp.headers['Location'] = url_for('user_get',
                                        user_id=user.id,
                                        _external=True)
    return resp, 201


@app.route("/scim/v2/Users/<user_id>", methods=['PUT'])
def users_put(user_id):

    return
    # user_resource = request.get_json(force=True)
    # userName = user_resource["userName"].split("@")[0]
    # firstName = user_resource["name"]["givenName"]
    # lastName = user_resource["name"]["familyName"]
    # password = user_resource["password"]
    # active = user_resource["active"]
    # user = User(userName, firstName, lastName, password=password, active=active, uid=uuid.uuid4())
    # print('useradd -p {0} -c "{1}" {2}'.format(password, firstName + " " + lastName, userName))
    # os.setuid(os.geteuid())
    # os.system('useradd -p {0} -c "{1}" {2}'.format(password, firstName + " " + lastName, userName))
    # rv = user.to_scim_resource()
    # send_to_browser(rv)
    # resp = flask.jsonify(rv)
    # resp.headers['Location'] = url_for('user_get',
    #                                     user_id=user.userName,
    #                                     _external=True)
    # return resp, 201
    # user_resource = request.get_json(force=True)
    # user = User.query.filter_by(id=user_id).one()
    # user.update(user_resource)
    # db.session.add(user)
    # db.session.commit()
    # return render_json(user)


@app.route("/scim/v2/Users/<user_id>", methods=['PATCH'])
def users_patch(user_id):
    print("/Users PATCH")
    patch_resource = request.get_json(force=True)
    if user_map.get(user_id):
        if bool(patch_resource["active"]) == False:
            User.run_command('userdel {0}'.format(user_map.get(user_id))) #TODO: Delete user from text file on completion
        else:
            #TODO: Check pwd for differences of users
            return

    # user_details = pwd.getpwnam(user_map.get(user_id))
    # rv = user.to_scim_resource()
    # send_to_browser(rv)
    # resp = flask.jsonify(rv)

    return
    # patch_resource = request.get_json(force=True)
    # for attribute in ['schemas', 'Operations']:
    #     if attribute not in patch_resource:
    #         message = "Payload must contain '{}' attribute.".format(attribute)
    #         return message, 400
    # schema_patchop = 'urn:ietf:params:scim:api:messages:2.0:PatchOp'
    # if schema_patchop not in patch_resource['schemas']:
    #     return "The 'schemas' type in this request is not supported.", 501
    # user = User.query.filter_by(id=user_id).one()
    # for operation in patch_resource['Operations']:
    #     if 'op' not in operation and operation['op'] != 'replace':
    #         continue
    #     value = operation['value']
    #     for key in value.keys():
    #         setattr(user, key, value[key])
    # db.session.add(user)
    # db.session.commit()
    # return render_json(user)


@app.route("/scim/v2/Users", methods=['GET'])
def users_get():
    print("/Users GET")
    users = list(pwd.getpwall())
    userList = []
    total_results = 0
    for usr in users:
        if usr.pw_uid >= 1000 and usr.pw_uid <= 60000:
            userName = str(usr[0])
            firstName = str(usr[4]).split(" ")[0]
            lastName = str(usr[4]).split(" ")[1].replace(",", "")
            userList.append(User(userName, firstName, lastName, active=True, uid=uuid.uuid4()))
            total_results+=1
    rv = ListResponse(userList,
                      start_index=1,
                      total_results=total_results)
    return flask.jsonify(rv.to_scim_resource())


@app.route("/scim/v2/Groups", methods=['GET'])
def groups_get():
    rv = ListResponse([])
    return flask.jsonify(rv.to_scim_resource())


@app.route("/db", methods=['POST'])
def create_db():
    db.create_all()
    return "create_all OK"


if __name__ == "__main__":
    try: 
        user_file = ScimFile("users.txt")
        user_map = user_file.get_dictonary()
    except Exception as e: 
        print("Error writing file {0} {1}".format(e, traceback.format_exc()))
    euid = os.geteuid()
    if euid != 0:
        print "Script not started as root. Running sudo.."
        args = ['sudo', sys.executable] + sys.argv + [os.environ]
        os.execlpe('sudo', *args)

    print 'Running. Your euid is', euid
    # app.debug = True
    socketio.run(app)
