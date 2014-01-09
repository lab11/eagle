#!/usr/bin/env python
# -*- coding: utf-8 -*-

HELP = """
This script runs an eagle ULP to get the global attributes for a board.
"""

import sys
# Get all of the tricky packages out of the way
try:
	import sh
	from sh import mktemp
	from sh import rm
except:
	print("You need to install the sh module.")
	print("https://github.com/amoffat/sh")
	sys.exit(1)

try:
	from sh import eagle
except:
	print("You need to have eagle in your path to generate the pdfs.")
	print("export PATH=$PATH:~/eagle-6.5.0/bin")
	sys.exit(1)

import glob
import os

def read_in_info (filename, d):
	with open(filename) as f:
		for line in f:
			if len(line.strip()) == 0:
				continue
			opts = line.split(':', 1)
			d[opts[0].strip().lower()] = opts[1].strip()

# Display the help if any arguments are provided.
if len(sys.argv) > 1:
	print(HELP)
	sys.exit(0)

# Determine the location of this script and the .ulp file
here   = os.path.dirname(os.path.realpath(__file__))
ulp    = os.path.join(here, '..', 'ulp', 'attributes.ulp')
scr    = os.path.join(here, '..', 'scr', 'ulp-sch.scr')
tmpscr = str(mktemp(os.path.join('/', 'tmp', 'ulp.scrXXXXXXXXXX'))).strip()

contents = ''
with open(scr, 'r') as f:
	contents = f.read()

contents = contents.replace('%ULP_PATH%', ulp)

with open(tmpscr, 'w') as f:
	f.write(contents)

# Figure out the name of the schematic to run this on.
for sch in glob.glob('*.sch'):
	attrs = {}

	sch_name = sch[:-4]

	# Read in the old .info file to save the original values
	if os.path.exists(sch_name + '.info'):
		read_in_info(sch_name + '.info', attrs)

	# Generate a new .info file in case anything changed
	eagle('-S', tmpscr, sch)

	# Read the new .info file in to update any changed values
	read_in_info(sch_name + '.info', attrs)

	# Write out the key values
	with open(sch_name + '.info', 'w') as f:
		for k,v in attrs.items():
			f.write('{}: {}\n'.format(k, v))


rm(tmpscr)
