import socket
#Hardcoded server ip, port
SERVER_IP = "10.0.1.2"
DPORT = 12346
QUEUE_LENGTH = 5

# Create a socket to listen at the specified ip, port and listen with the specified queue length
def getListeningSocket(server_IP, listening_port, queue_length):
  s = socket.socket()
  print ("Socket successfully created")
  s.bind((server_IP, listening_port))
  print ("socket binded to %s" %(listening_port))
  s.listen(queue_length)
  print ("socket is listening")
  return s
# Check if we are the Host mentioned in the request, returns True and the content of the request if so, else fals
def validateRequestHost(recvmsg):
  lines = recvmsg.split('\r\n')
  if len(lines)<2 or lines[1]!='Host: '+SERVER_IP:
    return False, None
  return True, lines[0]
# Check if HTTP/1.1 is mentioned in the request
def validateProtocol(protocol):
  if protocol != 'HTTP/1.1':
    return False
  return True
# Handles the GET Request
def handleGET(c, d, url):
  #If the request was "GET /assignment1?key=... HTTP/1.1\r\nHost: SERVER_IP\r\n\r\n"
  # Here the url is "/assignment1?key=..."
  print('Received a GET Request')
  urlList = url.split('?')
  if len(urlList)!=2:
    # We need /...?... as the format here
    c.sendall("HTTP/1.1 400 Bad Request\r\nCannot understand the GET request\r\n\r\n".encode())
    return
  if urlList[0] != '/assignment1':
    c.sendall("HTTP/1.1 404 Not Found\r\nCannot find "+urlList[0]+"\r\n\r\n".encode())
    return
  getReqContentList = urlList[1].split('=')
  if len(getReqContentList) != 2 or getReqContentList[0]!='key':
    #We want key=SMTH as the format here
    c.sendall("HTTP/1.1 400 Bad Request\r\nCannot understand the GET request\r\n\r\n".encode())
    return
  key = getReqContentList[1]
  if(key in d):
    # Requested object is returned
    c.sendall('HTTP/1.1 200 OK\r\n'+d[key]+'\r\n\r\n'.encode())
  else:
    # Key is not in the list
    c.sendall('HTTP/1.1 404 Not Found\r\nKey: '+key+' Not Found\r\n\r\n'.encode()) 
# Handles the PUT Request
def handlePUT(c, d, url):
  # PUT /assignment1/key/val HTTP/1.1\r\nHost:SERVER_IP\r\n\r\n
  print('Received a PUT Request')
  urlList = url.split('/')
  if len(urlList)!=4:
    # We need /assignment1/key/val as the format here
    c.sendall("HTTP/1.1 400 Bad Request\r\nCannot understand the POST request\r\n\r\n".encode())
    return
  if urlList[0] or urlList[1] != 'assignment1':
     #Client is requesting something other than /assignment1, not found
    c.sendall("HTTP/1.1 404 Not Found\r\nCannot find "+urlList[1]+"\r\n\r\n".encode())
    return
  key = urlList[2]
  val = urlList[3]
  if key in d:
    d[key] = val
    print('For key :'+urlList[2]+', value is updated to '+urlList[3])
    #If the target resource does have a current representation and that representation is successfully modified in accordance with the state of the enclosed representation, then the origin server must send either a 200 (OK) or a 204 (No Content) response to indicate successful completion of the request. - Mozila MDN Web docs, we have chosen 200 OK
    c.sendall("HTTP/1.1 200 OK\r\nFor key:"+urlList[2]+", value is updated to "+urlList[3]+"\r\n\r\n".encode())
  else:
    d[key] = val
    print(urlList[2]+','+urlList[3]+' is inserted into the dict')
    #If the target resource does not have a current representation and the PUT request successfully creates one, then the origin server must inform the user agent by sending a 201 (Created) response. - Mozilla MDN Web Docs
    c.sendall("HTTP/1.1 201 Created\r\nInserted "+urlList[2]+","+urlList[3]+" into the dict\r\n\r\n".encode())          
# Handles the DELETE Request
def handleDELETE(c, d, url):
  #DELETE /assignment1/key HTTP/1.1\r\nHost: SERVER_IP\r\n\r\n
  print('Received a DELETE Request')
  urlList = url.split('/')
  if len(urlList)!=3:
    c.sendall("HTTP/1.1 400 Bad Request\r\nCannot understand the request\r\n\r\n".encode())
    return
  if urlList[0] or urlList[1] != 'assignment1':
    c.sendall("HTTP/1.1 404 Not Found\r\nCannot find "+urlList[1]+"\r\n\r\n".encode()) #Client is requesting something other than /assignment1, not found
    return
  key = urlList[2]
  if key in d:
    del d[key]
    print('Deleted key: '+urlList[2])
    #  If a DELETE method is successfully applied, there are several response status codes possible:
      # A 202 (Accepted) status code if the action will likely succeed but has not yet been enacted.
      # A 204 (No Content) status code if the action has been enacted and no further information is to be supplied.
      # A 200 (OK) status code if the action has been enacted and the response message includes a representation describing the status.
    # - From Mozilla MDN Web docs. Here we have chosen 200 OK and send that we have deleted that key
    #Send that you have successfully deleted
    c.send("HTTP/1.1 200 OK\r\nDeleted key: "+urlList[2]+"\r\n\r\n".encode())
  else:
    # Key not found in Dict
    c.sendall("HTTP/1.1 404 Not Found\r\nCannot find key: "+urlList[2]+" in the dict\r\n\r\n".encode())           
def handleRequest(c, d, recvmsg):
  validity, requestContent = validateRequestHost(recvmsg)
  if not validity:
    # Bad request, we want atleast GET/PUT/DELETE etc on one line and the Host:=SERVER_IP on the next
    c.sendall("HTTP/1.1 400 Bad Request\r\nHost field missing or incorrect\r\n\r\n".encode())
    return
  requestContentList = requestContent.split(' ')
  if len(requestContentList) != 3:
    c.sendall("HTTP/1.1 400 Bad Request\r\nCannot understand the request\r\n\r\n".encode())
    return
  requestType, url, protocol = requestContentList
  if not validateProtocol(protocol):
    c.sendall("HTTP/1.1 505 HTTP Version Not Supported\r\n Only HTTP/1.1 is supported\r\n\r\n".encode())
  if requestType == 'GET':
    handleGET(c, d, url)
  elif requestType == 'PUT':
    handlePUT(c, d, url)
  elif requestType == 'DELETE':
    handleDELETE(c, d, url)
  else:
    #Doesn't start with GET/PUT/DELETE, So, server doesn't understand the 
    c.sendall("HTTP/1.1 400 Bad Request\r\n Cannot Understand the type of Request\r\n\r\n".encode())
def main():
  #Create the dict
  d = dict()
  #Create a socket to listen
  s = getListeningSocket(SERVER_IP, DPORT, QUEUE_LENGTH)
  #Server Loop
  while True:
    c, addr = s.accept()
    print ('Got connection from', addr )
    recvmsg = c.recv(1024).decode()
    #Printing for observation and debugging
    print('Server received '+recvmsg)
    # Parse the request and respond
    handleRequest(c, d, recvmsg)
    # Close the connection with the client
    c.close()

if __name__ == '__main__':
  main()