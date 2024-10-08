import socket
import threading

HEADER = 1024
FORMAT = "utf-8"
DISCONNECTMSG = "!DISCONNECT"
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER, PORT))

def send(msg):
    msg = msg.encode(FORMAT)
    msgLength = str(len(msg)).encode(FORMAT)
    msgLength += b" " * (HEADER - len(msgLength))
    client.send(msgLength)
    client.send(msg)

def receive(buffer=HEADER):
    return client.recv(buffer).decode(FORMAT)

def listening():
    while True:
        msg = receive()
        print(f"{SERVER}::{PORT} $ Server - ", str(msg).rstrip(' '))

print("Cilent is Starting...")
connected = True
threading.Thread(target=listening, daemon=True).start()
print(f"[{SERVER}::{PORT}]")
while connected:
    msg = input("")
    send(msg)
    if msg == DISCONNECTMSG:
        connected = False

client.close()
