import socket
import struct
from Crypto import Random
from Crypto.Random import random
from Crypto.Cipher import AES

keyPrime = b'Sixteen byte key'
initVect = Random.new().read(AES.block_size)


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


def AWorkerProcess(sock):
    while True:
        print('Give an operation mode (ECB/CFB):')
        operationMode = input()
        if operationMode in ['ECB', 'CFB']:
            break

    sendMessageTo(sock, 'B', operationMode)

    fromNode1, key_K = getMessageFrom(sock)
    print('Key received:', key_K)
    print('Keytype:', type(key_K))
    print('size:', int(key_K).bit_length())
    key_int = int(key_K)
    key_size = key_int.bit_length()
    key_bytes = key_int.to_bytes(key_size // 8 if key_size % 8 == 0 else key_size // 8 + 1, byteorder='big')
    print(key_bytes)
    cipher = AES.new(keyPrime, AES.MODE_CFB, initVect)
    key_K_d = cipher.decrypt(key_bytes)
    key_K_int = int.from_bytes(key_K_d, byteorder='big')
    print('initialKey:', key_K_int)

    print('Here is A worker')


def BWorkerProcess(sock):
    fromNode2, operationMode = getMessageFrom(sock)
    print('operationMode:', operationMode)
    fromNode2, key_K = getMessageFrom(sock)
    print('Key received:', key_K)
    key_int = int(key_K)
    key_size = key_int.bit_length()
    key_bytes = key_int.to_bytes(key_size // 8 if key_size % 8 == 0 else key_size // 8 + 1, byteorder='big')
    print(key_bytes)
    cipher = AES.new(keyPrime, AES.MODE_CFB, initVect)
    key_K_d = cipher.decrypt(key_bytes)
    key_K_int = int.from_bytes(key_K_d, byteorder='big')
    print('initialKey:', key_K_int)

    print('Here is B worker')


def KMWorkerProcess(sock):
    KRandom = random.getrandbits(128)
    KR_size = KRandom.bit_length()
    print(KRandom.bit_length())
    print(KRandom)
    print(str(KRandom).encode())
    KR_bytes = KRandom.to_bytes(KR_size // 8 if KR_size % 8 == 0 else KR_size // 8 + 1, byteorder='big')
    cipher = AES.new(keyPrime, AES.MODE_CFB, initVect)
    KEncrypted = cipher.encrypt(KR_bytes)
    print(KEncrypted)
    print(type(KEncrypted))
    print('as number:', int.from_bytes(KEncrypted, byteorder='big'))
    KEncrypted_nr = int.from_bytes(KEncrypted, byteorder='big')
    print('text: ', str(KEncrypted_nr).encode())
    sendMessageTo(sock, 'A', str(KEncrypted_nr))

    print('Here is KM worker')


while True:
    print('input a valid type of client for establish a connection (A, B, KM):', end=' ')
    clientType = input()
    if clientType in ['A', 'B', 'KM']:
        break

SERVER_IP = '127.0.0.1'
PORT = 12345

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.connect((SERVER_IP, PORT))

sendMessageTo(serverSocket, 'server', clientType)
fromNode, result = getMessageFrom(serverSocket)

if fromNode != clientType and result != 'OK':
    print('[CLIENT] error client [#1]')
    exit()

if clientType == 'A':
    AWorkerProcess(serverSocket)
elif clientType == 'B':
    BWorkerProcess(serverSocket)
else:
    KMWorkerProcess(serverSocket)

serverSocket.close()
print('Done!')
