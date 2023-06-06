#!/bin/bash
# 2023.06.06 @nyxgeek
# quick and dirty username generation from census data
#
# this will use approx 10GB of space and might take hours. HOURS. I tried to add output along the way.
# Good luck.

echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE A LONG LONG TIME, AND WILL TAKE UP LIKE 10GB of DISK SPACE!!! "
echo "******************************************************************************************"
echo ""
echo "(you still have time to CTRL-C for about 10 seconds)"
sleep 10
echo "Starting username generation..."


FIRSTNAMES=$1
LASTNAMES=$2

CURRENTDIR=`pwd`


#generate jsmith
echo "Generating jsmith"
TMPPATH="USERNAMES/tron_jsmith_c1990"
mkdir ${TMPPATH}
time while read LASTNAME; do for letter in {a..z}; do echo "${letter}${LASTNAME}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}

#generate j.smith
echo "Generating j.smith"
TMPPATH="USERNAMES/tron_j.smith_c1990"
mkdir ${TMPPATH} 2>/dev/null
time while read LASTNAME; do for letter in {a..z}; do echo "${letter}.${LASTNAME}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate smithj
echo "Generating smithj"
TMPPATH="USERNAMES/tron_smithj_c1990"
mkdir ${TMPPATH} 2>/dev/null
time while read LASTNAME; do for letter in {a..z}; do echo "${LASTNAME}${letter}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate smith.j
echo "Generating smith.j"
TMPPATH="USERNAMES/tron_smith.j_c1990"
mkdir ${TMPPATH}
time while read LASTNAME; do for letter in {a..z}; do echo "${LASTNAME}.${letter}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate johns
echo "Generating johns"
TMPPATH="USERNAMES/tron_johns_c1990"
mkdir ${TMPPATH} 2>/dev/null
time while read FIRSTNAME; do for letter in {a..z}; do echo "${FIRSTNAME}${letter}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate john.s
echo "Generating johns"
TMPPATH="USERNAMES/tron_john.s_c1990"
mkdir ${TMPPATH} 2>/dev/null
time while read FIRSTNAME; do for letter in {a..z}; do echo "${FIRSTNAME}.${letter}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate sjohn
echo "Generating sjohn"
TMPPATH="USERNAMES/tron_sjohn_c1990"
mkdir ${TMPPATH} 2>/dev/null
time while read FIRSTNAME; do for letter in {a..z}; do echo "${letter}${FIRSTNAME}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate s.john
echo "Generating s.john"
TMPPATH="USERNAMES/tron_s.john_c1990"
mkdir ${TMPPATH} 2>/dev/null
time while read FIRSTNAME; do for letter in {a..z}; do echo "${letter}.${FIRSTNAME}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate john.smith variations
echo "Generating john.smith variations. This is gonna take FOREVER. Limiting total to 10m lines per variation."

## VARIATION 1: 500 first names, 20k last names

TMPPATH="USERNAMES/tron_john.smith_500x20k" 
mkdir ${TMPPATH} 2>/dev/null

TMPFIRSTNAME="/tmp/first.tmp"
TMPLASTNAME="/tmp/last.tmp"

cat "$1" | head -n 500 > ${TMPFIRSTNAME}
cat "$2" | head -n 20000 > ${TMPLASTNAME}

time while read FIRSTNAME; do while read LASTNAME; do echo "${FIRSTNAME}.${LASTNAME}" >> ${TMPPATH}/full.txt; done< ${TMPFIRSTNAME}; done <  ${TMPLASTNAME}
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}

## VARIATION 2: 200 first names, 50k last names

TMPPATH="USERNAMES/tron_john.smith_200x50k"
mkdir ${TMPPATH} 2>/dev/null

TMPFIRSTNAME="/tmp/first.tmp"
TMPLASTNAME="/tmp/last.tmp"

cat "$1" | head -n 200 > ${TMPFIRSTNAME}
cat "$2" | head -n 50000 > ${TMPLASTNAME}

time while read FIRSTNAME; do while read LASTNAME; do echo "${FIRSTNAME}.${LASTNAME}" >> ${TMPPATH}/full.txt; done< ${TMPFIRSTNAME}; done <  ${TMPLASTNAME}
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}



## VARIATION 3: 1000 first names, 10k last names

TMPPATH="USERNAMES/tron_john.smith_1kx10k"
mkdir ${TMPPATH} 2>/dev/null

TMPFIRSTNAME="/tmp/first.tmp"
TMPLASTNAME="/tmp/last.tmp"

cat "$1" | head -n 1000 > ${TMPFIRSTNAME}
cat "$2" | head -n 10000 > ${TMPLASTNAME}

time while read FIRSTNAME; do while read LASTNAME; do echo "${FIRSTNAME}.${LASTNAME}" >> ${TMPPATH}/full.txt; done< ${TMPFIRSTNAME}; done <  ${TMPLASTNAME}
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}




#generate johnsmith variations
echo "Generating johnsmith variations. This is gonna take FOREVER. Limiting total to 10m lines per variation."


## VARIATION 1: 1k first names, 10k last names

TMPPATH="USERNAMES/tron_johnsmith_1kx10k"
mkdir ${TMPPATH} 2>/dev/null

TMPFIRSTNAME="/tmp/first.tmp"
TMPLASTNAME="/tmp/last.tmp"

cat "$1" | head -n 1000 > ${TMPFIRSTNAME}
cat "$2" | head -n 10000 > ${TMPLASTNAME}

time while read FIRSTNAME; do while read LASTNAME; do echo "${FIRSTNAME}${LASTNAME}" >> ${TMPPATH}/full.txt; done< ${TMPFIRSTNAME}; done <  ${TMPLASTNAME}
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}



#generate smith.john variations
echo "Generating smith.john variations. This is gonna take FOREVER. Limiting total to 10m lines per variation."


## VARIATION 1: 1k first names, 10k last names

TMPPATH="USERNAMES/tron_smith.john_1kx10k"
mkdir ${TMPPATH} 2>/dev/null

TMPFIRSTNAME="/tmp/first.tmp"
TMPLASTNAME="/tmp/last.tmp"

cat "$1" | head -n 1000 > ${TMPFIRSTNAME}
cat "$2" | head -n 10000 > ${TMPLASTNAME}

time while read FIRSTNAME; do while read LASTNAME; do echo "${LASTNAME}.${FIRSTNAME}" >> ${TMPPATH}/full.txt; done< ${TMPFIRSTNAME}; done <  ${TMPLASTNAME}
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}



#generate smithjohn variations
echo "Generating smithjohn variations. This is gonna take FOREVER. Limiting total to 10m lines per variation."

## VARIATION 1: 1k first names, 10k last names

TMPPATH="USERNAMES/tron_smithjohn_1kx10k"
mkdir ${TMPPATH} 2>/dev/null

TMPFIRSTNAME="/tmp/first.tmp"
TMPLASTNAME="/tmp/last.tmp"

cat "$1" | head -n 1000 > ${TMPFIRSTNAME}
cat "$2" | head -n 10000 > ${TMPLASTNAME}

time while read FIRSTNAME; do while read LASTNAME; do echo "${LASTNAME}${FIRSTNAME}" >> ${TMPPATH}/full.txt; done< ${TMPFIRSTNAME}; done <  ${TMPLASTNAME}
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate john.j.smith
echo "Generating john.j.smith variations. This is gonna take FOREVER. Limiting total to 10m lines per variation."

# VARIATION 1: 300 first, 750 last, all middle initials - 13m approx
TMPPATH="USERNAMES/tron_john.j.smith_300x1750"
mkdir ${TMPPATH} 2>/dev/null

TMPFIRSTNAME="/tmp/first.tmp"
TMPLASTNAME="/tmp/last.tmp"

cat "$1" | head -n 300 > ${TMPFIRSTNAME}
cat "$2" | head -n 1750 > ${TMPLASTNAME}

time while read FIRSTNAME; do while read LASTNAME; do for letter in {a..z}; do  echo "${FIRSTNAME}.${letter}.${LASTNAME}" >> ${TMPPATH}/full.txt;done; done< ${TMPFIRSTNAME}; done <  ${TMPLASTNAME}
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}


#generate jjs
TMPPATH="USERNAMES/tron_jjs_all"
mkdir ${TMPPATH} 2>/dev/null
for letter1 in {a..z}; do for letter2 in {a..z}; do for letter3 in {a..z}; do echo "${letter1}${letter2}${letter3}" >> ${TMPPATH}/full.txt; done; done < $2
cd ${TMPPATH}
split -l 175000 full.txt
rm full.txt
cd ${CURRENTDIR}

echo "Done!"
