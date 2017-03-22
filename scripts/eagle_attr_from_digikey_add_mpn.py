#!/usr/bin/env python3

print("NOPE. DIDN'T FINISH THIS ONE. WANT TO GET BACK TO IT SOMEDAY.")
print("Really needs actual XML parsing, not regular expression hacks.")
print("Should check each <technology> node for <attribute />s and operate")
print("on that structure. I hope to come back to this someday. Sorry.")
sys.exit(1)

from bs4 import BeautifulSoup
import collections
import glob
import lxml.objectify
from pprint import pprint
import requests
import shutil
import sys
import tempfile
import termcolor
import time

print_attn = lambda x: termcolor.cprint(x, attrs=['bold'])
print_err = lambda x: termcolor.cprint(x, 'red', attrs=['bold'])

print("")
print("*** MAKE SURE YOU HAVE CLOSED THE EAGLE FILE BEFORE RUNNING THIS ***")
print("")

print("I also recommend doing this with clean git, because, I wrote this in")
print("an afternoon and make no promises. But it worked for me!")
print("")

schs = glob.glob('*.sch')

if len(schs) == 0:
    print("Could not find any Eagle schematic files.")
    sys.exit(1)
elif len(schs) > 1:
    print("Multiple sch's found.")
    print("Please type the full file name of the sch you want.")
    for f in schs:
        print(" - " + f)
    sch = input("sch file: ")
else:
    sch = schs[0]

print("> Using {} as schematic".format(sch))
with open(sch) as s:
    schematic = lxml.objectify.parse(s)

print(schematic)
sys.exit()

brd = sch[:-4] + '.brd'

try:
    with open(brd) as b:
        board = b.readlines()
    print("> Using {} as board".format(brd))
except IOError:
    print("")
    print("WARN: No matching .brd file")
    r = input("      Continue without updating a board? [y/N] ").upper()
    if not( len(r) and r[0] == 'Y' ):
        sys.exit()
    board = None
    print("")


# Grab all of the attributes
attr_digikey_re = re.compile('<attribute name="DIGIKEY" value="([^"]*)".*[/]?>')
digikey_part_nos = dict()
for line in schematic:
    result = attr_digikey_re.match(line)
    if result is not None:
        digikey_part_no = result.groups()[0]
        digikey_part_nos[digikey_part_no] = None

# Check if the board has any other ones
if board:
    for line in board:
        result = attr_digikey_re.match(line)
        if result is not None:
            digikey_part_no = result.groups()[0]
            if digikey_part_no not in digikey_part_nos:
                print("WARN: Attribute {} in .brd file but not in .sch?".format(digikey_part_no))


# DigiKey Search API: https://api-portal.digikey.com/node/1364
# Lies. That requires OAuth. Too hard. Soup it.
def digikey_part_to_mfn(part_number):
    DIGIKEY_SEARCH   = 'http://search.digikey.com/scripts/DkSearch/dksus.dll?Detail&name={}'

    part_number  = part_number.replace('+', '%2B')
    url          = DIGIKEY_SEARCH.format(part_number)
    digikey_html = requests.get(url).text
    try:
        soup         = BeautifulSoup(digikey_html, "html.parser")
        mpn_th       = soup(text="Manufacturer Part Number")[0]
        mpn_th_tag   = mpn_th.parent
        mpn_td_tag   = mpn_th_tag.findNext('td')
        mpn_h1_tag   = mpn_td_tag.findNext('h1')
    except:
        #print(digikey_html)
        #print("-" * 80)
        #print(url)
        #print("-" * 80)
        #print("Sigh.. perhaps DigiKey has changed. Check out the HTML see what's wrong")
        #raise
        print("WARN: The attribute {} is not a valid DigiKey part number".format(part_number))
        return None
    return mpn_h1_tag.get_text().strip()


# Look up Manufacturer Part Numbers from DigiKey
for part in digikey_part_nos:
    sys.stdout.write('Lookup {}\r'.format(part))
    digikey_part_nos[part] = digikey_part_to_mfn(part)


print("")
if len(digikey_part_nos) == 0:
    print('No parts with DIGIKEY attributes found. Exiting.')
    sys.exit(1);

print("This script will add the following attributes:")
for digikey,mpn in digikey_part_nos.items():
    print_attn("{:20} => {:20}".format("DIGIKEY", "MPN"))
    print     ("{:20} => {:20}".format(digikey, mpn))

r = input("Write new attributes to eagle files? [Y/n] ").upper()
if len(r) and r[0] == 'N':
  sys.exit()

# Update schematic and board. Do everything in memory before touching files on disk
new_sch = tempfile.TemporaryFile()
for line in schematic:
   try:
      result = sch_part_tag_re.match(line)
      if result is not None:
         number, value, unit_prefix, suffix = result.groups()
         if int(number) >= 1000:
            if ignore_high_parts:
               continue
         old_name = prefix + number
         old_value = value + unit_prefix + suffix
         line = line.replace("name=\"" + old_name, "name=\"" + rename[old_name]['new_name'], 1)
         line = line.replace("value=\"" + old_value,"value=\"" + rename[old_name]['new_value'], 1)
         continue
      result = sch_instance_tag_re.match(line)
      if result is not None:
         number, = result.groups()
         if int(number) >= 1000:
            if ignore_high_parts:
               continue
         old_name = prefix + number
         line = line.replace(old_name, rename[old_name]['new_name'], 1)
         continue
      result = sch_pinref_tag_re.match(line)
      if result is not None:
         number, = result.groups()
         if int(number) >= 1000:
            if ignore_high_parts:
               continue
         old_name = prefix + number
         line = line.replace(old_name, rename[old_name]['new_name'], 1)
         continue
      result = sch_part_tag_novalue_re.match(line)
      if result is not None:
         number, deviceset = result.groups()
         if int(number) >= 1000 and ignore_high_parts:
            continue
         old_name = prefix + number
         line = line.replace(old_name, rename[old_name]['new_name'], 1)
         continue
   finally:
      new_sch.write(line.encode('utf-8'))

if board:
   new_brd = tempfile.TemporaryFile()
   for line in board:
      try:
         result = brd_element_tag_re.match(line)
         if result is not None:
            number, value, unit_prefix, suffix = result.groups()
            if int(number) >= 1000:
               if ignore_high_parts:
                  continue
            old_name = prefix + number
            old_value = value + unit_prefix + suffix
            line = line.replace("name=\"" + old_name, "name=\"" + rename[old_name]['new_name'], 1)
            line = line.replace("value=\"" + old_value, "value=\"" + rename[old_name]['new_value'], 1)
            continue
         result = brd_contactref_tag_re.match(line)
         if result is not None:
            number, = result.groups()
            if int(number) >= 1000:
               if ignore_high_parts:
                  continue
            old_name = prefix + number
            line = line.replace(old_name, rename[old_name]['new_name'], 1)
            continue
         result = brd_element_tag_othervalue_re.match(line)
         if result is not None:
            number, value = result.groups()
            if int(number) >= 1000:
               if ignore_high_parts:
                  continue
            old_name = prefix + number
            line = line.replace(old_name, rename[old_name]['new_name'], 1)
            continue
      finally:
         new_brd.write(line.encode('utf-8'))

new_sch.seek(0)
shutil.copyfileobj(new_sch, open(sch, 'wb'))
if board:
   new_brd.seek(0)
   shutil.copyfileobj(new_brd, open(brd, 'wb'))

