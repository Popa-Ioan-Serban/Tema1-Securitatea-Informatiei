import socket
import threading
import struct
from queue import Queue


def getMessage(sock):
    length_struct = sock.recv(4)
    length, = struct.unpack('!I', length_struct)
    message = sock.recv(length)
    return message


def getMessageFrom(sock):
    from_node = getMessage(sock)
    from_node = from_node.decode()
    message = getMessage(sock)
    message = message.decode()
    return from_node, message


def sendMessage(sock, message):
    length = len(message)
    sock.sendall(struct.pack('!I', length))
    sock.sendall(message.encode())


def sendMessageTo(sock, to_node, message):
    sendMessage(sock, to_node)
    sendMessage(sock, message)


def putMessageInQueue(commQueue, m_from, m_to, message):
    commQueue.put((m_from, m_to, message))


def getMessageFromQueue(commQueue, m_from, m_to):
    while True:
        tpl = commQueue.get()
        if tpl[0] == m_from and tpl[1] == m_to:
            break
        else:
            commQueue.put(tpl)
    return tpl[2]


def AWorkerProcess(sock, commQueue):
    fromNode1, operationType = getMessageFrom(sock)
    putMessageInQueue(commQueue, 'A', 'B', operationType)
    key_K = getMessageFromQueue(commQueue, 'KM', 'A')
    sendMessageTo(sock, 'A', key_K)
    print('A:', key_K)
    putMessageInQueue(commQueue, 'A', 'B', key_K)

    print('A is done\n')


def BWorkerProcess(sock, commQueue):
    operationMode = getMessageFromQueue(commQueue, 'A', 'B')

    sendMessageTo(sock, 'B', operationMode)
    key_K = getMessageFromQueue(commQueue, 'A', 'B')
    sendMessageTo(sock, 'B', key_K)
    print('B:', key_K)

    print('B is Done\n')


def KMWorkerProcess(sock, commQueue):
    fromNode3, keyEncrypted = getMessageFrom(sock)
    print('KM:', keyEncrypted)
    putMessageInQueue(commQueue, 'KM', 'A', keyEncrypted)

    print('KM is done\n')


class ClientThread(threading.Thread):
    def __init__(self, clientSocket, clientAddress, commQueue):
        threading.Thread.__init__(self)
        self.clientSocket = clientSocket
        self.clientAddress = clientAddress
        self.commQueue = commQueue

    def run(self):
        print('new connection: [{0}]:[{1}]'.format(self.clientAddress[0], self.clientAddress[1]))
        fromNode, clientType = getMessageFrom(self.clientSocket)

        if fromNode != 'server' and clientType not in ['A', 'B', 'KM']:
            print('[SERVER] error server [#1] for client [{0}]:[{1}]'.format(self.clientAddress[0], self.clientAddress[1]))
            sendMessageTo(self.clientSocket, clientType, 'NOT_OK')
            return

        sendMessageTo(self.clientSocket, clientType, 'OK')
        print('[{0}]:[{1}] connected as [{2}]'.format(self.clientAddress[0], self.clientAddress[1], clientType))

        if clientType == 'A':
            AWorkerProcess(self.clientSocket, self.commQueue)
        elif clientType == 'B':
            BWorkerProcess(self.clientSocket, self.commQueue)
        else:
            KMWorkerProcess(self.clientSocket, self.commQueue)

        print('[{0}]:[{1}] disconnected from the server'.format(self.clientAddress[0], self.clientAddress[1]))
        self.clientSocket.close()


HOST = '127.0.0.1'
PORT = 12345
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((HOST, PORT))
print('server started')
print('waiting for connections...')

serverSocket.listen(5)

commQueueOuter = Queue()

while True:
    clientSocketOuter, clientAddressOuter = serverSocket.accept()
    newThread = ClientThread(clientSocketOuter, clientAddressOuter, commQueueOuter)
    newThread.start()
