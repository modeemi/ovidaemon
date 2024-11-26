#!/usr/bin/env python

import grp
import serial
import socket
import time

LATESTFILE = "/home/pi/latest_in" # Name of latest sesamer
LOGFILE = "/home/pi/ovi_log" # Name of latest sesamer
LOCAL_PORT = 420
IDENTD_PORT = 113

ALLOWED_HOSTS = ["127.0.0.1",
                 "130.230.72.140", # coffee
                 "130.230.72.137", # battery
                 "130.230.72.149", # pepper
                 "130.230.72.137"] # cherry

def sesam(username = None):
    if(username):
        latest_in = open(LATESTFILE, "w")
        latest_in.write(f'{int(time.time())}|{username}')
        latest_in.close()
        logfile_in = open(LOGFILE, "a")
        logfile_in.write(f'{int(time.time())}|{username}')
        logfile_in.write("\n")
        logfile_in.close()
    else:
        latest_in = open(LATESTFILE, "w") # Empty the file
        latest_in.close()

    ser = serial.Serial("/dev/ttyUSB0", 9600, timeout=1)
    time.sleep(5)
    ser.close()
    return


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((socket.gethostname(), LOCAL_PORT))
server_socket.listen(5)
while True:
    # Set up server socket
    # accept connections from outside
    (client_socket, (peer_addr, peer_port)) = server_socket.accept()
    client_socket.sendall(b'Kerberos bites you in the buttocks\n')
    print(f'Connected {client_socket}, {peer_addr}, {peer_port}')
    if peer_addr not in ALLOWED_HOSTS:
        print('Attempted to connect from invalid host {peer_addr}')
        fail(client_socket)
    else:
        # Get ident
        ident_socket = socket.create_connection((peer_addr, IDENTD_PORT))
        ident_socket.sendall(f'{peer_port},{LOCAL_PORT}\n'.encode('utf-8'))
        answer = ident_socket.recv(4096)
        ident = answer.decode('utf-8').rstrip().split(':')
        if len(ident) != 4:
            fail(client_socket)
        if len(ident) == 4:
            (_addr, _userid, _unix, username) = ident
            group = grp.getgrnam('ovi')
            if username in group.gr_mem:
                print(f'Access granted for {username}@{peer_addr}')
                _ = client_socket.recv(4096)
                client_socket.sendall(b'You shall live to see another day\n')
                sesam(username)
            else:
                print(f'Access denied for user {username}@{peer_addr}')
        else:
            print(f'Could not parse answer from identd on {peer_addr}:{IDENTD_PORT}: {answer}')
    client_socket.close()
serversocket.close()
