import socket
import threading

bind_ip = "0.0.0.0"
bind_port = 9998

# 创建socket对象
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 指定监听地址和端口
server.bind((bind_ip, bind_port))

# 开始监听
server.listen(5)

# 打印监听地址和端口
print("[*] Listening on %s:%d" % (bind_ip, bind_port))

def handle_client(client_socket):
    # 调用recv()接收数据
    request = client_socket.recv(1024)
    
    # 打印接收的数据
    print("[*] Received: %s" % request)

    # 返回数据给客户端，关闭socket
    client_socket.send(b"ACK!")
    client_socket.close()


while True:
    # 将接收到的客户端socket对象保存到client变量中，将远程连接的详细信息保存到addr变量中
    client, addr = server.accept()

    print("[*] Accepted connection from: %s:%d" % (addr[0], addr[1]))

    # 创建一个新的线程，让它指向handle_client函数，并传入client变量
    client_handler = threading.Thread(target=handle_client, args=(client,))
    # 启动这个线程来处理刚才收到的连接
    client_handler.start()