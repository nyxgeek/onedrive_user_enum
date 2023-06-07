
# onedrive_user_enum v2.00
enumerate valid onedrive users

For a full rundown of the enumeration technique and OneDrive enum, check out the blog here:

https://www.trustedsec.com/blog/onedrive-to-enum-them-all/




### Now featuring:
* Local Database (sqlite3)
* Auto-lookup of tenants (thanks @DrAzureAD and @thetechr0mancer)
* Read in file OR folder of files
* Append -- easily create 'jsmith1' 'jsmith2' sprays
* Skip-Tried (de-dupe) -- remove previously tried usernames
* Kill-After -- cancel a userlist if no usernames identified within 'x' attempts

## OneDrive Enumeration overview:
OneDrive users have a file share URL with a known location:

https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx

In this instance, the username is 'lightmand' and the domain is 'acmecomputercompany.com'. If a user has logged into OneDrive, this path will exist and return a 403 status code. If they have not, or the user is invalid, it will return a 404.

The results may vary depending on how widely used OneDrive is within an org. Currently it is the most reliable user-enumeration method that I'm aware of (office365userenum no longer works, and the others like UhOh365 are unreliable). Further, it does not attempt a login and is much more passive, and should be undetectable to the target org. Microsoft will see the hits, but the target org won't.


## usage:

```
 # ./onedrive_enum.py -h

*********************************************************************************************************

                                         ██████               ███                          
                                        ░░████               ░░░                           
   ██████    █████████     ███████    ████████   █████████   ████   █████  █████   ███████ 
  ███░░███  ░░███░░░███   ███░░░███  ███░░░███  ░░███░░░███ ░░███  ░░███  ░░███   ███░░░███
 ░███  ░███  ░███  ░███  ░████████  ░███ ░░███   ░███  ░░░   ░███   ░███   ░███  ░████████ 
 ░███  ░███  ░███  ░███  ░███░░░░   ░███ ░░███   ░███        ░███   ░░███  ███   ░███░░░   
 ░░██████    ████  █████ ░░███████  ░░█████████  ██████      █████   ░░██████    ░░███████ 
  ░░░░░░    ░░░░  ░░░░░   ░░░░░░░    ░░░░░░░░░  ░░░░░░      ░░░░░     ░░░░░░      ░░░░░░░  
                                                                             
                                                                             
   ██████  ████████   █████ ████ █████████████      +-------------------------------------------------+
  ███░░███░░███░░███ ░░███ ░███ ░░███░░███░░███     |               OneDrive Enumerator               |
 ░███████  ░███ ░███  ░███ ░███  ░███ ░███ ░███     |           2023 @nyxgeek - TrustedSec            |
 ░███░░░   ░███ ░███  ░███ ░███  ░███ ░███ ░███     |                 version 2.00                    |
 ░░██████  ████ █████ ░░████████ █████░███ █████    |  https://github.com/nyxgeek/onedrive_user_enum  |
  ░░░░░░  ░░░░ ░░░░░   ░░░░░░░░ ░░░░░ ░░░ ░░░░░     +-------------------------------------------------+
                                                                             
*********************************************************************************************************
usage: onedrive_enum.py [-h] -d  [-t] [-u] [-a] [-U] [-p] [-o] [-T] [-e] [-r] [-x] [-n] [-k] [-v]

options:
  -h, --help           show this help message and exit
  -d , --domain        target domain name (required)
  -t , --tenant        tenant name
  -u , --username      user to target
  -a , --append        mutator: append a number, character, or string to a username
  -U , --userfile      file containing usernames (wordlists) -- will also take a directory
  -p , --playlist      file containing list of paths to user lists (wordlists) to try
  -o , --output        file to write output to (default: output.log)
  -T , --threads       total number of threads (defaut: 100)
  -e , --environment   Azure environment to target [commercial (default), chinese, gov]
  -r, --rerun          force re-run of previously tested tenant/domain/wordlist combination
  -x, --skip-tried     dedupe. skip any usernames from previous runs
  -n, --no-db          disable logging to db
  -k , --killafter     kill off non-productive jobs after x tries with no success
  -v, --verbose        enable verbose output


```

## example:
```
# ./onedrive_enum.py -t microsoft -d microsoft.com -U USERNAMES/statistically-likely/jsmith.txt

*********************************************************************************************************

                                         ██████               ███                          
                                        ░░████               ░░░                           
   ██████    █████████     ███████    ████████   █████████   ████   █████  █████   ███████ 
  ███░░███  ░░███░░░███   ███░░░███  ███░░░███  ░░███░░░███ ░░███  ░░███  ░░███   ███░░░███
 ░███  ░███  ░███  ░███  ░████████  ░███ ░░███   ░███  ░░░   ░███   ░███   ░███  ░████████ 
 ░███  ░███  ░███  ░███  ░███░░░░   ░███ ░░███   ░███        ░███   ░░███  ███   ░███░░░   
 ░░██████    ████  █████ ░░███████  ░░█████████  ██████      █████   ░░██████    ░░███████ 
  ░░░░░░    ░░░░  ░░░░░   ░░░░░░░    ░░░░░░░░░  ░░░░░░      ░░░░░     ░░░░░░      ░░░░░░░  
                                                                             
                                                                             
   ██████  ████████   █████ ████ █████████████      +-------------------------------------------------+
  ███░░███░░███░░███ ░░███ ░███ ░░███░░███░░███     |               OneDrive Enumerator               |
 ░███████  ░███ ░███  ░███ ░███  ░███ ░███ ░███     |           2023 @nyxgeek - TrustedSec            |
 ░███░░░   ░███ ░███  ░███ ░███  ░███ ░███ ░███     |                 version 2.00                    |
 ░░██████  ████ █████ ░░████████ █████░███ █████    |  https://github.com/nyxgeek/onedrive_user_enum  |
  ░░░░░░  ░░░░ ░░░░░   ░░░░░░░░ ░░░░░ ░░░ ░░░░░     +-------------------------------------------------+
                                                                             
*********************************************************************************************************

Beginning enumeration of https://microsoft-my.sharepoint.com/personal/USER_microsoft_com/
--------------------------------------------------------------------------------------------------------
[-] [403] VALID USERNAME FOR microsoft,microsoft.com - user1, username:user1@microsoft.com
[-] [403] VALID USERNAME FOR microsoft,microsoft.com - user2, username:user2@microsoft.com
[-] [403] VALID USERNAME FOR microsoft,microsoft.com - user3, username:user3@microsoft.com


```

#### Note: Users that are valid but who have not yet signed into OneDrive will return a 404 not found.


## sHoUtOuTz aNd GrEeTz

Thanks to @DrAzureAD, @thetechr0mancer, @rootsecdev, @hacking_lz
