#!/usr/bin/env python

HELP = """
Run all of the scripts relevant to eagle in the correct order.
"""

import glob
import os
import platform
import distro
import sys

# Get all of the tricky packages out of the way
try:
    import sh
except:
    print("You need to install the sh module.")
    print("https://github.com/amoffat/sh")
    print("Try `pip install sh` or `pip3 install sh`")
    sys.exit(1)

try:
    from sh import eagle
except ImportError:
    # Try to find Eagle if we can
    print("You need to have eagle in your PATH, trying to find it...")
    if platform.system() == 'Darwin':
        versions = glob.glob('/Applications/EAGLE-*')
        if len(versions):
            versions.sort()
            latest = versions[-1]
            print('Using {}'.format(latest))
            path = os.path.join(latest, 'EAGLE.app', 'Contents', 'MacOS')
            os.environ['PATH'] += ':' + path

    try:
        from sh import eagle
    except ImportError:
        print("Could not find eagle automatically, need to add to PATH manually")
        print("Something like `export PATH=$PATH:~/eagle-6.5.0/bin`")
        sys.exit(1)

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


if platform.system() == 'Linux':
    distro = distro.linux_distribution()
    if distro[0] == 'Ubuntu' and float(distro[1]) > 18:
        print("")
        print("Heads up. If you're on Ubuntu 18+ and are missing pdftk,")
        print("you may need to install a special version of pdftk, here:")
        print("https://askubuntu.com/questions/1028522/how-can-i-install-pdftk-in-ubuntu-18-04-bionic")
        print("")


if platform.system() == 'Darwin':
    print("")
    print("Heads up. If you're on a mac and this script seems to hang during PDF")
    print("generation, you may need to install an updated version of pdftk, here:")
    print("  http://stackoverflow.com/questions/39750883/pdftk-hanging-on-macos-sierra")
    print("")


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

