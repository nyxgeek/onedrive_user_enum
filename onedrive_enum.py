#!/usr/bin/env python
#
# 2019 @nyxgeek - TrustedSec
# checks for return code from:
# https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx
#
# 403 == valid OneDrive
# 404 == invalid
# Note: Users who are valid but have not used OneDrive will return a 404

import requests
import datetime
import os

# include standard modules
import argparse

# initiate the parser
parser = argparse.ArgumentParser()
#parser.add_argument("-h", "--help", help="help")
parser.add_argument("-t", "--target", help="domain to target")
parser.add_argument("-u", "--username", help="user to target")
parser.add_argument("-U", "--userfile", help="file containing users to target")
parser.add_argument("-o", "--output", help="file to write output to")

outputfilename = "onedrive_enum.log"


def checkUserFile():
    print("Beginning enumeration of %s.%s ..." % (targetdomain,targetextension))
    with open((os.path.abspath(outputfilename)),"a") as of:
        currenttime=datetime.datetime.now()
        of.write("Started enumerating onedrive at {0}\n".format(currenttime))



        f = open(userfile)
        for userline in f:
            username = userline.rstrip()

            url = 'https://' + targetdomain + '-my.sharepoint.com/personal/' + username + '_' + targetdomain + '_' + targetextension + '/_layouts/15/onedrive.aspx'
            #print("Url is: %s" % url)

            requests.packages.urllib3.disable_warnings()
            r = requests.head(url)
            if r.status_code == 403:
                RESPONSE = "[+] [403] VALID ONEDRIVE FOR"
            elif r.status_code == 404:
                RESPONSE = "[-] [404] not found"
            else:
                RESPONSE = "[?] [" + str(r.status_code) + "] UNKNOWN RESPONSE"

            print("%s %s" % (RESPONSE,username))
            of.write("%s %s\n" % (RESPONSE,username))

        f.close()
    of.close()


def checkUser():
    url = 'https://' + targetdomain + '-my.sharepoint.com/personal/' + username + '_' + targetdomain + '_' + targetextension + '/_layouts/15/onedrive.aspx'
    print("Url is: %s" % url)

    r = requests.get(url)

    if r.status_code == 403:
        RESPONSE = "[+] [403] VALID ONEDRIVE FOR"
    elif r.status_code == 404:
        RESPONSE = "[-] [404] not found"
    else:
        RESPONSE = "[?] [" + str(r.status_code) + "] UNKNOWN RESPONSE"

    print("%s %s" % (RESPONSE,username))




# read arguments from the command line
args = parser.parse_args()

if args.target:
    print("Setting target to %s" % args.target)
    targetdomainarray = (args.target.split('.'))
    targetdomain=targetdomainarray[0]
    print("Domain is: %s" % targetdomain)
    targetsections=len(targetdomainarray)
    targetextension = (targetdomainarray[(targetsections-1)])
    print("Extension is: %s" % targetextension )

if args.output:
    outputfilename = args.outputfile

if args.username:
    print("Checking username: %s" % args.username)
    username = args.username
    checkUser()

if args.userfile:
    print("Reading users from file: %s" % args.userfile)
    userfile = args.userfile
    checkUserFile()
