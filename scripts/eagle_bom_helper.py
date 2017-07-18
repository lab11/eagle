#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Python Built-ins
import collections
import glob
import json
import os
import pickle
from pprint import pprint
import re
import shutil
import sys
import tempfile
import time
import urllib.request, urllib.parse, urllib.error

# Third Party Libraries (i.e. need pip install)
import bidict
import dataprint
import icdiff
import Swoop
import termcolor

sch_file = glob.glob('*.sch')[0]
brd_file = glob.glob('*.brd')[0]

brd = Swoop.EagleFile.from_file(brd_file)
sch = Swoop.EagleFile.from_file(sch_file)


##############################################################################
## Part database

# Every API for this rate limits to a few requests / second at most, so we
# build up a local cache of DigiKey <> MPN

script_path = os.path.dirname(os.path.realpath(__file__))
digikey_MPN_db_file = os.path.join(script_path, 'db', 'digikey-mpn.pickle')
digikey_moq_aliases_db_file = os.path.join(script_path, 'db', 'digikey-moq-aliases.pickle')
MPN_manufacturer_db_file = os.path.join(script_path, 'db', 'mpn-manufacturer.pickle')
MPN_description_db_file = os.path.join(script_path, 'db', 'mpn-description.pickle')

try:
    with open(digikey_MPN_db_file, 'rb') as f:
        _digikey_MPN = pickle.load(f)
except IOError:
    _digikey_MPN = bidict.bidict()

try:
    with open(digikey_moq_aliases_db_file, 'rb') as f:
        _digikey_moq_aliases = pickle.load(f)
except IOError:
    _digikey_moq_aliases = dict()

try:
    with open(MPN_manufacturer_db_file, 'rb') as f:
        _MPN_manufacturer = pickle.load(f)
except IOError:
    _MPN_manufacturer = dict()

try:
    with open(MPN_description_db_file, 'rb') as f:
        _MPN_description = pickle.load(f)
except IOError:
    _MPN_description = dict()

def _sync_digikey_MPN():
    with open(digikey_MPN_db_file, 'wb') as f:
        pickle.dump(_digikey_MPN, f, pickle.HIGHEST_PROTOCOL)

def _sync_digikey_moq_aliases():
    with open(digikey_moq_aliases_db_file, 'wb') as f:
        pickle.dump(_digikey_moq_aliases, f, pickle.HIGHEST_PROTOCOL)

def _sync_MPN_manufacturer():
    with open(MPN_manufacturer_db_file, 'wb') as f:
        pickle.dump(_MPN_manufacturer, f, pickle.HIGHEST_PROTOCOL)

def _sync_MPN_description():
    with open(MPN_description_db_file, 'wb') as f:
        pickle.dump(_MPN_description, f, pickle.HIGHEST_PROTOCOL)

def _sync():
    _sync_digikey_MPN()
    _sync_digikey_moq_aliases()
    _sync_MPN_manufacturer()
    _sync_MPN_description()


def check_digikey_moq_alias(digikey_high_moq_sku, mpn):
    if digikey_high_moq_sku in _digikey_moq_aliases:
        return _digikey_moq_aliases[digikey_high_moq_sku]

    if digikey_high_moq_sku[-4:] == '2-ND':
        single_sku = digikey_high_moq_sku[:-4] + '1-ND'
    elif digikey_high_moq_sku[-5:] == 'TR-ND':
        single_sku = digikey_high_moq_sku[:-5] + 'CT-ND'
    else:
        raise NotImplementedError("High MOQ SKU? {}".format(digikey_high_moq_sku))

    queries = [ {'sku': single_sku, 'seller': 'Digi-Key', 'reference': 'line1'} ]
    response = _do_queries(queries)

    item = response['results'][0]['items'][0]

    new_mpn = item['mpn']
    if new_mpn != mpn:
        # Not the same part, just return the original
        print("WARN: differing MPN looking up high moq: {} != {}".format(new_mpn, mpn))
        return digikey_high_moq_sku

    for offer in item['offers']:
        if offer['seller']['name'] == 'Digi-Key':
            if offer['sku'] == digikey_high_moq_sku:
                _digikey_moq_aliases[digikey_high_moq_sku] = single_sku
                _sync_digikey_moq_aliases()
                return check_digikey_moq_alias(digikey_high_moq_sku, mpn)

    return digikey_high_moq_sku


def _update_from_response(item, _looked_up_digikey=None, _looked_up_mpn=None):
    mpn = item['mpn']
    if _looked_up_mpn and _looked_up_mpn != mpn:
        raise NotImplementedError("Internal Error: MPN returned doesn't match query? {} != {}".\
                format(_looked_up_mpn, mpn))

    for offer in item['offers']:
        if offer['seller']['name'] == 'Digi-Key':
            digikey = offer['sku']

            # A bit of a hack here, OctoPart API prefers the large quantity choices, but
            # we prefer the `minimum order quantity` 1 parts from digi-key
            if offer['moq'] > 1:
                digikey = check_digikey_moq_alias(digikey, mpn)

            if _looked_up_digikey and _looked_up_digikey != digikey:
                raise NotImplementedError("Internal Error: Digi-Key returned doesn't match query? {} != {}".\
                        format(_looked_up_digikey, digikey))
            break
    else:
        raise NotImplementedError("No Digi-Key part number: {}".format(item['offers']))

    try:
        _digikey_MPN[digikey] = mpn
    except bidict.BidictException:
        print("digikey: {}".format(digikey))
        print("    mpn: {}".format(mpn))
        pprint(_digikey_MPN)
        raise
    _sync_digikey_MPN()

    manufacturer = item['manufacturer']['name']
    _MPN_manufacturer[mpn] = manufacturer
    _sync_MPN_manufacturer()

    # Prefer Digi-Key's description, but take anything we can get
    for description in item['descriptions']:
        if description['attribution']['sources'][0]['name'] == 'Digi-Key':
            text = description['value']
            break
    else:
        text = item['descriptions'][0]['value']
    _MPN_description[mpn] = text
    _sync_MPN_description()


def _do_queries(queries):
    print("OctoPart Query: {}".format(queries))

    url = 'http://octopart.com/api/v3/parts/match?queries=%s' % urllib.parse.quote(json.dumps(queries))
    url += '&exact_only=true'
    url += '&include[]=descriptions'
    url += '&apikey=1f14f7be'

    try:
        data = urllib.request.urlopen(url).read()
        response = json.loads(data)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            print("Hit OctoPart rate limit. Cooling down for 5s")
            time.sleep(5)
            return _do_queries(queries)
        raise

    # Rate Limit
    time.sleep(.1)

    return response

def fetch_from_digikey(digikey_part):
    # https://octopart.com/api/docs/v3/rest-api#endpoints-parts-match
    # https://octopart.com/static/api/v3/examples/parts_match.py
    queries = [ {'sku': digikey_part, 'seller': 'Digi-Key', 'reference': 'line1'} ]
    response = _do_queries(queries)

    try:
        hits = response['results'][0]['hits']
        if hits > 1:
            pprint(response['results'][0])
            raise NotImplementedError('Ambiguous Digikey SKU (multiple results)')
    except KeyError:
        raise NotImplementedError('Lookup failed for DigiKey part {}'.format(digikey_part))

    _update_from_response(response['results'][0]['items'][0], _looked_up_digikey=digikey_part)


def fetch_from_mpn(mpn):
    queries = [ {'mpn': mpn, 'reference': 'line1'} ]
    response = _do_queries(queries)

    try:
        hits = response['results'][0]['hits']
        if hits > 1:
            pprint(response['results'][0])
            raise NotImplementedError('Ambiguous MPN (multiple results)')
    except KeyError:
        raise NotImplementedError('Lookup failed for DigiKey part {}'.format(digikey_part))

    _update_from_response(response['results'][0]['items'][0], _looked_up_mpn=mpn)



def digikey_to_MPN(digikey_part):
    try:
        return _digikey_MPN[digikey_part]
    except KeyError:
        pass
    fetch_from_digikey(digikey_part)
    return digikey_to_MPN(digikey_part)

def MPN_to_manufacturer(mpn):
    try:
        return _MPN_manufacturer[mpn]
    except KeyError:
        pass
    fetch_from_mpn(mpn)
    return MPN_to_manufacturer(mpn)

def MPN_to_description(mpn):
    try:
        return _MPN_description[mpn]
    except KeyError:
        pass
    fetch_from_mpn(mpn)
    return MPN_to_description(mpn)


##############################################################################
## Helper Functions
known_unit_prefixes = {
        'f': 1e-15,
        'p': 1e-12,
        'n': 1e-9,
        'u': 1e-6,
        'µ': 1e-6,
        'm': 1e-3,
        'c': 1e-2,
        'd': 1e-1,
        '': 1,
        'D': 1e1,
        'h': 1e2,
        'k': 1e3,
        'M': 1e6,
        'G': 1e9,
        }

def resolve_unit(value, unit_prefix):
    if unit_prefix == '':
        try:
            out = float(value)
        except:
            if value == 'DNP':
                out = float("inf")
            else:
                out = value
        return out
    else:
        return float(value) * known_unit_prefixes[unit_prefix]

Value = collections.namedtuple('Value', ('magnitude', 'prefix', 'unit', 'normalized'))
Value.__str__ = lambda x: '{}{}{}'.format(x.magnitude, x.prefix, x.unit) if x.magnitude is not None else '<No Value>'
def Value_from_string(string):
    # Create a null "value" for parts with no value
    if string is None:
        return Value(magnitude=None, prefix=None, unit=None, normalized=None)

    # Split 0.5kΩ into `0.5` and `kΩ`
    try:
        r = re.compile("([0-9.]+)[ ]*([{}]?)([^ ]+)".\
                format(''.join(known_unit_prefixes.keys())))
        m = r.match(string)
        magnitude = m.group(1)
        prefix = m.group(2)
        unit = m.group(3)
    except:
        print("Error parsing value?")
        print("Often this means that the value is incorrect")
        print("Consider fixing the board before hacking this script")
        print("")
        print("Problematic part:")
        print("  Part: {}".format(part))
        print("  Name: {}".format(name))
        print(" Value: {}".format(value))
        print("")
        raise

    magnitude = float(magnitude)
    if int(magnitude) == magnitude:
        magnitude = int(magnitude)

    v = Value(
            magnitude=magnitude,
            prefix=prefix,
            unit=unit,
            normalized=resolve_unit(magnitude, prefix)
            )
    return v

def collapse_range(numbers):
    n = list(map(int, numbers))
    n.sort()
    if len(n) == 1:
        return '{}'.format(n[0])
    if (n[-1] - n[0] + 1) != len(n):
        return '{}-!renumber!-{}'.format(n[0], n[-1])
    return '{}-{}'.format(n[0], n[-1])

##############################################################################
## File parsing / building up internal data structures

# In swoop, schmatics are made of "parts"
def parts_to_kinds(parts):
    kinds = {}
    name_to_part = {}
    name_re = re.compile("([a-zA-Z$]+)([0-9]+)")
    for part in parts:
        name = part.get_name()

        name_to_part[name] = part

        # Split C12 into `C` and `12`
        m = name_re.match(name)
        kind = m.group(1)
        number = m.group(2)

        # Skip over some of the stuff we don't care about
        if kind in ('FRAME', 'GND', 'U$'):
            continue

        if kind not in kinds:
            kinds[kind] = {}

        value = part.get_value()
        if kind[0] == 'U':
            # It seems that parts with "no value" according to the library
            # editor will end up with a "value" key if it's got multiple package
            # options, for example:
            # <part name="U28" library="signpost" deviceset="MCP23008" device="QFN" value="MCP23008QFN"/>
            # This makes an educated guess that it'll only happen for ICs, so we
            # skip the U family of components and hope that works
            value = None

        if value is not None and 'dnp' in value.lower():
            continue

        v = Value_from_string(value)
        if v not in kinds[kind]:
            kinds[kind][v] = {}

        device = part.get_device()
        if device not in kinds[kind][v]:
            kinds[kind][v][device] = {}

        kinds[kind][v][device][number] = part
    return kinds, name_to_part

# In swoop, boards are made of "elements"
def build_element_map(elements):
    sch_to_brd = {}
    orphans = []
    for element in elements:
        name = element.get_name()

        try:
            sch_to_brd[name_to_sch_part[name]] = element
        except KeyError:
            # Logos are frequently added to boards w/out a schematic part, this
            # is fine, ignore those
            if element.get_library() != 'logos':
                orphans.append(element)

    if len(orphans):
        termcolor.cprint('WARN: The following board elements have no corresponding schematic part:', attrs=['bold'])
        for orphan in orphans:
            print(orphan)

        r = input("Continue ignoring orphan elements? [Y/n] ")
        if len(r) and r.lower()[0] == 'n':
            sys.exit(1)
    return sch_to_brd

sch_kinds, name_to_sch_part = parts_to_kinds(Swoop.From(sch).get_parts())
sch_part_to_brd_element = build_element_map(Swoop.From(brd).get_elements())



def handle_attrs_for_part(part):
    try:
        return _handle_attrs_for_part(part)
    except:
        print('')
        termcolor.cprint('Exception handling: {}'.format(part), attrs=['bold'])
        print('')
        raise

def _handle_attrs_for_part(part):
    # Load existing attributes and clean up whitespace if needed:
    MPN = part.get_attribute('MPN')
    MPN = MPN.get_value() if MPN else None
    if MPN and MPN != MPN.strip():
        part.set_attribute('MPN', MPN.strip())
        MPN = part.get_attribute('MPN').get_value()

    DIGIKEY = part.get_attribute('DIGIKEY')
    DIGIKEY = DIGIKEY.get_value() if DIGIKEY else None
    if DIGIKEY and DIGIKEY != DIGIKEY.strip():
        part.set_attribute('DIGIKEY', DIGIKEY.strip())
        DIGIKEY = part.get_attribute('DIGIKEY').get_value()

    MANUFACTURER = part.get_attribute('MANUFACTURER')
    MANUFACTURER = MANUFACTURER.get_value() if MANUFACTURER else None
    if MANUFACTURER and MANUFACTURER != MANUFACTURER.strip():
        part.set_attribute('MANUFACTURER', MANUFACTURER.strip())
        MANUFACTURER = part.get_attribute('MANUFACTURER').get_value()

    DESCRIPTION = part.get_attribute('DESCRIPTION')
    DESCRIPTION = DESCRIPTION.get_value() if DESCRIPTION else None

    # Fill out missing attributes
    if DIGIKEY:
        mpn = digikey_to_MPN(DIGIKEY)
        # If MPN already exists, validate it matches, o/w add it
        if MPN:
            if mpn != MPN:
                raise NotImplementedError('Mismatch MPN?? {} != {}'.format(mpn, MPN))
        else:
            part.set_attribute('MPN', mpn)
    elif MPN:
        # No DigiKey, but have MPN
        DIGIKEY = MPN_to_digikey(MPN)
        part.set_attribute('DIGIKEY', DIGIKEY)
    else:
        # No attrs to look anything up with
        return

    manufacturer = MPN_to_manufacturer(mpn)
    # If MANUFACTURER exists, validate it matched, o/w add it
    if MANUFACTURER:
        if manufacturer != MANUFACTURER:
            raise NotImplementedError('Mismatch MANUFACTURER?? {} != {}'.\
                    format(manufacturer, MANUFACTURER))
    else:
        part.set_attribute('MANUFACTURER', manufacturer)

    # Only add DESCRIPTION if there's not one there
    if not DESCRIPTION:
        part.set_attribute('DESCRIPTION', MPN_to_description(mpn))


# Copy all attributes from part to element (sch -> brd)
def handle_attrs_update_element(part, element):
    _debug = False

    if _debug:
        print("_"*80)
        print(part)
        print(get_Attributes_from_part(part))
        print("")
        print(element)
        print(element.get_attributes())
        print(get_Attributes_from_part(element))
        print("")
        for a in element.get_attributes():
            print(a.get_name(), a.get_value())
        print(' ...... ')

    for attr in get_Attributes_from_part(part):
        if _debug:
            print(">{}<".format(attr))

        # Eagle requires that attributes have a bunch of info that's already in
        # the enclosing element tag, but it'll barf w/out them, so here goes
        #
        # <attribute name="DIGIKEY" value="490-10451-1-ND" x="32.512" y="81.28" size="1.778" layer="27" display="off"/>
        new_attr = Swoop.Attribute()
        new_attr.set_name(attr.name)
        new_attr.set_value(attr.value)
        new_attr.set_x(element.get_x())
        new_attr.set_y(element.get_y())
        # Attributes need a size, but we never show them, so arbitrary is fine
        new_attr.set_size(1.778)
        new_attr.set_layer('tValues') # seems to be where Eagle puts misc attributes
                                      # [our "cloned" name attr is on 25, tNames]
        new_attr.set_display("off")
        element.add_attribute(new_attr)

    if _debug:
        print("- - - - - "*5)
        print(part)
        print(element)
        print(get_Attributes_from_part(element))
        print("")
        for a in element.get_attributes():
            print(a.get_name(), a.get_value())


Attribute = collections.namedtuple('Attribute', ('name', 'value'))
def swoop_attribute_to_Attribute(swoop_attribute):
    return Attribute(
            name=swoop_attribute.get_name(),
            value=swoop_attribute.get_value(),
            )

def get_Attributes_from_part(part):
    #return [swoop_attribute_to_Attribute(a) for a in part.get_attributes()]
    # get_all_attributes will grab attributes from libraries as well
    r = []
    for name,value in part.get_all_attributes().items():
        r.append(Attribute(name=name, value=value))
    return r

def attr_row_helper(kind, value, device, number, part, rows):
    row = ['' for x in range(len(rows[0]))]
    row[0] = number
    row[1] = str(value)
    row[2] = device

    attrs = get_Attributes_from_part(part)

    for attr in attrs:
        try:
            idx = rows[0].index(attr.name)
            row[idx] = attr.value
        except ValueError:
            row[-1] += '!{}:{}!'.format(attr.name, attr.value)

    return row


def handle_orphan_parts(orphan_parts):
    real_orphans = []

    for orphan in orphan_parts:
        # We create custom supplies sometimes, can safely ignore those
        deviceset = orphan.get_deviceset()
        if 'VCC_' in deviceset:
            pass
        else:
            real_orphans.append(orphan)

    if len(real_orphans):
        termcolor.cprint('WARN: The following schematic parts have no corresponding board elements:', attrs=['bold'])
        for orphan in real_orphans:
            print(orphan)

        r = input("Continue ignoring orphan elements? [Y/n] ")
        if len(r) and r.lower()[0] == 'n':
            sys.exit(1)


# Iterating 'C', 'R', 'Q', etc
for kind in sorted(sch_kinds):
    print('== {} '.format(kind) + '='*60)
    values = sch_kinds[kind]
    rows = [['Name', 'Value', 'Package', 'DESCRIPTION', 'DIGIKEY', 'MPN', 'MANUFACTURER', '!Other!']]
    rows_before = [['Name', 'Value', 'Package', 'DESCRIPTION', 'DIGIKEY', 'MPN', 'MANUFACTURER', '!Other!']]

    # Iterating '10uF', '100uF', etc
    for value in sorted(values, key=lambda v: v.normalized):
        for device in sorted(sch_kinds[kind][value]):
            # Grab the state of the world before we've done anything
            # Iterating C10, C11, C12, etc
            for number in sorted(sch_kinds[kind][value][device], key=lambda n: int(n)):
                sch_part = sch_kinds[kind][value][device][number]

                before = attr_row_helper(kind, value, device, number, sch_part, rows_before)
                rows_before.append(before)



            if value.magnitude is not None:
                # For parts with values, all parts with the same value (i.e. all the
                # 1k resistors) should have the same attributes, this makes that
                # happen. For stuff without values (i.e. ICs, LEDs), skip this step

                # First check if there are any conflicts in existing attributes
                existing_attrs = []
                no_attrs = []
                # Iterating C10, C11, C12, etc
                for number in sorted(sch_kinds[kind][value][device], key=lambda n: int(n)):
                    sch_part = sch_kinds[kind][value][device][number]
                    attrs = get_Attributes_from_part(sch_part)
                    if attrs:
                        if attrs not in existing_attrs:
                            existing_attrs.append(attrs)
                    else:
                        no_attrs.append(sch_part)

                if len(existing_attrs) > 1:
                    print('')
                    termcolor.cprint('Error: Conflicting attributes', attrs=['bold'])
                    print('Parts of the same kind and same value have differing attributes')
                    print('This is probably a bad thing that you should fix up')
                    print('Caveat: This script does not handle multiple packages yet')
                    print('        i.e. if you have 0402 and 0603 0.1uF caps, this will fail')
                    print('')
                    for attrs in existing_attrs:
                        print(attrs)
                        for number,part in sch_kinds[kind][value][device].items():
                            if attrs == get_Attributes_from_part(part):
                                print("{} ".format(number), end='')
                        print('')
                    raise NotImplementedError("Conflicting existing attrs: {}".format(existing_attrs))

                if len(existing_attrs) == 1:
                    # Add attributes from one part to all identical parts
                    for sch_part in no_attrs:
                        for attr in existing_attrs[0]:
                            sch_part.set_attribute(attr.name, attr.value)



            # Next iterate parts to flesh out all attributes
            # Iterating C10, C11, C12, etc
            orphan_parts = []
            for number in sorted(sch_kinds[kind][value][device], key=lambda n: int(n)):
                sch_part = sch_kinds[kind][value][device][number]
                handle_attrs_for_part(sch_part)

                try:
                    brd_element = sch_part_to_brd_element[sch_part]
                    handle_attrs_update_element(sch_part, brd_element)
                except KeyError:
                    orphan_parts.append(sch_part)

                row = attr_row_helper(kind, value, device, number, sch_part, rows)
                rows.append(row)
            handle_orphan_parts(orphan_parts)

    if rows_before == rows:
        termcolor.cprint('No changes', attrs=['bold'])
        print(dataprint.to_string(rows))
    else:
        with tempfile.NamedTemporaryFile(mode='w+t') as before, tempfile.NamedTemporaryFile(mode='w+t') as after:
            # HACK for space of MPN entry on diff
            rows_before[0][rows_before[0].index('MPN')] = '.' * 8 + 'MPN' + '.' * 8
            rows[0][rows[0].index('MPN')] = '.' * 8 + 'MPN' + '.' * 8

            dataprint.to_file(before, rows_before)
            dataprint.to_file(after, rows)
            before.flush()
            after.flush()
            options = icdiff.get_options()[0]
            options.no_headers = True
            icdiff.diff_files(options, before.name, after.name)
    print('')

print()
r = input('Write updated Eagle files? [Y/n] ')
if len(r) and r[0].lower() == 'n':
    sys.exit()

sch.write(sch_file)
brd.write(brd_file)


###############################################################################
## Try to reduce the Eagle file diff churn a little

# This is a bit obnoxious, but worth doing:
#
# When the lxml library internal to Swoop writes back the Eagle file, it
# consistently treats all float fields as floats, whereas Eagle will round off
# whole integers when it writes the fields, i.e.:
#  - Eagle:  <instance gate="G$2" part="FRAME9" x="152.4" y="0"/>
#  -  lxml:  <instance gate="G$2" part="FRAME9" x="152.4" y="0.0"/>
# In practice, these are the same, and Eagle handles them appropriately, but
# they make for a really noisy diff.
#
# While we're at it, Eagle will strip the nice indentation the next time it
# saves the file, so let's just do it ourselves now

r = re.compile('("-?[0-9]+)\.0(")')
for eagle_file in (sch_file, brd_file):
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmpfile:
        with open(eagle_file) as ifile:
            for line in ifile:
                # x.0 -> x
                if 'version="1.0"' in line:
                    # Need to protect the first line:
                    # <?xml version="1.0" encoding="utf-8"?>
                    tmpfile.write(line)
                    continue
                line = r.sub(r'\1\2', line)

                # Strip leading whitespace
                # Try not to mess with multi-line text elements
                if len(line.strip()) and line.strip()[0] == '<':
                    line = line.strip() + '\n'

                tmpfile.write(line)
    # https://stackoverflow.com/a/31499114/358675
    # Overwrite the original file with the munged temporary file in a
    # manner preserving file attributes (e.g., permissions).
    shutil.copystat(eagle_file, tmpfile.name)
    shutil.move(tmpfile.name, eagle_file)
