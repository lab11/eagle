#!/usr/bin/env python

"""
Adds titles to each page of a pdf.

Use ~ for a blank title.
"""

import sys

try:
	import sh
	from sh import mv
	from sh import rm
except ImportError:
	print('You need the sh module.')
	print('sudo pip install sh')
	sys.exit(1)
try:
	from sh import pdflatex
except ImportError:
	print('Requires pdflatex')
	sys.exit(1)
try:
	from sh import pdftk
except ImportError:
	print('Requires pdftk')
	sys.exit(1)

import glob
import os
import tempfile

usage = '{} <inputfile.pdf> <title1> <title2> <titlex...>'

tdir = tempfile.mkdtemp()

TITLES_TEX = os.path.join(tdir, 'pdftitles.tex')
TITLES_PDF = os.path.join(tdir, 'pdftitles.pdf')
TITLES_BURST = os.path.join(tdir, 'pdftitles_b_%04d.pdf')
TITLES_GLOB = os.path.join(tdir, 'pdftitles_b_{}.pdf')

INPUT_BURST = os.path.join(tdir, 'input_b_%04d.pdf')
INPUT_GLOB = os.path.join(tdir, 'input_b_*.pdf')

MERGED_GLOB = os.path.join(tdir, 'merged_{}.pdf')
MERGED_PDF = os.path.join(tdir, 'merged.pdf')

latex_header = """
\\documentclass{article}
\\usepackage[margin=1cm,pdftex]{geometry}
\\pagestyle{plain}
\\renewcommand{\\familydefault}{\\sfdefault}
\\pagenumbering{gobble}
\\begin{document}
\\center """
latex_footer = """
\\end{document}
"""

if len(sys.argv) < 3:
	print(usage)
	sys.exit(1)

input_file = sys.argv[1]
output_file = input_file[:-4] + '_titles' + '.pdf'

# Get a list of all the titles
# Make sure that there are at least as many titles as input pages
titles = sys.argv[2:]

pdfinfo = pdftk(input_file, 'dump_data')
pdfinfol = pdfinfo.strip().split('\n')
for line in pdfinfol:
	items = line.split(':')
	if len(items) == 2 and items[0] == 'NumberOfPages':
		numpages = int(items[1].strip())
		break

while numpages > len(titles):
	titles.append('~')

# Combine the headers and create a .tex file with the headers
latex_titles = ' \\newpage\n'.join(titles)

latex_out = latex_header + latex_titles + latex_footer

with open(TITLES_TEX, 'w') as f:
	f.write(latex_out)

# Create pdf
pdflatex('-output-directory={}'.format(tdir), TITLES_TEX)

# Split title pdf into pages
pdftk(TITLES_PDF, 'burst', 'output', TITLES_BURST)

# Split the input file into pages
pdftk(input_file, 'burst', 'output', INPUT_BURST)

# Merge
inputs = glob.glob(INPUT_GLOB)
for inputf in inputs:
	num = inputf[-8:-4]

	#pdftk(TITLES_GLOB.format(num), 'background', inputf, 'output',
	#	MERGED_GLOB.format(num))
	pdftk(inputf, 'background', TITLES_GLOB.format(num), 'output',
		MERGED_GLOB.format(num))

# Combine
merged_files = sorted(glob.glob(MERGED_GLOB.format('*')))
args = merged_files + ['cat', 'output', MERGED_PDF]
pdftk(args)

# Move to output file
mv(MERGED_PDF, output_file)

# Delete temp folder
rm('-rf', tdir)

