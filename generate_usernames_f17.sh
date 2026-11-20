#!/bin/bash
# 2023.06.06 @nyxgeek
# quick and dirty username generation from census data
#
# Usage: ./generate_usernames_f17.sh firstnames.txt lastnames.txt
#
# Output goes to USERNAMES/tron_<pattern>/ as 175k-line chunks (xaaa, xaab, ...).
# The full set is large (~10GB) so make sure you have the disk space.
# Set SKIP_WAIT=1 to skip the 10 second abort window.

set -euo pipefail

CHUNK_LINES=175000

if [[ $# -lt 2 || ! -r $1 || ! -r $2 ]]; then
	echo "Usage: $0 <firstnames-file> <lastnames-file>" >&2
	exit 1
fi

echo "******************************************************************************************"
echo " HEY! THIS IS GOING TO TAKE UP LIKE 10GB of DISK SPACE!!!"
echo "******************************************************************************************"

if [[ -z ${SKIP_WAIT:-} ]]; then
	echo "(you still have time to CTRL-C for about 10 seconds)"
	sleep 10
fi
echo "Starting username generation..."

OUTROOT="USERNAMES"
WORKDIR=$(mktemp -d)
trap 'rm -rf "${WORKDIR}"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# Normalize inputs: strip CRs, trim surrounding whitespace, drop blank lines,
# de-duplicate (keeping order). The head-limited cross products therefore take
# the first N *unique* names.
clean() { tr -d '\r' < "$1" | awk '{gsub(/^[ \t]+|[ \t]+$/, "")} NF && !seen[$0]++'; }
clean "$1" > "${WORKDIR}/first.all"
clean "$2" > "${WORKDIR}/last.all"
for f in first.all last.all; do
	if [[ ! -s ${WORKDIR}/${f} ]]; then
		echo "Error: ${f%.all} names file has no usable lines" >&2
		exit 1
	fi
done

# gen <dirname> <awk args...>
# Runs awk and streams its output straight into split (no giant intermediate file).
# Any existing chunks in the target directory are removed first so re-runs are idempotent.
gen() {
	local name=$1; shift
	local dir="${OUTROOT}/tron_${name}"
	mkdir -p "${dir}"
	find "${dir}" -maxdepth 1 -type f \( -name 'x*' -o -name full.txt \) -delete
	awk "$@" | split -a 3 -l "${CHUNK_LINES}" - "${dir}/x"
}

# Prelude: L[0..25] = a..z
LETTERS='BEGIN{for(i=0;i<26;i++)L[i]=sprintf("%c",97+i)}'

# gen_letter <dirname> <input-file> <awk print expression using $0 and L[i]>
gen_letter() {
	local name=$1 file=$2 expr=$3
	echo "Generating ${name}"
	time gen "${name}" "${LETTERS} {for(i=0;i<26;i++) print ${expr}}" "${file}"
}

# gen_cross <dirname> <nfirst> <nlast> <awk print expression using f, m (and L[i] if letters=1)>
# first names are the outer loop, last names the inner loop.
gen_cross() {
	local name=$1 nfirst=$2 nlast=$3 expr=$4
	head -n "${nfirst}" "${WORKDIR}/first.all" > "${WORKDIR}/first.tmp"
	head -n "${nlast}" "${WORKDIR}/last.all" > "${WORKDIR}/last.tmp"
	echo "Generating ${name}"
	time gen "${name}" "${LETTERS}
		NR==FNR {l[++n]=\$0; next}
		{f=\$0; for(j=1;j<=n;j++){m=l[j]; ${expr}}}" "${WORKDIR}/last.tmp" "${WORKDIR}/first.tmp"
}

LAST="${WORKDIR}/last.all"
FIRST="${WORKDIR}/first.all"

# last name + letter patterns
gen_letter jsmith_c1990   "${LAST}" 'L[i] $0'
gen_letter j.smith_c1990  "${LAST}" 'L[i] "." $0'
gen_letter smithj_c1990   "${LAST}" '$0 L[i]'
gen_letter smith.j_c1990  "${LAST}" '$0 "." L[i]'

echo "Generating smithja Last/First/Middle"
time gen smithja_c1990 "${LETTERS} {for(i=0;i<26;i++) for(k=0;k<26;k++) print \$0 L[i] L[k]}" "${LAST}"

# first name + letter patterns
gen_letter johns_c1990   "${FIRST}" '$0 L[i]'
gen_letter john.s_c1990  "${FIRST}" '$0 "." L[i]'
gen_letter sjohn_c1990   "${FIRST}" 'L[i] $0'
gen_letter s.john_c1990  "${FIRST}" 'L[i] "." $0'

# first x last cross products (limited to ~10m lines each)
gen_cross john.smith_500x20k   500  20000 'print f "." m'
gen_cross john.smith_200x50k   200  50000 'print f "." m'
gen_cross john.smith_1kx10k    1000 10000 'print f "." m'
gen_cross johnsmith_1kx10k     1000 10000 'print f m'
gen_cross smith.john_1kx10k    1000 10000 'print m "." f'
gen_cross smithjohn_1kx10k     1000 10000 'print m f'

# john.j.smith: 300 first, 1750 last, all middle initials (~13.6m)
gen_cross john.j.smith_300x1750 300 1750 'for(i=0;i<26;i++) print f "." L[i] "." m'

# jjs: every three-letter combination
echo "Generating jjs"
time gen jjs_all 'BEGIN{for(i=97;i<=122;i++)for(j=97;j<=122;j++)for(k=97;k<=122;k++)printf "%c%c%c\n",i,j,k}'

echo "Done!"
