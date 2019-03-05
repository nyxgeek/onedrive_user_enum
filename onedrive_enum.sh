#!/bin/bash

# OneDrive user enumeration - checks for existence of OneDrive folder indicating user has set up
#https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx
#
# Usage: ./onedrive_enum.sh acmecomputercompany.com users.txt


echo "+-----------------------------------------+"
echo "|           OneDrive Enumerator           |"
echo "|       2019 @nyxgeek - TrustedSec        |"
echo "+-----------------------------------------+"
echo ""
echo "Determine whether a user has OneDrive set up. Useful as backup method for enumeration."
echo "Checks for existence of following-style path:"
echo "https://acmecomputercompany-my.sharepoint.com/personal/lightmand_acmecomputercompany_com/_layouts/15/onedrive.aspx"
echo ""

DOMAIN=`echo "$1" | rev | cut -d. -f2- | rev`
EXTENSION=`echo "$1" | rev | cut -d. -f1 | rev`
USERLIST=$2

while read line; do
#echo  "[*] Testing for: $line"

RESPONSECODE=`curl -k -s -o /dev/null -I -w "%{http_code}" https://"$DOMAIN"-my.sharepoint.com/personal/"$line"_"$DOMAIN"_"$EXTENSION"/_layouts/15/onedrive.aspx`

if [ $RESPONSECODE == 403 ]; then
SYMBOL="[+] [403] ONEDRIVE EXISTS FOR "
elif [ $RESPONSECODE == 404 ]; then
SYMBOL="[-] [404] NOT FOUND "
else
SYMBOL="[?] [$RESPONSECODE] UNKNOWN RESPONSE "
fi

echo "$SYMBOL $line"
done < $USERLIST
