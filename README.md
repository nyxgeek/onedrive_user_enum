# onedrive_user_enum
enumerate valid onedrive users

## usage

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

###Note: Users that are valid but who have not yet signed into OneDrive will return a 404 not found.
