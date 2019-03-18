#!/usr/bin/python
# -----------------
# CashDrawer library log parser.
#  bug report: thinkroute@gmail.com
# -----------------

import sys
import os
import re
import argparse 
import pandas as pd

FILE="logs\syslog.1"
VERSION="1.1"
LNO = 0	#line no
RNO = 0	#line no
PNO = 0 #pass no
FNO = 0 #fail no

RESULT			= {}	#Test result of the record, based on the counter of open/enable
DATE 			= {}	# The date of this boot record
TIME 			= {}	# The time of this boot record
OPEN 			= {}	#OpenDevice() 	start
ENALBE 			= {}	#EnableDevice()	start
OPENDEVICE		= {}	#OpenDevice()	action
ENABLEDEVICE 	= {}	#EnableDevice()	action
ISCONNECTED 	= {}	#IsDrawerConnected()
DETAIL          = {}	#Detail logs

class LogInfo:
	def __init__(self):
		self.text 			= ""
		self.open			= 0		#[ 1]
		self.enable			= 0		#[ 2]
		self.openDevice 	= 0		#[ 1.1]
		self.enableDevice 	= 0		#[ 2.1]
		self.isDrawerConnected = 0

	def text(self):
		return (self.text)
	def connect(self):
		return (self.isDrawerConnected)
	def open(self):					# [ 1]
		return (self.open)
	def enable(self):				# [ 2]
		return (self.enable)
	def openDevice(self):			# [ 1.1]
		return (self.openDevice)
	def enableDevice(self):			# [ 2.1]
		return (self.enableDevice)
	def result(self):
		if self.open > 0:
			RESULT[RNO] = "Fail"
			return False
		elif self.enable > 0:
			RESULT[RNO] = "Fail"
			return False
		elif self.enableDevice > 0:
			RESULT[RNO] = "Fail"
			return False
		elif self.openDevice > 0:
			RESULT[RNO] = "Fail"
			return False
		elif (self.open + self.enable + self.enableDevice + self.openDevice) > 0:
			RESULT[RNO] = "Fail"
			return False
		else: 
			RESULT[RNO] = "Pass"
			return True
		
	def dellog(self):
		self.text 			= ""
		self.open			= 0		#[ 1]
		self.enable			= 0		#[ 2]
		self.openDevice 	= 0		#[ 1.1]
		self.enableDevice 	= 0		#[ 2.1]
		self.isDrawerConnected = 0

	def addlog(self, line):
		self.line = line
		self.text += line.split('ZZ: ')[1] + "\n"
		DETAIL[RNO] = self.text
		if re.search(r'IsDrawerConnected', self.line):
			self.isDrawerConnected += 1
			ISCONNECTED[RNO] = self.isDrawerConnected
		elif re.search(r'\[\s1\]',		self.line):	#[ 1]
			self.open += 1
			t = re.search('(\w*)\s*(\d+)\s(\d+):(\d+):(\d+)', self.line)
			MM = t.group(1)
			dd = t.group(2)
			hh = t.group(3)
			mm = t.group(4)
			ss = t.group(5)
			DATE[RNO] = MM + "/" + dd
			TIME[RNO] = hh + ":" + mm + ":" + ss
			OPEN[RNO] = self.open
		elif re.search(r'\[-1\]',		self.line):	#[-1]
			self.open -= 1
			OPEN[RNO] = self.open
		elif re.search(r'\[\s2\]',		self.line):	#[ 2]
			self.enable += 1
			ENALBE[RNO] = self.enable
		elif re.search(r'\[-2\]',		self.line):	#[-2]
			self.enable -= 1
			ENALBE[RNO] = self.enable
		elif re.search(r'\[\s1\.1\]',	self.line):	#[ 1.1]
			self.openDevice += 1
			OPENDEVICE[RNO] = self.openDevice
		elif re.search(r'\[-1\.1\]',	self.line):	#[-1.1]
			self.openDevice -= 1
			OPENDEVICE[RNO] = self.openDevice
		elif re.search(r'\[\s2\.1\]',	self.line):	#[ 2.1]
			self.enableDevice += 1
			ENABLEDEVICE[RNO] = self.enableDevice
		elif re.search(r'\[-2\.1\]',	self.line):	#[-2.1]
			self.enableDevice -= 1
			ENABLEDEVICE[RNO] = self.enableDevice

def isLogStart(line):
	if re.search(r'\[\s1\]', line):
		return 1
	else:
		return 0

def cli_parser():
	des = "Cashdrawer library log parser."
	epi = "Bug report: thinkroute@gmail.com"

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
		fp = open(args.file, "r")
	except IOError:
		print("ERR: target log file can't open!")
		sys.exit(1)

	global LNO	#line no
	global RNO	#line no
	global PNO	#pass no
	global FNO	#fail no
	info = LogInfo()

	for l in fp:
		LNO += 1
		if (bool(re.search(r'ZZ:', l)) != True):
			continue

		line = l.strip()
		if isLogStart(line):
			RNO += 1
			if (info.result() == True):	#pass or null
				PNO += 1	
			elif (info.result() == False):	#fail
				FNO += 1
				#print(RNO, info.open, info.openDevice, info.enable, info.enableDevice, info.connect())
				#print(info.text)
			info.dellog()
		info.addlog(line)

	sum = pd.DataFrame({"result": RESULT, "date": DATE, "time": TIME,
			"open": OPEN, "enable": ENALBE, 
			"openDevice": OPENDEVICE, "enableDevice": ENABLEDEVICE, 
			"isConnected": ISCONNECTED}) 
	
	if (args.excel == "NONE"):
		head = "LOG: " + args.file + "  LINE: " + str(LNO) + "  RECORD: " + str(RNO) + "  PASS: " + str(PNO) + "  FAIL: " + str(FNO)
		print(head)
		print(sum)
	else:
		sum['detail'] = DETAIL.values()
		sum.to_excel(args.excel, sheet_name=args.file)

if __name__ == '__main__':
	main()
