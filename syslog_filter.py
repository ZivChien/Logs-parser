#!/usr/bin/python
# -----------------
# Linux syslog filter. filting some syslog header.
#  bug report: thinkroute@gmail.com
# -----------------

import sys
import os
import re
import argparse 
import pandas as pd

FILE="logs/syslog.1"
VERSION="0.3"
HOSTNAME="root888-laptop"
SSNAME = ['gnome-session', 'libCashDrawer', 'aip4750cd']
LNO = 0	#line no
RNO = 0	#record no
FNO = 0	#fail record no
D_RECORD = {}   # dict of record
D_FAIL = {}     # dict of fail record
D_DES = {}      # dict of fail description
D_DEV = {}      # dict of fail device

def cli_parser():
    des = "syslog parser. ()"
    epi = "Bug report: thinkroute@gmail.com"

    parser = argparse.ArgumentParser(description=des, epilog=epi)
    parser.add_argument("-e", "--excel", type=str, default="NONE", help="output as an Excel file, default is output in the screen.")
    parser.add_argument("-f", "--file", type=str, default=FILE, help="target log file name.")
    parser.add_argument("-V", "--version", action='version', version="Version=" + VERSION, help="display version")
    parser.add_argument("-v", "--verbose", action='store_true', help="output detail log, default is output a summary table, enable the option only worked with the EXCEL option as default")
    parser.add_argument("-d", "--drop", action='store_true', help="enable to drop the non-cashdrawer routine, default is drop all.")
    args = parser.parse_args()

    if (os.path.isfile(args.file) != 1):
        print("ERR: target log file (" + args.file + ") not exist!")
        sys.exit(-1)

    if (args.excel != "NONE"):
        if (args.verbose == True):
            print("ERR: the EXCEL and VERBOSE option as a mutex")
            sys.exit(-1)
        elif (not re.search("\.", args.excel)):
            args.excel = args.excel + ".xls"
        elif (not re.search("\.xls$", args.excel)):
            args.excel = args.excel.split(".")[-1] + ".xls"

    return args

def isSname(name):
    global SSNAME

    for x in SSNAME:
        if x == name:
            return 1
    return 0


def main():
    args=cli_parser()

    try:
        fp = open(args.file, "r")
    except IOError:
        print("ERR: target log file can't open!")
        sys.exit(1)

    global LNO	#line no
    global RNO	#record no
    global FNO  #fail record no
    global D_RECORD # record dict
    global D_FAIL   # fail record dict
    global D_DES    # dict of fail description
    global D_DEV    # dict of fail device
    global sy_cnt
    sy_cnt = 0  #line counter for collecting failure symptom 

    for l in fp:

        if (bool(re.search(HOSTNAME, l)) != True):
            continue

        l = re.search('(.*)\s'+ HOSTNAME +'\s(.*)', l.strip()).group(2)
        l = re.search('(\S*):\s(.*)', l)
        snm = l.group(1)    #session name
        des = l.group(2)    #description

        # remove PID on session name
        if re.search('\]$', snm):
            snm = re.search('(.*)\[\d*\]', snm).group(1)
        
        # if option DROP is enable, then drop non-cashdrawer's routine
        if (args.drop == False):
            if not isSname(snm):
                #LNO -= 1
                continue

        LNO += 1
        # remove timestamp on detail description
        if (re.search('^\d+:\d+:\d+\.\d*\s', des)):
            des = re.search('^\d+:\d+:\d+\.\d*\s(\[\S*\].*)', des).group(1)

        # formatting routine name
        if (re.search("^\[\S*\]", des)):
            tmp = re.search("^(\[\S*\])\s*(.*)", des)
            t1 = tmp.group(1)
            t2 = tmp.group(2)
            des = t1 + ", " + t2

        # RNO as a record counter which depend on "gnome-session with Tool started"
        if (snm == "gnome-session"):
            if (re.search("Tool\sstarted", des)):
                RNO += 1
                D_RECORD[RNO] = LNO
                D_FAIL[RNO] = "pass"    #init for fail record
                D_DES[RNO] = "none"     #init for fail description
                D_DEV[RNO] = "none"     #init for fail device
            elif (re.search("Error\sSummary:", des)):
                FNO += 1
                D_FAIL[RNO] = str(LNO)
                sy_cnt = 4

            if (sy_cnt == 3):
                sy_cnt -= 1
                D_DES[RNO] = des
            elif (sy_cnt == 1):
                sy_cnt -= 1
                D_DEV[RNO] = re.search(":\s(.*)", des).group(1)
            elif (sy_cnt != 0):
                sy_cnt -= 1

        #if option VERBOSE is enable, then print the detail information to standard output
        #TODO: default is disable
        if (args.verbose == True):
            out = snm + ", " + des
            print(out)
    
    sumln = "record: " + str(len(D_RECORD)) + " fail: " + str(sum(d != "pass" for d in D_FAIL.values()))
    print("==summary====\n", sumln)

    if (args.excel == "NONE"):
        table = pd.DataFrame({"start": D_RECORD, "result": D_FAIL, "device": D_DEV, "descriptoin": D_DES})
        print(table)
    else:
        D_DES[RNO + 1] = sumln
        table = pd.DataFrame({"start": D_RECORD, "result": D_FAIL, "device": D_DEV, "descriptoin": D_DES})
        table.to_excel(args.excel, sheet_name=args.file)

if __name__ == '__main__':
	main()