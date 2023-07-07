# Client ip: 10.0.1.1
# Our ip: 10.0.1.2
# Server ip: 10.0.1.3
# Cache server listens in port 64321
# Server listens in port 12346
# Approach for caching: Cache server should store the data it GETs from the server, But we don't want to store infinitely and would want to have a max N items we store and then to cache another item, we delete the least recently used(LRU) item from our cache. To do this, we use the following:
# 1. a dict 'cache' to store the key, val we get from the GET requests
# 2. a doubly linked list 'DLL' storing the recent keys we have received requests for from the client, stored in that order
# 3. a dict 'locationInDLL' having (key, reference to this key in the DLL) so that we can use this to update the linked list whenever this key is accessed. 
# General Procedure:
# PUT Requests are just copied over to the server and the responses are copied over to the client
# For GET Requests, First check if the key is in our cache:
#   If there:
#           1. Delete key from DLL and put it in the front of the DLL
#           2. Return the val
#   Else:
#           1. Fetch val from server
#           2. If size(cache) < MAX_SAVED:
#               a. add it to cache
#               b. Add this key to the front of the DLL 
#               c. Return val to client
#           2. Else:
#               a. Delete from cache the key at the end of the DLL
#               b. Delete the key at the end of the DLL from the DLL
#               c. Add this key to cache and to the front of the DLL
#               d. Return val to client
import socket, copy
class Node:
    def __init__(self, key):
        self.prev = None
        self.next = None
        self.key = key
class DLL:
    def __init__(self):
        self.head_sentinel = Node(None)
        self.tail_sentinel = Node(None)
    def empty(self):
        return self.head_sentinel.next is None
    def insertAtHead(self, key):
        node = Node(key=key)
        if self.empty():
            node.prev = self.head_sentinel
            node.next = self.tail_sentinel
            self.head_sentinel.next = node
            self.tail_sentinel.prev = node
        else:
            node.prev = self.head_sentinel
            node.next = self.head_sentinel.next
            self.head_sentinel.next = node
            node.next.prev = node
        return node
    def first(self):
        return self.head_sentinel.next
    def remove(self, node): #node is assumed not to be the first node, node.prev is not head_sentinel
        if self.empty():
            return
        if self.head_sentinel.next is node and self.head_sentinel.prev is node:
            # Single node case
            self.head_sentinel.next = None
            self.tail_sentinel.prev = None
        else:

            node.prev.next = node.next
            node.next.prev = node.prev
            # This wouldn't be correct if node was the first node, then hs.next be the ts, instead of being None and vice versa
        del node
    def putFirst(self, node):
        if not (self.first() is node):
            save_key = node.key
            self.remove(node)
            self.insertAtHead(save_key)
        # else do nothing
    def removeLast(self):
        self.remove(self.tail_sentinel.prev)
    def printAll(self):
        print('Printing: ')
        if self.empty():
            return
        node = copy.deepcopy(self.head_sentinel.next)
        while node.next is not None:
            print(node.key)
            node = node.next
#Hardcoded:
CACHE_IP = '10.0.1.2'
CACHE_PORT = 64321
SERVER_PORT = 12346
SERVER_IP = '10.0.1.3'
QUEUE_LENGTH = 5
#For Caching
MAX_SAVED = 5
# Helper fns When cache needs to act as a client
def getSocket(serverIP, serverPORT):
    s = socket.socket()
    s.connect((serverIP, serverPORT))
    return s
def GET(key, serverIP = SERVER_IP, serverPort = SERVER_PORT):
  s = getSocket(serverIP=serverIP, serverPORT=serverPort)
  s.sendall('GET /assignment1?key='+key+' HTTP/1.1\r\nHost: '+SERVER_IP+'\r\n\r\n'.encode())
  recvmsg = s.recv(1024).decode()
  s.close()
  return recvmsg
def PUT(key, val, serverIP = SERVER_IP, serverPort = SERVER_PORT):
  if serverIP is None and serverPort is None:
    s = getSocket()
  else:
    s = getSocket(serverIP=serverIP, serverPORT=serverPort)
  s.sendall('PUT /assignment1/'+key+'/'+val+' HTTP/1.1\r\nHost: '+SERVER_IP+'\r\n\r\n'.encode())
  recvmsg = s.recv(1024).decode()
  s.close()
  return recvmsg

# When cache needs to act as the server
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
  if len(lines)<2 or lines[1]!='Host: '+CACHE_IP:
    return False, None
  return True, lines[0]
# Check if HTTP/1.1 is mentioned in the request
def validateProtocol(protocol):
  if protocol != 'HTTP/1.1':
    return False
  return True

def handleCacheHit(c, cache, dll, locationInDLL, key):
  print('Cache Hit! Value in cache for this key is '+cache[key])
  # Make this the most recently used key
  dll.putFirst(node=locationInDLL[key])
  # Update position of the key in the DLL in the location dict
  locationInDLL[key] = dll.head_sentinel.next
  c.sendall('HTTP/1.1 200 OK\r\n'+cache[key]+'\r\n\r\n'.encode())

def handleCacheMiss(c, cache, dll, locationInDLL, key):
  print('Cache miss, fetching from main server...')
  # First get the value from the server
  msgrecved = GET(key)
  print('Received the following from the main server: '+msgrecved)
  # Now, parse this message
  # Msg format: HTTP/1.1 XXX RESPONSE CODE TEXT\r\n SOMETHING \r\n\r\n
  msglines = msgrecved.split('\r\n')
  if len(msglines) < 2:
    c.sendall('HTTP/1.1 502 Bad Gateway\r\n Received Invalid response from main server\r\n\r\n'.encode())
    return
  firstLine = msglines[0].split(' ')
  #  firstline like [HTTP/1.1, XXX, RESPONSE, CODE, TEXT]
  if len(firstLine)<2:
    c.sendall('HTTP/1.1 502 Bad Gateway\r\n Received Invalid response from main server\r\n\r\n'.encode())
    return
  if firstLine[1] not in ['200', '404']:
    c.sendall('HTTP/1.1 502 Bad Gateway\r\n Received Invalid response from main server\r\n\r\n'.encode())
    return
  elif firstLine[1] == '404':
    if msglines[1] == 'Key: '+key+' Not Found':
      c.sendall('HTTP/1.1 404 Not Found\r\nKey Not Found\r\n\r\n'.encode())
    else:
      c.sendall("HTTP/1.1 404 Not Found\r\nCannot find assignment1\r\n\r\n".encode())
    return
  print('Got value successfully from the main server')
  val = msglines[1]
  # val is the value returned from the main server
  if len(cache) < MAX_SAVED:
    cache[key] = val
    print('Cached '+key)
    dll.insertAtHead(key)
    locationInDLL[key] = dll.head_sentinel.next
    c.sendall(msgrecved.encode())
  else:
    # Delete from cache the LRU key
      del cache[dll.tail_sentinel.prev.key]
      del locationInDLL[dll.tail_sentinel.prev.key]
      dll.removeLast()
      print('Removed LRU key from Cache')
      cache[key] = val
      print('Cached '+key)
      dll.insertAtHead(key)
      locationInDLL[key] = dll.head_sentinel.next
      c.sendall(msgrecved.encode())   
# def handleWrongURLGET(c, url):
#   s = getSocket(SERVER_IP, SERVER_PORT)

#   pass

# Handles the GET Request
def handleGET(c, cache, dll, locationInDLL, url):
  #If the request was "GET /assignment1?key=... HTTP/1.1\r\nHost: CACHE_IP\r\n\r\n"
  # Here the url is "/assignment1?key=..."
  print('Received a GET Request')
  urlList = url.split('?')
  if len(urlList)!=2:
    # We need /...?... as the format here
    c.sendall("HTTP/1.1 400 Bad Request\r\nCannot understand the GET request\r\n\r\n".encode())
    return
  if urlList[0] != '/assignment1':
    c.sendall("HTTP/1.1 404 Not Found\r\nCannot find "+urlList[0]+"\r\n\r\n".encode())
    # Future maybe implement
    # # We do not cache for other urls than /assignment1. So, we just forward it and get back the request
    # handleWrongURLGET(c, url)
    
    return
  getReqContentList = urlList[1].split('=')
  if len(getReqContentList) != 2 or getReqContentList[0]!='key':
    #We want key=SMTH as the format here
    c.sendall("HTTP/1.1 400 Bad Request\r\nCannot understand the GET request\r\n\r\n".encode())
    return
  key = getReqContentList[1]
  if(key in cache):
    # Cache hit
    handleCacheHit(c, cache, dll, locationInDLL, key)
  else:
    # Cache miss
    handleCacheMiss(c, cache, dll, locationInDLL, key)

# Handles the PUT Request
def handlePUT(c, url):
  # PUT /assignment1/key/val HTTP/1.1\r\nHost:CACHE_IP\r\n\r\n
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
  # Now, PUT this to the server and redirect the response to the client
  return_msg = PUT(key, val)
  c.sendall(return_msg.encode())

def handleRequest(c, cache, dll, locationInDLL, recvmsg):
  validity, requestContent = validateRequestHost(recvmsg)
  if not validity:
    # Bad request, we want atleast GET/PUT/DELETE etc on one line and the Host:=CACHE_IP on the next
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
    handleGET(c, cache, dll, locationInDLL, url)
  elif requestType == 'PUT':
    handlePUT(c, url)
  else:
    #Doesn't start with GET/PUT/DELETE, So, server doesn't understand the 
    c.sendall("HTTP/1.1 400 Bad Request\r\n Cannot Understand the type of Request\r\n\r\n".encode())

def main():
  #Create the dicts and the DLL
  cache = dict()
  locationInDLL = dict()
  dll = DLL()
  #Create a socket to listen
  s = getListeningSocket(CACHE_IP, CACHE_PORT, QUEUE_LENGTH)
  #Server Loop
  while True:
    c, addr = s.accept()
    print ('Got connection from', addr )
    recvmsg = c.recv(1024).decode()
    #Printing for observation and debugging
    print('Server received '+recvmsg)
    # Parse the request and respond
    handleRequest(c, cache, dll, locationInDLL, recvmsg)
    # Close the connection with the client
    c.close()

if __name__ == '__main__':
  main()
