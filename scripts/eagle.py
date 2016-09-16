#!/usr/bin/env python

HELP = """
Run all of the scripts relevant to eagle in the correct order.
"""

import os
import sys

#           filename               arguments
scripts = [('eagle_centroid.py',   False),
           ('bom_to_text.py',      False),
           ('eagle_pdf.py',        False),
           ('eagle_png.py',        False),
           ('eagle_attributes.py', False),
           ('eagle_tofab_zip.py',  True),
           ('board_bundle.py',     True)
          ]

here = os.path.dirname(os.path.realpath(__file__))

for s, args in scripts:
	print("Running {}...".format(s))

	path = os.path.join(here, s)
	if args:
		cmd = '{} {}'.format(path, ' '.join(sys.argv[1:]))
	else:
		cmd = path

	ret = os.system(cmd)
	if ret != 0:
		print("Error running scripts")
		sys.exit(1)

