
# onedrive_user_enum
enumerate valid onedrive users


## overview:
OneDrive users have a file share URL with a known location:

https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx

In this instance, the username is 'lightmand' and the domain is 'acmecomputercompany.com'. If a user has logged into OneDrive, this path will exist and return a 403 status code. If they have not, or the user is invalid, it will return a 404.

The results may vary depending on how widely used OneDrive is within an org. Currently it is the most reliable user-enumeration method that I'm aware of (office365userenum no longer works, and the others like UhOh365 are unreliable). Further, it does not attempt a login and is much more passive, and should be undetectable to the target org. Microsoft will see the hits, but the target org won't.


## usage:

```
python onedrive_enum.py -U users.txt -d acmecomputercompany.com

Flags:
    -d    target domain
    -T    tenant (optional: try running without specifying this flag first)
    -u    username to test
    -U    file containing usernames to test
    -o    output file (default: onedrive_enum.log)
    -v    verbose mode
    -t    threads (default: 10)

```

## example:
```
> python onedrive_enum.py -U users.txt -d acmecomputercompany.com

+-----------------------------------------+
|           OneDrive Enumerator           |
|       2019 @nyxgeek - TrustedSec        |
+-----------------------------------------+

Reading users from file: users.txt
Connection to https://acmecomputercompany-my.sharepoint.com was successful...
Beginning enumeration of https://acmecomputercompany-my.sharepoint.com/personal/USER_acmecomputercompany_com/
[-] [404] not found acmecomputercompany.com - fakeuser
[-] [404] not found acmecomputercompany.com - fake.user
[-] [404] not found acmecomputercompany.com - westb
[+] [403] VALID ONEDRIVE FOR acmecomputercompany.com - westa
[-] [404] not found acmecomputercompany.com - westc
[+] [403] VALID ONEDRIVE FOR acmecomputercompany.com - lightmand
[-] [404] not found acmecomputercompany.com - admin
[-] [404] not found acmecomputercompany.com - crabapplee
[+] [403] VALID ONEDRIVE FOR acmecomputercompany.com - johns
[-] [404] not found acmecomputercompany.com - venturej
[-] [404] not found acmecomputercompany.com - stevens
[-] [404] not found acmecomputercompany.com - stevenf
>
```

### Note: Users that are valid but who have not yet signed into OneDrive will return a 404 not found.
