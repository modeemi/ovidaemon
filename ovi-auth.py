#!/usr/bin/python
import spwd, getpass, crypt
import time
import grp
import os

import serial
import signal

def keybhandler(signum, frame):
	pass # Ignore SIGINT
signal.signal(signal.SIGINT, keybhandler)
signal.signal(signal.SIGTSTP, keybhandler) # Ignore suspend (ctrl+z)

LATESTFILE = "/home/pi/latest_in" # Name of latest sesamer


def login():
	username = raw_input(" Username: ")
	clearpass = getpass.getpass()
	try:	
		cryptedpasswd = spwd.getspnam(username)[1]
	except: # Wrong username
		return None
	if(crypt.crypt(clearpass, cryptedpasswd) == cryptedpasswd):
		return username
def print_motd():
	motd = open("/etc/motd")
	for line in motd.readlines():
		print " "+line,
	motd.close()
	return

def sesam(username = None):
	if(username):
		latest_in = open(LATESTFILE, "w")
		latest_in.write("%s|%s" % (str(int(time.time())), username))
		latest_in.close()
	else:
		latest_in = open(LATESTFILE, "w") # Empty the file
		latest_close()
	
	#os.system("perl /home/pi/opensesame.pl")
	ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
	time.sleep(5)
	ser.close()
	return

while True:
	os.system("clear")
	print_motd()
	try:
		username = login()
	except EOFError:
		username = None

	if(username):
		members = grp.getgrnam("ovi")[3]
		if(username in members):
			print " You shall pass."
			sesam(username)
	else:
		print " Suddenly, the dungeon collapses."
		time.sleep(5)
