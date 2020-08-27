#!/usr/bin/env python
#
# 2019 @nyxgeek - TrustedSec
# checks for return code from:
# https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx


import requests
from requests.exceptions import ConnectionError, ReadTimeout, Timeout
import datetime
import os
import time
import threading


# include standard modules
import argparse

# initiate the parser
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--domain", help="target domain name", required=True)
parser.add_argument("-t", "--tenant", help="tenant name (default: based off domain name)")
parser.add_argument("-u", "--username", help="user to target")
parser.add_argument("-U", "--userfile", help="file containing users to target")
parser.add_argument("-o", "--output", help="file to write output to (default: onedrive_enum.log)")
parser.add_argument("-v", "--verbose", help="enable verbose output", action='store_true')
parser.add_argument("-T", "--threads", help="total number of threads (defaut: 10)")

username = "FakeUser"
verbose = False
isUser = False
isUserFile = False
outputfilename = "onedrive_enum.log"


# read arguments from the command line
args = parser.parse_args()

if args.domain:
    #print("Setting target to %s" % args.domain)
    targetdomainarray = (args.domain.split('.'))
    targetdomain=targetdomainarray[0]

    # set tenantname here by default
    tenantname = targetdomain
    if verbose:
        print("Domain is: %s" % targetdomain)
    targetsections=len(targetdomainarray)
    targetextension = (targetdomainarray[(targetsections-1)])
    if verbose:
        print("Extension is: %s" % targetextension )

if args.tenant:
    # if a tenant is specified, overwrite the default domain one
    print("Setting tenant as: %s" % args.tenant)
    tenantname = args.tenant

if args.output:
    outputfilename = args.output

if args.verbose:
    verbose = True

if args.threads:
    thread_count = args.threads
else:
    thread_count = 10

if args.username:
    print("Checking username: %s" % args.username)
    username = args.username.replace(".","_")
    #checkUser()
    isUser = True

if args.userfile:
    print("Reading users from file: %s" % args.userfile)
    global userfile
    userfile = args.userfile
    #checkUserFile()
    global isUserfile
    isUserFile = True







print("\n+-----------------------------------------+")
print("|           OneDrive Enumerator           |")
print("|       2019 @nyxgeek - TrustedSec        |")
print("+-----------------------------------------+\n")

def checkURL(userline):
    of = open((os.path.abspath(outputfilename)),"a")
    username = (userline.rstrip()).replace(".","_")

    if ( "@" in username ):
        if verbose:
            print("Email address format detected, converting to username format")
        username = username.split("@")[0]


    url = 'https://' + tenantname + '-my.sharepoint.com/personal/' + username + '_' + targetdomain + '_' + targetextension + '/_layouts/15/onedrive.aspx'
    if verbose:
        print("Url is: %s" % url)

    requests.packages.urllib3.disable_warnings()

    try:
        r = requests.head(url, timeout=2.0)
    except requests.ConnectionError as e:
        if verbose:
            print e

        print("Encountered connection error. Let's sleep on it.")
        time.sleep(3)
    except requests.Timeout as e:
        print("Read Timeout reached, sleeping for 3 seconds")
        time.sleep(3)
    except requests.RequestException as e:
        print("Request Exception - weird. Gonna sleep for 3")
        time.sleep(3)
    if r.status_code == 403:
        RESPONSE = "[+] [403] VALID ONEDRIVE FOR"
    elif r.status_code == 401:
        RESPONSE = "[+] [401] VALID ONEDRIVE FOR"
    elif r.status_code == 404:
        RESPONSE = "[-] [404] not found"
    else:
        RESPONSE = "[?] [" + str(r.status_code) + "] UNKNOWN RESPONSE"

    print("%s %s.%s - %s, username:%s@%s.%s" % (RESPONSE,targetdomain,targetextension,username, username.replace("_","."),targetdomain,targetextension))
    of.write("%s %s.%s - %s, username:%s@%s.%s\n" % (RESPONSE,targetdomain,targetextension,username, username.replace("_","."),targetdomain,targetextension))
    of.flush()
    of.close()


def checkUserFile():
    print("Beginning enumeration of https://%s-my.sharepoint.com/personal/USER_%s_%s/" % (tenantname,targetdomain,targetextension))
    of = open((os.path.abspath(outputfilename)),"a")
    currenttime=datetime.datetime.now()        
    of.write("Started enumerating onedrive at {0}\n".format(currenttime))
    of.close()

    f = open(userfile)
    listthread=[]
    for userline in f:

        while int(threading.activeCount()) >= int(thread_count):
            # We have enough threads, sleeping.
            time.sleep(3)

        x = threading.Thread(target=checkURL, args=(userline,))
        x.start()
        listthread.append(x)

    f.close()
    
    for i in listthread:
    	i.join()
    return


def checkUser():
    url = 'https://' + tenantname + '-my.sharepoint.com/personal/' + username + '_' + targetdomain + '_' + targetextension + '/_layouts/15/onedrive.aspx'
    print("Url is: %s" % url)

    r = requests.get(url)

    if r.status_code == 403:
        RESPONSE = "[+] [403] VALID ONEDRIVE FOR"
    elif r.status_code == 401:
        RESPONSE = "[+] [401] VALID ONEDRIVE FOR"
    elif r.status_code == 404:
        RESPONSE = "[-] [404] not found"
    else:
        RESPONSE = "[?] [" + str(r.status_code) + "] UNKNOWN RESPONSE"

    print("%s %s" % (RESPONSE,username))


def testConnect():
    url = 'https://' + tenantname + '-my.sharepoint.com/personal/TESTUSER_' + targetdomain + '_' + targetextension + '/_layouts/15/onedrive.aspx'
    requests.packages.urllib3.disable_warnings()

    try:
        r = requests.head(url, timeout=1.0)
    except requests.ConnectionError as e:
        if verbose:
            print e
        print("Tenant does not exist - please specify tenant with -t option")
        quit()


    if r.status_code:
        print("Connection to https://%s-my.sharepoint.com was successful..." % tenantname )
        if isUser:
            checkUser()
        if isUserFile:
            checkUserFile()
    else:
        print("Could not reach %s" % url)
        quit()

testConnect()
