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

# include standard modules
import argparse

# initiate the parser
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--domain", help="target domain name")
parser.add_argument("-t", "--tenant", help="tenant name (default: based off domain name)")
parser.add_argument("-u", "--username", help="user to target")
parser.add_argument("-U", "--userfile", help="file containing users to target")
parser.add_argument("-o", "--output", help="file to write output to (default: onedrive_enum.log)")
parser.add_argument("-v", "--verbose", help="enable verbose output", action='store_true')

username = "FakeUser"
verbose = False
isUser = False
isUserFile = False
outputfilename = "onedrive_enum.log"
print("\n+-----------------------------------------+")
print("|           OneDrive Enumerator           |")
print("|       2019 @nyxgeek - TrustedSec        |")
print("+-----------------------------------------+\n")


def checkUserFile():
    print("Beginning enumeration of https://%s-my.sharepoint.com/personal/USER_%s_%s/" % (tenantname,targetdomain,targetextension))
    with open((os.path.abspath(outputfilename)),"a") as of:
        currenttime=datetime.datetime.now()
        of.write("Started enumerating onedrive at {0}\n".format(currenttime))



        f = open(userfile)
        for userline in f:
            username = userline.rstrip()

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
                continue
            except requests.Timeout as e:
                print("Read Timeout reached, sleeping for 3 seconds")
                time.sleep(3)
            except requests.RequestException as e:
                print("Request Exception - weird. Gonna sleep for 3")
                time.sleep(3)
                continue
            if r.status_code == 403:
                RESPONSE = "[+] [403] VALID ONEDRIVE FOR"
            elif r.status_code == 404:
                RESPONSE = "[-] [404] not found"
            else:
                RESPONSE = "[?] [" + str(r.status_code) + "] UNKNOWN RESPONSE"

            print("%s %s.%s - %s" % (RESPONSE,targetdomain,targetextension,username))
            of.write("%s %s.%s - %s\n" % (RESPONSE,targetdomain,targetextension,username))

        f.close()
    of.close()


def checkUser():
    url = 'https://' + tenantname + '-my.sharepoint.com/personal/' + username + '_' + targetdomain + '_' + targetextension + '/_layouts/15/onedrive.aspx'
    print("Url is: %s" % url)

    r = requests.get(url)

    if r.status_code == 403:
        RESPONSE = "[+] [403] VALID ONEDRIVE FOR"
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
        print("Tenant does not exist - please specify tenant with -T option")
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

if args.username:
    print("Checking username: %s" % args.username)
    username = args.username
    #checkUser()
    isUser = True

if args.userfile:
    print("Reading users from file: %s" % args.userfile)
    userfile = args.userfile
    #checkUserFile()
    isUserFile = True


testConnect()
