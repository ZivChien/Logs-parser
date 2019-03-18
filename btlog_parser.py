#!/usr/bin/python
# -------------------
# Windows Bootlog Parser
#  bug report: ziv.chien@
# -------------------

import sys
import os
import re
import argparse 
import pandas as pd

# --- Global variables
FILE="logs/ntbtlog.txt"
VERSION="1.1"
LNO = 0	#The number of the total line on the target file
RNO = 0	#The number of the total available record on the target file
OS 		= {}	# Version 10.0
BUILD 	= {}	# (Build 14393)
DATE 	= {}	# The date of this boot record
TIME 	= {}	# The time of this boot record
TOTAL 	= {}	# Total number of the boot drivers.
LOADED 	= {}	# Lists on boot driver, then loaded success by this boot
NOT_LOADED = {}	# Lists on boot driver, but not loaded by this boot
FTEC 	= {}	# counter for f3bcbufl[ufl|ufu].sys
CPU  	= {}	# coutner for 4158CPUX64.sys
LAST 	= {}	# the last loaded driver name

class LogInfo:
	def __init__(self):
		self.text 			= ""
		self.ver_win			= 0	#Microsoft (R) Windows (R) Version 10.0 (Build 14393)
		self.ver_build			= 0	#Microsoft (R) Windows (R) Version 10.0 (Build 14393)
		self.date				= 0 #1 11 2019 18:30:51.346
		self.time				= 0
		self.cnt_total			= 0
		self.cnt_loaded 		= 0	#BOOTLOG_LOADED \SystemRoot\system32\ntoskrnl.exe
		self.cnt_not_loaded		= 0	#BOOTLOG_NOT_LOADED \SystemRoot\System32\drivers\cdrom.sys
		self.cnt_ftec			= 0	#f3bcbufl[ufl|ufu].sys
		self.cnt_cpu			= 0 #SystemRoot\System32\drivers\4158CPUX64.sys

	def dellog(self):
		self.text 			= ""
		self.ver_win			= 0
		self.ver_build			= 0
		self.date				= 0
		self.time				= 0
		self.cnt_total			= 0
		self.cnt_loaded 		= 0
		self.cnt_not_loaded		= 0
		self.cnt_ftec			= 0
		self.cnt_cpu			= 0

	def text(self):
		return (self.text)
	def total(self):
		return (self.cnt_total)

	def show(self):
		print(	"OS: ",   self.ver_win, 
				"Buld: ", self.ver_build, 
				"Date: ", self.date,
				"Time: ", self.time,
				"Totl: ", self.cnt_total, 
				"Load: ", self.cnt_loaded, 
				"NoLd: ", self.cnt_not_loaded,
				"FTEC: ", self.cnt_ftec,
				"4158: ", self.cnt_cpu,
				"Last: ", self.text)

	def addlog(self, line):
		self.line = line
		if re.search('^Microsoft', self.line):		#^Microsoft
			self.ver_win = self.line.split(' ')[5].split('.')[0]
			self.ver_build = self.line.split(' ')[7].split(')')[0]
			OS[RNO] 	= self.ver_win
			BUILD[RNO]	= self.ver_build
		elif re.search('^BOOT', self.line):			#BOOTLOG_LOADED
			self.cnt_total += 1
			TOTAL[RNO] 	= self.cnt_total
			load = self.line.split('_')[1].split(' ')[0]
			if re.search('NOT', load):
				self.cnt_not_loaded += 1
				NOT_LOADED[RNO]	= self.cnt_not_loaded
			elif re.search('LOADED', load):
				self.cnt_loaded += 1
				self.text = self.line.split('\\')[-1]
				LOADED[RNO] = self.cnt_loaded
				LAST[RNO]	= self.text
				if re.search('f3bc', self.text):
					self.cnt_ftec += 1
				if re.search('4158CPU', self.text):
					self.cnt_cpu += 1
				FTEC[RNO] = self.cnt_ftec
				CPU[RNO]  = self.cnt_cpu
		elif re.search(':', self.line):		#1 11 2019 18:30:51.346
			ss = self.line.split(':')[1].strip()
			t = re.search('(\d*)\s*(\d*)\s*(\d*)\s*(\d*)$', 
						self.line.split(':')[0].strip())
			dd = t.group(2)
			MM = t.group(1)
			yy = t.group(3)
			mm = t.group(4)
			self.date = yy + "/" + MM + "/" + dd
			self.time = mm + ":" + ss
			DATE[RNO] = self.date
			TIME[RNO] = self.time

def isLogStart(line):
	if re.search('^Microsoft', line):
		return 1
	else:
		return 0

def cli_parser():
	des = "Windows Bootlog parser."
	epi = "Bug report: ziv.chien@mic.com.tw #5620"

	parser = argparse.ArgumentParser(description=des, epilog=epi)
	parser.add_argument("-e", "--excel", type=str, default="NONE", help="output as an Excel file, default is output in the screen")
	parser.add_argument("-f", "--file", type=str, default=FILE, help="target log file name")
	parser.add_argument("-v", "--version", action='version', version="Version=" + VERSION, help="display version")
	args = parser.parse_args()
		
	if (os.path.isfile(args.file) != 1):
		print("ERR: target log file (" + args.file + ") not exist!")
		sys.exit(-1)

	if (args.excel != "NONE"):
		if (not re.search("\.", args.excel)):
			args.excel = args.excel + ".xls"
		elif (not re.search("\.xls$", args.excel)):
			args.excel = args.excel.split(".")[-1] + ".xls"

	return args


def main():
	args=cli_parser()

	try:
		fp = open(args.file, "r", encoding='utf-16')
	except IOError:
		print("ERR: target log file can't open!")
		sys.exit(1)

	global LNO
	global RNO

	info = LogInfo()

	for l in fp:
		LNO += 1
		line = l.strip()
		if isLogStart(line):
			RNO += 1
			if (info.total() == 0):	#null means first
				info.addlog(line)
				continue
			info.dellog()
		info.addlog(line)

	sum = pd.DataFrame({"os": OS, "build": BUILD, "date": DATE, "time": TIME, 
						"total": TOTAL, "loaded": LOADED, "not loaded": NOT_LOADED, 
						"ftec": FTEC, "4158": CPU, "last": LAST})

	if (args.excel == "NONE"):
		header = "LOG: " + args.file + "\tLINE: " + str(LNO) + "\tRECORD: " + str(RNO)
		print(header)
		print(sum)
	else:
		sum.to_excel(args.excel, sheet_name=args.file)
	

if __name__ == '__main__':
	main()
