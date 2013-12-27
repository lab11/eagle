#!/usr/bin/env python
# -*- coding: utf-8 -*-

HELP = """
This script runs an eagle script to generate a png of the PCB.

Simply run this script in a folder containing a .sch and .brd file to
generate the png.
"""
import sys

# Get all of the tricky packages out of the way
try:
	from sh import rm
	from sh import mv
	from sh import mktemp
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

# Determine the location of this script and the .scr file
here      = os.path.dirname(os.path.realpath(__file__))
pngscr    = os.path.join(here, '..', 'scr', 'png.scr')
scr       = os.path.join(here, '..', 'scr', 'script.scr')
tmpscr    = os.path.join('/tmp', str(mktemp('scrXXXX')).strip())

# Create script to run the pdf script
contents = ''
with open(scr, 'r') as f:
	contents = f.read()

contents = contents.replace('%SCRIPT_PATH%', pngscr)


# Figure out the name of the schematic to run this on.
for sch in glob('*.sch'):
	sch_name, sch_ext = os.path.splitext(sch)

	rm('-f', '{}_pcb.png'.format(sch_name))

	contents_now = contents.replace('%N', sch_name)
	print(contents_now)
	with open(tmpscr, 'w') as f:
		f.write(contents_now)
	
	# Generate the png
	eagle('-S', tmpscr, sch)

rm('-f', tmpscr)

