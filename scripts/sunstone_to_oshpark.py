#!/usr/bin/env python3

'''
Copy Sunstone gerbers output for OSH Park
'''

import os
import sys

try:
	from sh import cp
	import sh
except:
	print('Need sh module')
	print('sudo pip3 install sh')
	sys.exit(1)

def query_yes_no(question, default="yes"):
	"""Ask a yes/no question via input() and return their answer.

	"question" is a string that is presented to the user.
	"default" is the presumed answer if the user just hits <Enter>.
		It must be "yes" (the default), "no" or None (meaning
		an answer is required of the user).

	The "answer" return value is True for "yes" or False for "no".
	"""
	valid = {"yes": True, "y": True, "ye": True,
			 "no": False, "n": False}
	if default is None:
		prompt = " [y/n] "
	elif default == "yes":
		prompt = " [Y/n] "
	elif default == "no":
		prompt = " [y/N] "
	else:
		raise ValueError("invalid default answer: '%s'" % default)

	while True:
		sys.stdout.write(question + prompt)
		choice = input().lower()
		if default is not None and choice == '':
			return valid[default]
		elif choice in valid:
			return valid[choice]
		else:
			sys.stdout.write("Please respond with 'yes' or 'no' "
							 "(or 'y' or 'n').\n")

extensions = {
	'top': 'GTL',
	'bot': 'GBL',
	'smt': 'GTS',
	'smb': 'GBS',
	'slk': 'GTO',
	'bsk': 'GBO',
	'oln': 'GKO',
	'L1':  'GTL',
	'L2':  'G2L',
	'L3':  'G3L',
	'L4':  'GBL',
	'drd': 'XLN'
}

print('Looking for gerber files created by Sunstone CAM')

new_files = []
for f in os.listdir('.'):
	fname, ext = os.path.splitext(f)

	if ext[1:] in extensions:
		new_name = '{}_oshpark.{}'.format(fname, extensions[ext[1:]])
		new_files.append(new_name)
		cp(f, new_name)

make_zip = query_yes_no('Would you like to create a ZIP of the OSH Park Gerbers')

if make_zip and len(new_files) > 0:
	sh.zip('osh_park_gerbers.zip', *new_files)

