#!/usr/bin/env python

import argparse
import datetime
import glob
import os
import sys

from sh import mkdir
from sh import rm
from sh import unzip
from sh import ls
from sh import cp
import sh

about = """
Bundle all of the created eagle output to a zip that could be posted on the web.
"""

FAB_FOLDER = 'to_fab'
ASSEM_FOLDER = 'to_assembler'
IMAGE_FOLDER = 'images'

project_date = datetime.date.today().strftime("%Y-%m-%d")

# Process all of the command line arguments
argp = argparse.ArgumentParser(description=about)
argp.add_argument('--date',
	default=project_date,
	help='Specify a date other than today\'s')
args = argp.parse_args()

# Check for folders we want to create
folders = [FAB_FOLDER, ASSEM_FOLDER, IMAGE_FOLDER]
for folder in folders:
	if os.path.isdir(folder):
		print('"{}" directory exists. Please remove before continuing.'.
			format(folder))
		sys.exit(1)

# Check for the zip files we need
fab_zip = glob.glob('*to_fab_{}.zip'.format(args.date))[0]
assem_zip = glob.glob('*to_assembler_{}.zip'.format(args.date))[0]

if not fab_zip:
	print('No to_fab .zip file found. Maybe you should run eagle.py.')
	sys.exit(1)

if not assem_zip:
	print('No to_assembler .zip file found. Maybe you should run eagle.py.')
	sys.exit(1)

# Check for brd and sch files
schs = glob.glob('*.sch')
brds = glob.glob('*.brd')

bases = []
for s in schs:
	bases.append(s[0:-4])

# Get the pdfs of the board
pdfs = []
for b in bases:
	pdfs += glob.glob('{}.pdf'.format(b))

# Get any dxf files
dxfs = []
dxfs += glob.glob('*.dxf')

# Get the info files if they exist
infos = []
for b in bases:
	info_file = '{}.info'.format(b)
	if os.path.exists(info_file):
		infos.append(info_file)

# Get all images
jpgs = glob.glob('*.jpg')
jpgs.extend(glob.glob('*.png'))

# Find the bom
boms = glob.glob('*_bom.xls*')
converted_boms = []
for b in boms:
	base = os.path.splitext(b)[0]
	csv = '{}.csv'.format(base)
	txt = '{}.txt'.format(base)
	if os.path.exists(csv):
		converted_boms.append(csv)
	if os.path.exists(txt):
		converted_boms.append(txt)
boms += converted_boms

# Get the output file name
output_name = fab_zip.split('_to_fab')[0] + '_{}.zip'.format(args.date)

# Actually make the zip

# Generate the folders we use to organize things
mkdir(FAB_FOLDER)
mkdir(ASSEM_FOLDER)
mkdir(IMAGE_FOLDER)

# Put the contents of the zip files in the folders
# This way we don't have to replicate that logic
unzip(fab_zip, '-d', FAB_FOLDER)
unzip(assem_zip, '-d', ASSEM_FOLDER)

# Put the images in the images folder
for jpg in jpgs:
	cp(jpg, IMAGE_FOLDER)

# Get the filenames for fab
fab_files = glob.glob('{}/*'.format(FAB_FOLDER))
assem_files = glob.glob('{}/*'.format(ASSEM_FOLDER))
image_files = glob.glob('{}/*'.format(IMAGE_FOLDER))

combined =  [output_name] + schs + brds + pdfs + dxfs + infos + boms + \
                            fab_files + assem_files + image_files

sh.zip(*combined)

rm('-rf', FAB_FOLDER)
rm('-rf', ASSEM_FOLDER)
rm('-rf', IMAGE_FOLDER)
