#!/usr/bin/env python

about = """
Script to automatically zip up the proper gerber files for shipping
to a board company. This script recommends this folder hierarchy:

   - eagle/hardware/cad folder
     - <project board name>
       - rev_<revision>
         - <actual gerber files>

but will try its best to figure out your project name and revision.

This script works with the sunstone CAM process and the other one in Eagle.
"""

import argparse
import datetime
import glob
import os
import sys
try:
	from sh import rm
	import sh
except:
	print('You need to install the sh module.')
	print('sudo pip install sh')
	sys.exit(1)

revision     = ''
project_name = ''
project_date = ''

fab_extensions = ['bot', 'bsk', 'drd','0102','0116','1516','0216','0215','0115', 'oln', 'slk', 'smb', 'smt', 'top',
                  'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7', 'L8', 'L9', 'L10',
                  'GBL', 'GBO', 'GBS', 'GTL', 'GTO', 'GTS', 'TXT', 'DIM', 'mil',
                  'gbs', 'gts']
assembler_extensions = ['bps', 'tps', 'tsp', 'bsp', 'centroid', 'pdf']
stencil_extensions = ['tsp', 'bsp', 'oln', 'DIM', 'mil']
# Files to add if they exist
fab_add_files = ['fabnotes.txt']

fab_files = []
assem_files = []
stencil_files = []

schematic  = ''

# Process all of the command line arguments
project_date = datetime.date.today().strftime('%Y-%m-%d')
argp = argparse.ArgumentParser(description=about)
argp.add_argument('--date',
	default=project_date,
	help='Specify a date other than today\'s')
args = argp.parse_args()
project_date = args.date

# find the schematic filename
files = os.listdir('.')
for f in files:
	fname, fext = os.path.splitext(f)
	if fext[1:] == 'sch':
		schematic = fname
		break

# figure out the proper filename
folder_str = os.getcwd()
folders = folder_str.split(os.sep)

# get revision
if folders[-1][0:4] == 'rev_':
	revs = folders[-1].split('_')
	revision = revs[-1]
else:
	try:
		# not in a rev_X folder, see if it is in a filename
		if 'rev' in schematic:
			# get only letters or numbers after the word rev
			remainder = schematic.rsplit('rev', 1)[1]
			revision  = filter(str.isalnum, remainder)
		else:
			# get only the letters after the last _ in the filename
			remainder = schematic.rsplit('_', 1)[1]
			revision  = filter(str.isalnum, remainder)
	except:
		revision = ''

if len(revision) > 1 or revision == '':
	revision = raw_input('Could not find revision. \
Please enter revision value: ')

# get project name
if 'rev' == folders[-1][0:3]:
	# offset for a revision folder
	folder_index = -2
else:
	# use the immediate predecessor
	folder_index = -1

if folders[folder_index] in ['eagle', 'hardware', 'cad']:
	# use the project name in the projects directory
	for i,f in zip(folders, range(0,len(folders))):
		if f == 'projects':
			project_name = folders[i+1]
			break
	# check if no projects dir
	if project_name == '':
		# use the folder name of whatever the eagle folder is in
		project_name = folders[folder_index-1]

else:
	# files are not in an eagle directory, use whatever folder they are in
	project_name = folders[folder_index]


# get the gerbers that need to be added
files = os.listdir('.')
for f in files:
	fname, fext = os.path.splitext(f)
	if fext[1:] in fab_extensions:
		fab_files.append(f)
		assem_files.append(f)
	if fext[1:] in assembler_extensions:
		assem_files.append(f)
	if fext[1:] in stencil_extensions:
		stencil_files.append(f)
	if os.path.basename(f) in fab_add_files:
		fab_files.append(f)
		assem_files.append(f)

# Add any bom files to the assembler zip
boms = glob.glob('*bom*')
assem_files += boms

fab_filename = '{0}_{1}_to_fab_{2}'.format(project_name, revision, project_date)
assem_filename = '{0}_{1}_to_assembler_{2}'.format(project_name, revision,
	project_date)
stencil_filename = '{0}_{1}_to_stencil_{2}'.format(project_name, revision,
	project_date)

print('Project name:    {}'.format(project_name))
print('Revision:        {}'.format(revision))
print('Date:            {}'.format(project_date))
print('Fab files:       {}'.format(' '.join(fab_files)))
print('Assembler files: {}'.format(' '.join(assem_files)))
print('Stencil files:   {}'.format(' '.join(stencil_files)))

if len(fab_files) == 0:
	print('Nothing to do!')
	print('Maybe you should run the cam job')
	sys.exit(1)

rm('-f', fab_filename)
rm('-f', assem_filename)
rm('-f', stencil_filename)
sh.zip(fab_filename, fab_files)
sh.zip(assem_filename, assem_files)
sh.zip(stencil_filename, stencil_files)
