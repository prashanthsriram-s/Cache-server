import socket
#Hardcoded server details of h2
SERVER_IP = "10.0.1.2"
PORT = 12346
# Functions to establish a connection
def getSocket():
    s = socket.socket()
    s.connect((SERVER_IP, PORT))
    return s
def GET(key):
    s = getSocket()
    s.sendall('GET /assignment1?key='+key+' HTTP/1.1\r\nHost: '+SERVER_IP+'\r\n\r\n'.encode())
    recvmsg = s.recv(1024).decode()
    s.close()
    return recvmsg
def PUT(key, val):
    s = getSocket()
    s.sendall('PUT /assignment1/'+key+'/'+val+' HTTP/1.1\r\nHost: '+SERVER_IP+'\r\n\r\n'.encode())
    recvmsg = s.recv(1024).decode()
    s.close()
    return recvmsg
def DELETE(key):
    s = getSocket()
    s.sendall('DELETE /assignment1/'+key+' HTTP/1.1\r\nHost: '+SERVER_IP+'\r\n\r\n'.encode())
    recvmsg = s.recv(1024).decode()
    s.close()
    return recvmsg

def main():
    #Loop to Prompt user to select GET/PUT/DELETE/EXIT
    while(True):
        choice = int(input("1.GET, 2.PUT, 3.DELETE, 4.EXIT\n"))
        if(choice==1):
            key = raw_input("Enter key to GET\n")
            print(GET(key))    
        elif(choice==2):
            key, val =  raw_input("Enter key <space> value\n").split()
            print(PUT(key, val))
        elif(choice==3):
            key = raw_input("Enter key to DELETE\n")
            print(DELETE(key))
        else:
            break

if __name__ == '__main__':
    main()