#!/usr/bin/env python
#
# 2019 @nyxgeek - TrustedSec
# checks for return code from:
# https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx
#
# Thanks to @jarsnah12 and @initroott for contributions!

import requests
from requests.exceptions import ConnectionError, ReadTimeout, Timeout
import datetime
import os
import time
import threading
from threading import Semaphore
import logging
#from retrying import retry
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# include standard modules
import argparse

writeLock = Semaphore(value = 1)

# initiate the parser
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--domain", help="target domain name", required=True)
parser.add_argument("-t", "--tenant", help="tenant name (default: based off domain name)")
parser.add_argument("-u", "--username", help="user to target")
parser.add_argument("-U", "--userfile", help="file containing users to target")
parser.add_argument("-o", "--output", help="file to write output to (default: output.log)")
parser.add_argument("-v", "--verbose", help="enable verbose output", action='store_true')
parser.add_argument("-T", "--threads", help="total number of threads (defaut: 10)")

username = "FakeUser"
verbose = False
isUser = False
isUserFile = False
outputfilename = "output.log"


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
    if targetsections > 2:
        targetextension = (targetdomainarray[(targetsections-2)]+"_"+targetdomainarray[(targetsections-1)])
        #print("Extension is: %s" % targetextension )
    else:
        targetextension = (targetdomainarray[(targetsections-1)])
        #print("Extension is: %s" % targetextension )

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

if args.threads:
    thread_count = args.threads
else:
    thread_count = 10




def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session




print("\n+-----------------------------------------+")
print("|           OneDrive Enumerator           |")
print("|       2019 @nyxgeek - TrustedSec        |")
print("+-----------------------------------------+\n")

#@retry
def checkURL(userline):
    #global r
    username = (userline.rstrip()).replace(".","_")
    if ( "@" in username ):
        if verbose:
            print("Email address format detected, converting to username format")
        username = username.split("@")[0]


    url = 'https://' + tenantname + '-my.sharepoint.com/personal/' + username + '_' + targetdomain + '_' + targetextension + '/_layouts/15/onedrive.aspx'
    if verbose:
        writeLock.acquire()
        print("Url is: %s" % url)
        writeLock.release()

    requests.packages.urllib3.disable_warnings()

    try:
        r = requests_retry_session().head(url, timeout=2.0)
    except requests.ConnectionError as e:
        if verbose:
            print("Error: %s" % e)

        print("Encountered connection error. Let's sleep on it.")
        time.sleep(3)
        checkURL(userline)
        #continue
    except requests.Timeout as e:
        if verbose:
            print("Error: %s" % e)
        print("Read Timeout reached, sleeping for 3 seconds")
        time.sleep(3)
        checkURL(userline)
    except requests.RequestException as e:
        if verbose:
            print("Error: %s" % e)
        print("Request Exception - weird. Gonna sleep for 3")
        time.sleep(3)
        checkURL(userline)
        #continue
    except:
        print("Well, I'm not sure what just happened. Onward we go...")
        time.sleep(3)
        checkURL(userline)

    if r.status_code == 403:
        RESPONSE = "[+] [403] VALID ONEDRIVE FOR"
    elif r.status_code == 401:
        RESPONSE = "[+] [401] VALID ONEDRIVE FOR"
    elif r.status_code == 404:
        RESPONSE = "[-] [404] not found"
    else:
        RESPONSE = "[?] [" + str(r.status_code) + "] UNKNOWN RESPONSE"

    domain_rebuilt = targetdomain.replace("_",".") + "." + targetextension.replace("_",".")

    writeLock.acquire()
    print("%s %s - %s, username:%s@%s" % (RESPONSE,domain_rebuilt,username, username.replace("_","."),domain_rebuilt))
    writeLock.release()
    of.write("%s %s - %s, username:%s@%s\n" % (RESPONSE,domain_rebuilt,username, username.replace("_","."),domain_rebuilt))

    of.flush()

#def doNothing(userline):
#  logging.info("Doing nothing with: " + userline)
#  time.sleep(10)

def checkUserFile():

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")

    print("Beginning enumeration of https://%s-my.sharepoint.com/personal/USER_%s_%s/" % (tenantname,targetdomain,targetextension))
    currenttime=datetime.datetime.now()

    of.write("Started enumerating onedrive at {0}\n".format(currenttime))
    of.flush()

    f = open(userfile)
    listthread=[]
    for userline in f:
        #if threading.activeCount() < thread_count:
        while int(threading.active_count()) >= int(thread_count):
            #print "We have enough threads, sleeping."
            time.sleep(1)

        #print "Spawing thread for: " + userline + " thread(" + str(threading.activeCount()) +")"
        x = threading.Thread(target=checkURL, args=(userline,))

        listthread.append(x)
        x.start()

    f.close()

    for i in listthread:
        i.join()
    return


def checkUser():
    url = 'https://' + tenantname + '-my.sharepoint.com/personal/' + username + '_' + targetdomain + '_' + targetextension + '/_layouts/15/onedrive.aspx'
    print("Url is: %s" % url)

    r = requests_retry_session().get(url)

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
        r = requests_retry_session().head(url, timeout=1.0)
    except requests.ConnectionError as e:
        if verbose:
            print("%s" % e)
        print("Tenant does not exist - please specify tenant with --tenant or -t option")
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


of = open((os.path.abspath(outputfilename)),"a")
testConnect()
of.close()
