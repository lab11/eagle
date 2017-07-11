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
import sys
import time
import urllib.request, urllib.parse, urllib.error

# Third Party Libraries (i.e. need pip install)
import bidict
import dataprint
import Swoop

sch_file = glob.glob('*.sch')[0]
brd_file = glob.glob('*.brd')[0]

brd = Swoop.EagleFile.from_file(brd_file)
sch = Swoop.EagleFile.from_file(sch_file)

#old_brd = Swoop.EagleFile.from_file(brd_file)
#old_sch = Swoop.EagleFile.from_file(sch_file)


##############################################################################
## Part database

# Every API for this rate limits to a few requests / second at most, so we
# build up a local cache of DigiKey <> MPN

script_path = os.path.dirname(os.path.realpath(__file__))
digikey_MPN_db_file = os.path.join(script_path, 'db', 'digikey-mpn.pickle')
digikey_moq_aliases_db_file = os.path.join(script_path, 'db', 'digikey-moq-aliases.pickle')
MPN_manufacturer_db_file = os.path.join(script_path, 'db', 'mpn-manufacturer.pickle')

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


def _sync_digikey_MPN():
    with open(digikey_MPN_db_file, 'wb') as f:
        pickle.dump(_digikey_MPN, f, pickle.HIGHEST_PROTOCOL)

def _sync_digikey_moq_aliases():
    with open(digikey_moq_aliases_db_file, 'wb') as f:
        pickle.dump(_digikey_moq_aliases, f, pickle.HIGHEST_PROTOCOL)

def _sync_MPN_manufacturer():
    with open(MPN_manufacturer_db_file, 'wb') as f:
        pickle.dump(_MPN_manufacturer, f, pickle.HIGHEST_PROTOCOL)

def _sync():
    _sync_digikey_MPN()
    _sync_digikey_moq_aliases()
    _sync_MPN_manufacturer()


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


def _do_queries(queries):
    print("OctoPart Query: {}".format(queries))

    url = 'http://octopart.com/api/v3/parts/match?queries=%s' % urllib.parse.quote(json.dumps(queries))
    url += '&apikey=1f14f7be'

    data = urllib.request.urlopen(url).read()
    try:
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
Value.__str__ = lambda x: '{}{}{}'.format(x.magnitude, x.prefix, x.unit)
def Value_from_string(string):
    # Split 0.5kΩ into `0.5` and `kΩ`
    try:
        r = re.compile("([0-9.]+)[ ]*([{}]?)([^ ]+)".\
                format(''.join(known_unit_prefixes.keys())))
        m = r.match(value)
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

kinds = {}

parts = Swoop.From(sch).get_parts()
for part in parts:
    name = part.get_name()
    # Split C12 into `C` and `12`
    r = re.compile("([a-zA-Z$]+)([0-9]+)")
    m = r.match(name)
    kind = m.group(1)
    number = m.group(2)

    # Skip over some of the stuff we don't care about
    if kind in ('FRAME', 'GND'):
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

    if value is not None:
        v = Value_from_string(value)
        if v not in kinds[kind]:
            kinds[kind][v] = {}
        kinds[kind][v][number] = part


def handle_attrs(attrs):
    if 'DIGIKEY' in attrs:
        attrs['DIGIKEY'] = attrs['DIGIKEY'].strip()
        mpn = digikey_to_MPN(attrs['DIGIKEY'])
        if 'MPN' in attrs:
            attrs['MPN'] = attrs['MPN'].strip()
            if mpn != attrs['MPN']:
                raise NotImplementedError('Mismatch MPN?? {} != {}'.format(mpn, attrs['MPN']))
        attrs['MPN'] = mpn
    elif 'MPN' in attrs:
        attrs['MPN'] = attrs['MPN'].strip()
        mpn = attrs['MPN']
        attrs['DIGIKEY'] = MPN_to_digikey(attrs['MPN'])
    else:
        # No attrs to look anything up with
        return

    manufacturer = MPN_to_manufacturer(mpn)
    if 'Manufacturer' in attrs:
        attrs['Manufacturer'] = attrs['Manufacturer'].strip()
        if manufacturer != attrs['Manufacturer']:
            raise NotImplementedError('Mismatch Manufacturer?? {} != {}'.\
                    format(manufacturer, attrs['Manufacturer']))
    else:
        attrs['Manufacturer'] = manufacturer


for kind in kinds:
    print('== {} '.format(kind) + '='*60)
    values = kinds[kind]
    rows = [('Name', 'Value', 'DIGIKEY', 'MPN', 'Manufacturer', '!Other!')]
    for value in sorted(values, key=lambda v: v.normalized):
        idents = collapse_range(kinds[kind][value].keys())
        for number in sorted(kinds[kind][value], key=lambda n: int(n)):
            row = ['' for x in range(len(rows[0]))]
            row[0] = number
            row[1] = str(value)

            part = kinds[kind][value][number]
            attrs = part.get_all_attributes()

            handle_attrs(attrs)

            for attr,val in attrs.items():
                try:
                    idx = rows[0].index(attr)
                    row[idx] = val
                except ValueError:
                    row[-1] += '!{}:{}!'.format(attr, val)

            rows.append(row)
    print(dataprint.to_string(rows))
    print('')

