#!/usr/bin/python
import spwd, getpass, crypt
import time
import grp
import os

import serial
import signal

import server # server listening at part 420
from twisted.internet import reactor
import threading

def keybhandler(signum, frame):
	pass # Ignore SIGINT
signal.signal(signal.SIGINT, keybhandler)
signal.signal(signal.SIGTSTP, keybhandler) # Ignore suspend (ctrl+z)

LATESTFILE = "/home/pi/latest_in" # Name of latest sesamer
SERVER_PORT = 420
ALLOWED_HOSTS = ["127.0.0.1",
                 "130.230.72.140", # coffee
                 "130.230.72.137", # battery
                 "130.230.72.137"] # cherry

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
		latest_in.close()
	
	#os.system("perl /home/pi/opensesame.pl")
	ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
	time.sleep(5)
	ser.close()
	return

def authenticate(user):
        return user in grp.getgrnam("ovi").gr_mem

def setup_server():
        def is_allowed_host(peer):
                return ALLOWED_HOSTS.count(peer.host)

        def is_allowed_user(system_type, user_info):
                return system_type == "UNIX" and authenticate(user_info)

        def allow_access(user_info):
                print "Access granted to %s" % user_info
                sesam(user_info)

        factory = server.make_server_factory(is_allowed_host, is_allowed_user, allow_access)

        reactor.listenTCP(SERVER_PORT, factory)

# TODO: move code below to twisted event loop
def interactive_session():
        while True:
                os.system("clear")
                print_motd()
                try:
                        username = login()
                except EOFError:
                        username = None

                if(username):
                        if(authenticate(username)):
                                print " You shall pass."
                                sesam(username)
                else:
                        print " Suddenly, the dungeon collapses."
                        time.sleep(5)

setup_server()

threading.Thread(target=interactive_session).start()
reactor.run()

