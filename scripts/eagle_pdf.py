#!/usr/bin/env python
# -*- coding: utf-8 -*-

HELP = """
This script runs an eagle script to generate pdf documentation of a
PCB. It creates a pdf of the schematic and various layers to make a simple
reference for others to use.

Simply run this script in a folder containing a .sch and .brd file to
generate the pdfs.
"""
import sys, os, platform

# Get all of the tricky packages out of the way
try:
	from sh import rm
	from sh import mv
except:
	print("You need to install the sh module.")
	print("https://github.com/amoffat/sh")
	sys.exit(1)

try:
	from sh import pdftk
except:
	print("You need to install pdftk.")
	print("sudo apt-get install pdftk")
	sys.exit(1)

try:
	from sh import eagle
except:
	print("You need to have eagle in your path to generate the pdfs.")
	print("export PATH=$PATH:~/eagle-6.5.0/bin")
	sys.exit(1)

if platform.system().lower() == 'darwin':
	if os.path.exists('/Applications/wkhtmltopdf.app/Contents/MacOS/wkhtmltopdf'):
		include_bom = True
	else:
		print("If you want to include the bom you must have wkhtmltopdf installed.")
		print("Get it from here: https://code.google.com/p/wkhtmltopdf/downloads/detail?name=wkhtmltopdf.dmg")
		include_bom = False
else:
	try:
		from sh import unoconv
		include_bom = True
	except:
		print("If you want to include the bom you must have unoconv installed.")
		print("sudo apt-get install unoconv")
		include_bom = False


from glob import glob
import sh
from subprocess import call

# List of all of the pdfs that get generated
pdf_files = [('schematic', '~'),
             ('drawing', 'Top and Bottom Layers'),
             ('top_drawing', 'Top Layer'),
             ('bot_drawing', 'Bottom Layer'),
             ('top_copper', 'Top Copper Layer'),
             ('layer2_copper', 'Layer 2 Copper'),
             ('layer3_copper', 'Layer 3 Copper'),
             ('bot_copper', 'Bottom Copper Layer'),
             ('top_place', 'Top Paste Layer with Silkscreen'),
             ('bot_place', 'Bottom Paste Layer with Silkscreen'),
             ('drawing_1-1', 'Top and Bottom Layers 1:1 Scale'),
             ('top_copper_1-1', 'Top Layer 1:1 Scale'),
             ('layer2_copper_1-1', 'Layer 2 Copper 1:1 Scale'),
             ('layer3_copper_1-1', 'Layer 3 Copper 1:1 Scale'),
             ('bot_copper_1-1', 'Bottom Copper Layer 1:1 Scale')
            ]

# Default layer count
layer_count = 2

# Display the help if any arguments are provided.
if len(sys.argv) > 1:
	print(HELP)
	sys.exit(0)

# Determine the location of this script and the .scr file
here      = os.path.dirname(os.path.realpath(__file__))
pdfscr    = os.path.join(here, '..', 'scr', 'pdf.scr')
scr       = os.path.join(here, '..', 'scr', 'script.scr')
tmpscr    = os.path.join('/', 'tmp', 'script.scr')
numberpdf = os.path.join(here, 'number_pdf.sh')
titlepdf  = os.path.join(here, 'pdf_titles.py')

# Create script to run the pdf script
contents = ''
with open(scr, 'r') as f:
	contents = f.read()

contents = contents.replace('%SCRIPT_PATH%', pdfscr)

with open(tmpscr, 'w') as f:
	f.write(contents)

# Figure out the name of the schematic to run this on.
for sch in glob('*.sch'):
	sch_name, sch_ext = os.path.splitext(sch)

	# Delete the old pdfs if they exist
	for pdf in pdf_files + ['layer_test']:
		rm('-f', '{}_{}.pdf'.format(sch_name, pdf))

	# Delete the merged version
	rm ('-f', '{}.pdf'.format(sch))

	# Generate the pdfs
	eagle('-S', tmpscr, sch)

	# If a bom is present also convert it to pdf
	if include_bom:
		boms = glob('*bom*xls*')
		if len(boms) > 0:
			bom_tries = 3
			while bom_tries > 0:
				if platform.system().lower() == 'darwin':
					call(['/bin/rm', '-rf', 'osx_bom_to_pdf'])
					os.mkdir('osx_bom_to_pdf')
					call(['qlmanage','-o','osx_bom_to_pdf','-p',boms[0]])
					qldir = boms[0] + '.qlpreview'
					os.chdir("%s/%s" % ('osx_bom_to_pdf',qldir))
					call(['/Applications/wkhtmltopdf.app/Contents/MacOS/wkhtmltopdf',
						'Preview.html', '{}_bom.pdf'.format(sch_name)])
					mv('{}_bom.pdf'.format(sch_name), '../../')
					os.chdir('../..')
					call(['/bin/rm', '-rf', 'osx_bom_to_pdf'])
					break
				else:
					try:
						unoconv('-f', 'pdf', '-o', '{}_bom.pdf'.format(sch_name), boms[0])
						break
					except sh.ErrorReturnCode:
						print('Unable to convert bom on this go. Will try again \ because that seems to fix it.')
				bom_tries -= 1
				if bom_tries == 0:
					# Failed to convert bom. Exclude it
					print('Just could not convert bom. You\'ll have to go \ without it.')
					include_bom = False
		else:
			include_bom = False

	# Check if it is a four layer board by determining if the layer2 or layer3
	# pdf is bigger than the test pdf
	test_size = os.stat('{}_layer_test.pdf'.format(sch_name)).st_size
	layer2_size = os.stat('{}_layer2_copper.pdf'.format(sch_name)).st_size
	layer3_size = os.stat('{}_layer3_copper.pdf'.format(sch_name)).st_size
	if layer2_size > test_size or layer3_size > test_size:
		layer_count = 4

	# Combine them
	pdfs = []
	titles = []
	for pdf, title in pdf_files:
		if ('layer2' in pdf or 'layer3' in pdf) and layer_count == 2:
			continue
		pdfname = '{}_{}.pdf'.format(sch_name, pdf)
		if os.path.exists(pdfname):
			pdfinfo = pdftk(pdfname, 'dump_data')
			pdfinfol = pdfinfo.strip().split('\n')
			for line in pdfinfol:
				items = line.split(':')
				if len(items) == 2 and items[0] == 'NumberOfPages':
					numpages = int(items[1].strip())
					break
			titles += [title]*numpages
			pdfs.append(pdfname)
	if include_bom:
		pdfs.append('{}_bom.pdf'.format(sch_name))

	args = pdfs + ['cat', 'output', '{}.pdf'.format(sch_name)]
	pdftk(*args)

	# Delete the generated pdfs if they exist
	for pdf, title in pdf_files + [('layer_test', '~')]:
		try:
			rm('{}_{}.pdf'.format(sch_name, pdf))
		except sh.ErrorReturnCode_1:
			pass

	try:
		rm('-f', '{}_bom.pdf'.format(sch_name))
	except sh.ErrorReturnCode_1:
		pass

	# Add page numbers to the generated pdf
	os.system(numberpdf + ' {}.pdf'.format(sch_name))

	# Add titles to generated pdf
	os.system(titlepdf + ' {}_numbered.pdf "'.format(sch_name) + \
		'" "'.join(titles) + '"')

	rm('{}.pdf'.format(sch_name))
	rm('{}_numbered.pdf'.format(sch_name))
	mv('{}_numbered_titles.pdf'.format(sch_name), '{}.pdf'.format(sch_name))

# Delete doc_data.txt if it was created
rm('-f', 'doc_data.txt')

