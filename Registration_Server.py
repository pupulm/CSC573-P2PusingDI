import time
#import datetime
import socket
import threading
import os
#import platform
#import sys
import random
import pickle

wd = os.getcwd()
directory = wd+""
FilePath=directory
dict_peer_index={}


# function to calculate the TTL for each registered peer and decrement it every second
def timer_function(Cookie):
    while dict_peer_index[Cookie]["TTL"]!=0:
        dict_peer_index[Cookie]["TTL"]=dict_peer_index[Cookie]["TTL"]-1
        time.sleep(1)

''' this function to create peer index which contains the unique cookie, hostname of the connected peer, port number in use by the peer,'''
'''whether the peer is active or not, TTL, most recent time when the connected peer was active and the number of times peer connected in last 30 days'''


def peer_info(Cookie,hostname,port,Active_flag,connected_count):
    dict_peer_index[Cookie]={}
    dict_peer_index[Cookie]["hostname"]=hostname
    dict_peer_index[Cookie]["port"]=port
    dict_peer_index[Cookie]["Active_flag"]=Active_flag
    dict_peer_index[Cookie]["TTL"]=7200
    dict_peer_index[Cookie]["Recently_active"]=time.ctime()
    dict_peer_index[Cookie]["Connected_count"] = connected_count


# To display the peers that are connected to the registration server in a human readable format
def display():
    print()
    print("Details of all peers is as follows: ")
    print()
    print ("Hostname\tCookie\tActive Flag\tTTL\tListening_Port\tMost Recent Registration\tConnected Count\n")
    for Cookie in dict_peer_index.keys():

        if dict_peer_index[Cookie]["Active_flag"]==1:
            a= "Active"
            print ("%s\t%s\t%s\t\t%d\t%s\t\t%s\t%s\n" %(dict_peer_index[Cookie]["hostname"], Cookie, a,dict_peer_index[Cookie]["TTL"] , dict_peer_index[Cookie]["port"], dict_peer_index[Cookie]["Recently_active"], dict_peer_index[Cookie]["Connected_count"]))
        else:
            a= "Inactive"
            print ("%s\t%s\t%s\t%d\t%s\t\t%s\t\t\t%s\n" %(dict_peer_index[Cookie]["hostname"], Cookie, a,dict_peer_index[Cookie]["TTL"] , dict_peer_index[Cookie]["port"], dict_peer_index[Cookie]["Recently_active"], dict_peer_index[Cookie]["Connected_count"]))


# Function to define all the response that are provided by the registration server on a request
def ServerMain(connectionSocket,addr):
    global t1
    global FilePath
    msg = connectionSocket.recv(2048)
    msg1 = str.split(str(msg)," ")
    print()
    print("Message from peer ")
    #print(msg)
    #print(msg1[0])
    if msg1[0] == r"b'REGISTER":  # this is register a peer with the registration server for the first time, it generates a cookie for the requesting peer
        if msg1[4] != "Cookie:":
            print("Registering the Client...\n")
            hostname = addr[0]
            list_port = msg1[5]
            peeraddr = connectionSocket.getpeername()
            Cookie = random.randint(0,100)
            connected_count = 1  # number of times a peer connected in last 30 days
            reply = "P2P-DI/1.0 200 OK Cookie: "+str(Cookie)+" "
            peer_info(Cookie,hostname,list_port,1,connected_count)
            a=bytes(reply,'utf-8')
            connectionSocket.send(a)
            print("reply sent")
            display()
            t1=threading.Thread(target=timer_function, args=(Cookie,))
            t1.start()
    

        elif msg1[4]=="Cookie:":  # if a peer comes back with an existing cookie, then new cookie is not generated. Existing cookie is used to make the connection.
            Cookie=int(msg1[5])
            hostname=addr[0]
            dict_peer_index[Cookie]["Active_flag"]=1
            dict_peer_index[Cookie]["Recently_active"]=time.ctime()
            reply= "P2P-DI/1.0 200 OK Cookie: "+str(Cookie)+" Host: "+hostname+" "
            a=bytes(reply,'utf-8')
            threading.Thread(target=timer_function, args=(Cookie)).start()
            connectionSocket.send(a)


    msg = connectionSocket.recv(2048)
    msg1 = str.split(str(msg)," ")
    print()
    print("Message from peer ")
    print(msg)

    if msg1[0] == r"b'LEAVE":
        c=str(addr)
        print("Setting Peer %s to 'Inactive'...\n"%(c))
        hostname = addr[0]
        Cookie=int(msg1[5]) 
        dict_peer_index[Cookie]["Active_flag"]=0
        dict_peer_index[Cookie]["TTL"]=0
        reply = "P2P-DI/1.0 300 OK Host:"+hostname
        a=bytes(reply,'utf-8')
        connectionSocket.send(a)
        display()
        connectionSocket.close()
        
        
    if msg1[0] == r"b'PQUERY" :
        print("Sending Peer-Index Table")
        hostname = addr[0]
        reply = "P2P-DI/1.0 400 OK Host:"+hostname
        a=bytes(reply,'utf-8')
        connectionSocket.send(a)
        peer_table = pickle.dumps(dict_peer_index)
        connectionSocket.send(peer_table)
        
        msg = connectionSocket.recv(2048)
        msg1 = str.split(str(msg)," ")
        print()
        print("Message from peer ")
        print(msg)

        if msg1[0] == r"b'LEAVE":
            c=str(addr)
            print("Setting Peer %s to 'Inactive'...\n"%(c))
            hostname = addr[0]
            Cookie=int(msg1[5]) 
            dict_peer_index[Cookie]["Active_flag"]=0
            dict_peer_index[Cookie]["TTL"]=0
            reply = "P2P-DI/1.0 300 OK Host:"+hostname
            a=bytes(reply,'utf-8')
            connectionSocket.send(a)
            display()
            connectionSocket.close()
            
        if msg1[0] == r"b'PQUERY" :
            print("Sending Peer-Index Table")
            hostname = addr[0]
            reply = "P2P-DI/1.0 400 OK Host:"+hostname
            a=bytes(reply,'utf-8')
            connectionSocket.send(a)
            peer_table = pickle.dumps(dict_peer_index)
            connectionSocket.send(peer_table)
            connectionSocket.close()

        if msg1[0] == r"b'KEEP-ALIVE" :
            print("KEEP ALIVE!!!!!")
            hostname = addr[0]
            dict_peer_index[Cookie]["TTL"]=7200
            reply = "P2P-DI/1.0 500 OK Host:"+hostname
            a=bytes(reply,'utf-8')
            threading.Thread(target=timer_function, args=(Cookie)).start()
            connectionSocket.send(a)
            connectionSocket.close()

    if msg1[0] == r"b'KEEP-ALIVE" :
        print("KEEP ALIVE!!!!!")
        hostname = addr[0]
        dict_peer_index[Cookie]["TTL"]=7200
        reply = "P2P-DI/1.0 500 OK Host:"+hostname
        a=bytes(reply,'utf-8')
        threading.Thread(target=timer_function, args=(Cookie)).start()
        connectionSocket.send(a)



# Creating registration server and binding its port number
ServerSocket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
ServerSocket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
PORT = input("Enter the port number to be used by registration server (should be between 65400 and 65500):") # this is only for the purpose of this project but any valid port number can be provide
ServerSocket.bind( ( '', int(PORT) ) )
ServerSocket.listen(1)
print("Registration server running on port: %s"%PORT)
print("Waiting for connections......")


while True:
    connectionSocket,addr = ServerSocket.accept()
    print ("Connection made with: " + str(addr) + "\n")
    threading.Thread(target=ServerMain,args=(connectionSocket,addr)).start()



