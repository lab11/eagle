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
here   = os.path.dirname(os.path.realpath(__file__))
pngscr = os.path.join(here, '..', 'scr', 'png.scr')
scr    = os.path.join(here, '..', 'scr', 'script.scr')
tmppng = os.path.join(str(mktemp('/tmp/pngXXXXXXXXXX')).strip() + '.scr')
tmpscr = os.path.join(str(mktemp('/tmp/scrXXXXXXXXXX')).strip() + '.scr')

# Get the text from the png script file so that we can replace the 
# schematic name later.
pngscr_contents = ''
with open(pngscr, 'r') as f:
	pngscr_contents = f.read()

# Create script to run the pdf script
contents = ''
with open(scr, 'r') as f:
	contents = f.read()
contents = contents.replace('%SCRIPT_PATH%', tmppng)
with open(tmpscr, 'w') as f:
	f.write(contents)

# Figure out the name of the schematic to run this on.
for sch in glob('*.sch'):
	sch_name, sch_ext = os.path.splitext(sch)

	png_name = '{}_pcb.png'.format(sch_name)
	rm('-f', png_name)

	pngscr_contents = pngscr_contents.replace('%N', sch_name)
	with open(tmppng, 'w') as f:
		f.write(pngscr_contents)
	
	# Generate the png
	eagle('-S', tmpscr, sch)

	# Trip whitespace
	sh.convert(png_name, '-trim', png_name)

rm('-f', tmpscr)
rm('-f', tmppng)

