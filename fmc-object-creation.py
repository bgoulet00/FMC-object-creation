# this script will create FMC host, range and network objects in bulk
# the input file will be a csv in the format name,description,oject-type,value
# the input file will have a header row with those descriptions which will be stripped off when the file is read
# see the sample csv file for reference

# BASE_URL needs to be updated with the FMC url/ip

# written with python3.6.8 and tested on FMCv7.0.4

import requests
from requests.auth import HTTPBasicAuth
import json
import csv
import os
import sys
import time
from datetime import date

# Disable SSL warnings
import urllib3
urllib3.disable_warnings()

# Global Variables
BASE_URL = 'https://192.168.100.22'
object_file = 'fmc-objects.csv'
logFile = 'fmc-object-creation.log'

# prompt user for FMC credentials
# login to FMC and return the value of auth tokens and domain UUID from the response headers
# exit with an error message if a valid response is not received
def login():
    print('\n\nEnter FMC Credentials')
    user = input("USERNAME: ").strip()
    passwd = input("PASSWORD: ").strip()
    response = requests.post(
       BASE_URL + '/api/fmc_platform/v1/auth/generatetoken',
       auth=HTTPBasicAuth(username=user, password=passwd),
       headers={'content-type': 'application/json'},
       verify=False,
    )
    if response:
        return {'X-auth-access-token': response.headers['X-auth-access-token'], 
        'X-auth-refresh-token':response.headers['X-auth-refresh-token'],
        'DOMAIN_UUID':response.headers['DOMAIN_UUID']}
    else:
        sys.exit('Unable to connect to ' + BASE_URL + ' using supplied credentials')

    
#creates host, range or network objects.  initially the bulk method was tried to create
#all objects in a single call but should FMC have an issue creating any single item in the bulk request
#it rejects/fails the entire request.  this function will create each object one at a time to avoid
#complete failure. this does however require a lot of API calls and therefore check/pause when request limit reached
def createObjects(token, DUUID, objList):

    for obj in objList:
        out_str = '\ncreating' + obj['type'] + 'object' + obj['name'] + obj['value']
        print(out_str)
        with open(logFile, "a") as file:
                file.write(out_str + '\n')
        dict = {'name':obj['name'], 'description':obj['description'], 'type':obj['type'], 'value':obj['value']}
        payload = json.dumps(dict)
        response = requests.post(
            BASE_URL + '/api/fmc_config/v1/domain/' + DUUID + '/object/' + obj['type'] + 's',
            headers={'Content-Type': 'application/json', 'X-auth-access-token':token},
            data=payload,
            verify=False,
            )
        if response.status_code == 429:
            print('request limit reached. pausing 1 minute')
            time.sleep(61)
            response = requests.get(
            BASE_URL + '/api/fmc_config/v1/domain/' + DUUID + '/object/' + obj['type'] + 's',
            headers={'Content-Type': 'application/json', 'X-auth-access-token':token},
            data=payload,
            verify=False,
            )
        if response.status_code == 201:
            out_str = obj['type'] + ' object creation complete'
            print(out_str)
            with open(logFile, "a") as file:
                file.write(out_str)
        else:
            result = response.json()
            out_str = 'object creation failed:' + result['error']['messages'][0]['description']
            print(out_str)
            with open(logFile, "a") as file:
                file.write(out_str)


def main():

    # lists of dictionary objects
    objects = []

    result = login()
    token = result.get('X-auth-access-token')
    DUUID = result.get('DOMAIN_UUID')
    
    #create empty log file
    with open(logFile, "w") as file:
        pass
    
    #read input file and create objects
    if os.path.isfile(object_file):
        print(object_file + ' found. Creating objects.....')
        with open(object_file, "r") as file:
            reader = csv.reader(file)
            next(reader, None) #strip the heading row
            for row in reader:
                objects.append({"name": row[0].strip(),
                                "description": row[1].strip(),
                                "type": row[2].strip(),
                                "value":row[3].strip()})
        createObjects(token, DUUID, objects)
    else:
        print(object_file + ' not present. skipping object creation')
    
if __name__ == "__main__":
    main()
