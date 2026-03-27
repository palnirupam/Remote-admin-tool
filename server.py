import socket

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket()
server.bind((HOST, PORT))
server.listen(5)

print("Server started...")

while True:
    conn, addr = server.accept()
    print("Connected:", addr)

    while True:
        cmd = input("Enter command (type 'exit' to close): ")

        if not cmd:
            continue

        conn.send(cmd.encode())

        if cmd.lower() == "exit":
            break

        data = conn.recv(4096)

        if not data:
            print("Client disconnected")
            break

        print("\nOutput:")
        print(data.decode(errors="ignore"))
        print("------\n")

    conn.close()
