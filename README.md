# onedrive_user_enum
enumerate valid onedrive users

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
