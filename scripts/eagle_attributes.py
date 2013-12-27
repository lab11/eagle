#!/usr/bin/env python
# -*- coding: utf-8 -*-

HELP = """
This script runs an eagle ULP to get the global attributes for a board.
"""

import sys
# Get all of the tricky packages out of the way
try:
	import sh
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

from glob import glob
import os
import sys
import sh

# Display the help if any arguments are provided.
if len(sys.argv) > 1:
	print(HELP)
	sys.exit(0)

# Determine the location of this script and the .ulp file
here = os.path.dirname(os.path.realpath(__file__))
ulp = os.path.join(here, '..', 'ulp', 'attributes.ulp')
scr = os.path.join(here, '..', 'scr', 'ulp-sch.scr')
tmpscr = os.path.join('/', 'tmp', 'ulp.scr')

contents = ''
with open(scr, 'r') as f:
	contents = f.read()

contents = contents.replace('%ULP_PATH%', ulp)

with open(tmpscr, 'w') as f:
	f.write(contents)

# Figure out the name of the schematic to run this on.
for sch in glob('*.sch'):
	# Attributes to .info file
	eagle('-S', tmpscr, sch)
