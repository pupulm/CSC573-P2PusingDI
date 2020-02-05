import socket
import threading
#import shlex
import os
import platform
import time
import pickle
import sys

wd = os.getcwd()
directory = wd + ""
os.chdir(directory)

RFC_files = []
current_path = os.getcwd() + "//RFCs"
host_name = socket.gethostname()

# SERVER_NAME = ''
HOST = input("Enter the hostname or IP address of the registration server:")
SERVER_PORT = input("Enter the port number on which registration server is listening(should be between 65400 and 65500):")  # eg: 65401
Cookieval = None
# HOST = socket.gethostbyname(socket.gethostname())
listening_port = input("Enter the port number on which the peer will receive connections (should be between 65400 and 65500):")  # eg: 65402

def returnfiles():  # function to find the directory path where RFC files will be present to download from
    for file in os.listdir(current_path):
        if file.endswith(".txt"):
            RFC_files.append(file)


def merge(local_rfc, remote_rfc):  # function to merge the RFC indices which is locally present and is with remote peer
    for key, value in remote_rfc.items():
        if key not in local_rfc:
            local_rfc[key] = value
        else:
            local_rfc[key] = local_rfc[key] + value
    return local_rfc


def local_RFC_index():  # function to define RFC index, it has RFC number, title, peer name and TTL
    RFC_Index = {}
    for file in RFC_files:
        file.replace(".txt", "")
        rfc_info = file.split("_")
        rfc_no = rfc_info[0]
        rfc_title = rfc_info[1]
        rfc_dic = {
            "RFC Title": rfc_title,
            "peer name": host_name,
            "TTL": 7200
        }
        if not RFC_Index.get(rfc_no):
            RFC_Index[rfc_no] = [rfc_dic]
        else:
            RFC_Index.get(rfc_no).append(rfc_dic)
    return RFC_Index


def ServerMain(socket, addr, local_RFC):  #function definition for server peer
    global FilePath
    global HOST
    global OS
    msg = socket.recv(1024)
    message = str.split(str(msg), " ")
    print(msg)
    if message[0] == "b'GET":
        if message[1] == 'RFC-INDEX':  # if requested message is RFC-INDEX, respond with RFC-index
            print("Sending RFC-INDEX to %s.....\n" %(str(addr)))
            response = pickle.dumps(local_RFC)
            socket.send(response)
            print("Finished sending RFC-Index to %s\n" %(str(addr)))
        msg = socket.recv(1024)
        print(msg)
        message = str.split(str(msg), " ")
        if message[0] == "b'CLOSE":  # to close the socket
            socket.close()
        elif message[0] == "b'GET":  # to send the requested RFC file to peer client
            print("Sending requested RFC to %s......\n" %str(addr))
            response = "P2P-DI/1.0 200 OK(%^&***)Host: " + HOST
            rfc_title = local_RFC[message[2]][0]['RFC Title']
            filename = "{0}_{1}".format(str(message[2]), rfc_title)
            current_path1 = os.getcwd() + "/RFCs"
            if os.path.isfile(current_path1 + "/" + filename):
                with open(current_path1 + "/" + filename, "r") as f:
                    size = os.path.getsize(current_path1 + "/" + filename)
                    filedata = f.read()
                    filedata1 = bytes((filedata), 'utf-8')
                    socket.send(filedata1)
                print("Finished sending RFC %s to %s\n" % (message[2], str(addr)))
            socket.close()


def ServerModule(local_RFC):  #function to create peer server section and bind it
    global HOST
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((socket.gethostbyname('localhost'), int(listening_port)))

    server_socket.listen(25)
    print("Starting server.....\n")
    while True:
        client_socket, addr = server_socket.accept()
        print("Connection from: " + str(addr))
        MainThread = threading.Thread(target=ServerMain, args=(client_socket, addr, local_RFC))
        MainThread.start()


def display(dict_peer_index):  # to display the peer index returned by Registration server
    print("Details of all peers is as follows: ")
    print("Hostname\tCookie\tActive Flag\tTTL\tListening_Port\tMost Recent Registration\tConnected Count\n")
    for Cookie in dict_peer_index.keys():
        if dict_peer_index[Cookie]["Active_flag"] == 1:
            a = "Active"
            print("%s\t%s\t%s\t\t%d\t%s\t\t%s\t%s\n" % (
            dict_peer_index[Cookie]["hostname"], Cookie, a, dict_peer_index[Cookie]["TTL"],
            dict_peer_index[Cookie]["port"], dict_peer_index[Cookie]["Recently_active"], dict_peer_index[Cookie]["Connected_count"]))
        else:
            a = "Inactive"
            print("%s\t%s\t%s\t%d\t%s\t\t%s\t\t\t%s\n" % (
            dict_peer_index[Cookie]["hostname"], Cookie, a, dict_peer_index[Cookie]["TTL"],
            dict_peer_index[Cookie]["port"], dict_peer_index[Cookie]["Recently_active"], dict_peer_index[Cookie]["Connected_count"]))




register = input("Do you want to Register?(Y/N) ")  # call to register peer with registration server
if (register == 'Y'):

    if os.path.isfile("Cookie.txt"):  # if cookie is present, the connection is made with cookie
        with open("Cookie.txt", "r") as f:
            Cookieval = f.read()
    else:
        Cookieval = None

    s = socket.socket()
    s.connect((HOST, int(SERVER_PORT)))

    if Cookieval != None:  # carry cookie if cookie is present
        message = "REGISTER P2P-DI/1.0 Host: " + HOST + " Cookie: " + str(Cookieval) + " Port: " + str(
            listening_port) + " "
    else:
        message = "REGISTER P2P-DI/1.0 Host: " + HOST + " Port: " + str(listening_port) + " "
    s.send(bytes((message), encoding='utf-8'))
    rep = s.recv(1024)
    print(rep)
    reply = str.split(str(rep), " ")
    if reply[1] == "200" and reply[2] == "OK":
        print("Peer %s registered with RS\n" % (str(s.getsockname())))
        Cookieval = str(reply[4])
        f = open("Cookie.txt", "w+")
        f.write(Cookieval)
        f.close()
rfc_no = input("Enter RFC Number ")  # requesting the RFC Number that needs to be downlaoded

returnfiles()
local_RFC = local_RFC_index()
MainThread = threading.Thread(target=ServerModule, args=(local_RFC,))
MainThread.start()


f = 0  # to check if RFC requested is present locally or not
for keys in local_RFC.keys():
    if (rfc_no == keys):
        f = f + 1
        break
if (f == 0):
    print("RFC not found on local host ")
else:
    print("RFC found on local host ")

print("Do you want to LEAVE, KEEP ALIVE, PQUERY")  # call to allow user what operation is to be performed, options are Leave, peer query or keep alive
input1 = input("1. LEAVE\n2.KEEP ALIVE\n3.PQUERY\n")
if input1 == "1":
    message = "LEAVE P2P-DI/1.0 Host: " + HOST + " Cookie: " + str(Cookieval) + " " + str(listening_port) + " "
elif input1 == "2":
    message = "KEEP-ALIVE P2P-DI/1.0 Host: " + HOST + " Cookie: " + str(Cookieval) + " " + str(listening_port) + " "
elif input1 == "3":
    message = "PQUERY P2P-DI/1.0 Host: " + HOST + " Cookie: " + str(Cookieval) + " " + str(listening_port) + " "
s.send(bytes((message), encoding='utf-8'))
rep = s.recv(4096)
print(str(rep))
# print(rep)
reply = str.split(str(rep), " ")
if reply[1] == "300" and reply[2] == "OK":
    print("Leaving the peer network...BYE :(")
elif reply[1] == "500" and reply[2] == "OK":
    print("Keep alive successful ")
elif reply[1] == "400" and reply[2] == "OK":
    rep1 = s.recv(4096)
    dict_peer_index = pickle.loads(rep1)
    print("Peer information received ")
    print()
    display(dict_peer_index)
    for Cookie in dict_peer_index.keys():
        if int(dict_peer_index[Cookie]["Active_flag"]) == 1 and int(dict_peer_index[Cookie]["port"])!=int(listening_port):
            HOST = dict_peer_index[Cookie]["hostname"]
            PORT = int(dict_peer_index[Cookie]["port"])
            s1 = socket.socket()
            s1.connect((HOST, PORT))
            message = "GET RFC-INDEX P2P-DI/1.0 Host: " + HOST
            s1.send(bytes((message), encoding='utf-8'))
            rep = s1.recv(409600)
            r = pickle.loads(rep)
            f = 0
            for keys in r.keys():
                if (rfc_no == keys):
                    f = f + 1
                    break
            if (f == 0):  # if requested RFC Number does not match with any number in RFC index
                print("RFC not found on remote host ")
            else:
                print("RFC found on remote host ")
            dict_local = merge(local_RFC, r)  # call to merge local and remote RFC index
            if (f != 0):
                message = "GET RFC " + str(rfc_no) + " P2P-DI/1.0 Host: " + HOST
                s1.send(bytes((message), encoding='utf-8'))
                filename = str(rfc_no) + ".txt"
                rep = s1.recv(2706000)
                f = open(filename, "w+")
                f.write(str(rep))
                f.close()
                print("RFC %s successfully downloaded!\n" % (rfc_no))
            elif (f == 0):
                message = "CLOSE CONNECTION P2P-DI/1.0 HOST: " + HOST
            s1.close()

print("Do you want to LEAVE, KEEP ALIVE, PQUERY")
input1 = input("1. LEAVE\n2.KEEP ALIVE\n3.PQUERY\n")
if input1 == "1":
    message = "LEAVE P2P-DI/1.0 Host: " + HOST + " Cookie: " + str(Cookieval) + " " + str(listening_port) + " "
elif input1 == "2":
    message = "KEEP-ALIVE P2P-DI/1.0 Host: " + HOST + " Cookie: " + str(Cookieval) + " " + str(listening_port) + " "
elif input1 == "3":
    message = "PQUERY P2P-DI/1.0 Host: " + HOST + " Cookie: " + str(Cookieval) + " " + str(listening_port) + " "
s.send(bytes((message), encoding='utf-8'))
rep = s.recv(4096)
print(str(rep))
# print(rep)
reply = str.split(str(rep), " ")
if reply[1] == "300" and reply[2] == "OK":
    print("Leaving the peer network...BYE :(")
elif reply[1] == "500" and reply[2] == "OK":
    print("Keep alive successful ")
elif reply[1] == "400" and reply[2] == "OK":
    rep1 = s.recv(4096)
    dict_peer_index = pickle.loads(rep1)
    print("Peer information received ")
    print()
    display(dict_peer_index)
    for Cookie in dict_peer_index.keys():
        PORT=int(dict_peer_index[Cookie]["port"])
        if int(dict_peer_index[Cookie]["Active_flag"]) == 0 and PORT != int(listening_port):
            print("No Active Peers!!!")
    s1.close()

