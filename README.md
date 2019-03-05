# onedrive_user_enum
enumerate valid onedrive users


## overview
OneDrive users have a file share URL with a known location:

https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx

In this instance, the username is 'lightmand' and the domain is 'acmecomputercompany.com'. If a user has logged into OneDrive, this path will exist and return a 403 status code. If they have not, or the user is invalid, it will return a 404.

The results may vary depending on how widely used OneDrive is within an org. It will often have less coverage than a full user-enum brute force attack via a tool like office365userenum (https://bitbucket.org/grimhacker/office365userenum), but it does not attempt a login and is much more passive, and undetectable to the target org. Microsoft will see the hits, but the target org won't.


## usage

Python:

```
> python onedrive_enum.py -U users.txt -t acmecomputercompany.com
Setting target to acmecomputercompany.com
Domain is: acmecomputercompany
Extension is: com
Reading users from file: users.txt
Beginning enumeration of acmecomputercompany.com ...
[-] [404] not found fakeuser
[-] [404] not found fake.user
[-] [404] not found westb
[+] [403] VALID ONEDRIVE FOR westa
[-] [404] not found westc
[+] [403] VALID ONEDRIVE FOR lightmand
[-] [404] not found admin
[-] [404] not found crabapplee
[+] [403] VALID ONEDRIVE FOR johns
[-] [404] not found venturej
[-] [404] not found stevens
[-] [404] not found stevenf
>
```

Bash:
```
> ./onedrive_enum.sh acmecomputercompany.com users.txt
+-----------------------------------------+
|           OneDrive Enumerator           |
|       2019 @nyxgeek - TrustedSec        |
+-----------------------------------------+

Determine whether a user has OneDrive set up. Useful as backup method for enumeration.
Checks for existence of following-style path:
https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx

[-] [404] NOT FOUND  fakeuser
[-] [404] NOT FOUND  fake.user
[-] [404] NOT FOUND  westb
[+] [403] ONEDRIVE EXISTS FOR  westa
[-] [404] NOT FOUND  westc
[+] [403] ONEDRIVE EXISTS FOR  lightmand
[-] [404] NOT FOUND  admin
[-] [404] NOT FOUND  crabapplee
[+] [403] ONEDRIVE EXISTS FOR  johns
[-] [404] NOT FOUND  venturej
[-] [404] NOT FOUND  stevens
[-] [404] NOT FOUND  stevenf
>
```

### Note: Users that are valid but who have not yet signed into OneDrive will return a 404 not found.
