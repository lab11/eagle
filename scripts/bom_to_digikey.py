#!/usr/bin/env python
# -*- coding: utf-8 -*-

print("This script takes a BOM (in csv) and turns it into an uploadable Digikey order (also csv).");
print("To use the script you must have a \"Part\" Column and up to four \"DIGIKEY*\" columns.");
print("You can then enter the rough number of components you want to order.\n\n")

import sys

# Get all of the tricky packages out of the way
try:
        from sh import rm
except:
        print("You need to install the sh module.")
        print("https://github.com/amoffat/sh")
        sys.exit(1)

try:
        from sh import unoconv
        from sh import soffice
        import sh
except:
        print("You must have unoconv installed to convert the bom.")
        print("sudo apt-get install unoconv")
        sys.exit(1)

try:
        import dataprint
except:
        print("You need to install the dataprint module.")
        print("sudo pip install dataprint")
        sys.exit(1)

try:
    import natsort
except:
    print("You need to pip install natsort.")
    sys.exit(1)

import csv as csvr
from glob import glob
import os
import itertools
import re
import operator


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

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
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

# Display the help if any arguments are provided.
if len(sys.argv) > 1:
        print(HELP)
        sys.exit(0)


boms = glob('*bom.xls*')

if len(boms) == 0:
        print("Could not find a bom to convert.")
        sys.exit(1)

for b in boms:
        # Get the root name
        base = os.path.splitext(b)[0]
        csv_out = '{}_digikey.csv'.format(base)
        csv_in = '{}.csv'.format(base)

        # Check if csv and txt versions already exist
        if os.path.exists(csv_out):
                # Open it and determine if we created it. If we did, then I'm sure it's
                # fine to overwrite it. Otherwise, we probably shouldn't just overwrite
                # other people's files.
                with open(csv_out, 'r') as f:
                    print('Found existing {}'.format(csv_out));
                    if query_yes_no("Would you like to overwrite it?"):
                        pass
                    else:
                        print("Okay, exiting");
                        sys.exit(1)

        parts = {};
        qtys = {}
        parts_with_refs = {}
        with open(csv_in, 'r') as f:
                # Figure out where all the columns are there are
                csvreader = csvr.reader(f)
                columns = next(csvreader);
                columns = next(csvreader);
                columns = next(csvreader);
                columns = next(csvreader);
                columns = next(csvreader);
                try:
                    parts_column = columns.index('Part');
                except ValueError:
                    print("There must be a column called \"Part\" to execute this script. Exiting");
                    sys.exit(1);

                digikey_columns = [];
                try:
                    digikey_columns.append(columns.index('DIGIKEY'));
                    digikey_columns.append(columns.index('DIGIKEY1'));
                except ValueError:
                    pass

                if(len(digikey_columns) < 1):
                    print("There must a column called \"DIGIKEY*\" to execute this script. Exiting");
                    sys.exit(1);

                try:
                    digikey_columns.append(columns.index('DIGIKEY2'));
                    digikey_columns.append(columns.index('DIGIKEY3'));
                    digikey_columns.append(columns.index('DIGIKEY4'));
                except ValueError:
                    pass


                #process the columns into a dictionary where digikey part is
                #the key and a list of part number is the value
                #keep another dictionary of qtys for each part
                for part in csvreader:
                    for col in digikey_columns:
                        if part[col] in parts:
                            parts[part[col]].append(part[parts_column]);
                            qtys[part[col]] = qtys[part[col]] + 1;
                        else:
                            if part[col] != '':
                                parts[part[col]] = [part[parts_column]];
                                qtys[part[col]] = 1;

                #for each part in the dictionary compress the part numbers
                #to put in the digikey reference field
                for part, ref_list in parts.items():
                    #sort the list alphabetically
                    #this should group all the prefixes together
                    ref_list = natsort.natsorted(ref_list);
                    ref_string = ""
                    cur_prefix = ""
                    cur_num = 0;
                    first_num = 0;
                    for ref in ref_list:
                        #we are already processing that prefix, just add the number
                        if re.match("[a-zA-Z]+",ref).group(0) == cur_prefix:
                            num = int(re.match(".*?([0-9]+)$",ref).group(1));
                            if cur_num + 1 is num:
                                cur_num = num;
                            else:
                                if first_num == cur_num:
                                    ref_string = ref_string + (str(first_num)+" ")
                                else:
                                    ref_string = ref_string + (str(first_num)+"-"+str(cur_num)+" ")
                                cur_num = num;
                                first_num = num;

                        else:
                            #finish up the older prefix
                            if cur_prefix is "":
                                pass
                            else:
                                if cur_num is first_num:
                                    ref_string = ref_string + str(cur_num)+" ";
                                else:
                                    ref_string = ref_string+(str(first_num)+"-"+str(cur_num)+" ");
                            #we need to start a new prefix
                            cur_prefix = re.match("[a-zA-Z]+",ref).group(0);
                            ref_string = ref_string +  re.match("[a-zA-Z]+",ref).group(0);
                            cur_num = int(re.match(".*?([0-9]+)$",ref).group(1));
                            first_num = int(re.match(".*?([0-9]+)$",ref).group(1));


                    if cur_num is first_num:
                        ref_string = ref_string + (str(cur_num));
                    else:
                        ref_string = ref_string + (str(first_num)+"-"+str(cur_num));

                    parts_with_refs[part] = ref_string;

        print("How many of each resistor would you like to buy?:");
        try:
            res_qty = int(raw_input());
        except ValueError:
            print("Must input an integer, exiting.");
            sys.exit(1);

        print("How many of each capacitor would you like to buy?:");
        try:
            cap_qty = int(raw_input());
        except ValueError:
            print("Must input an integer, exiting.");
            sys.exit(1);

        print("How many of every other part would you like to buy?:");
        try:
            board_qty = int(raw_input());
        except ValueError:
            print("Must input an integer, exiting.");
            sys.exit(1);

        #sort the dictionary so similar parts are grouped
        #transform it into a tuple for this
        sorted_parts_with_refs = sorted(parts_with_refs.items(), key = operator.itemgetter(1))

        # Write back CSV
        with open(csv_out, 'w') as f:
               # Add header to csv
            f.write("Part List, Digikey Part Number, QTY\n");
            for part, ref_list in sorted_parts_with_refs:
                if(ref_list[0] == "R"):
                    f.write(ref_list + "," + part + "," + str(qtys[part]*res_qty) + "\n");
                elif ref_list[0] == "C":
                    f.write(ref_list + "," + part + "," + str(qtys[part]*cap_qty)+ "\n");
                else:
                    f.write(ref_list + "," + part + "," + str(qtys[part]*board_qty)+ "\n");
            f.close();
