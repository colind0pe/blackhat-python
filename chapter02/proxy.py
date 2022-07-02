# 测试时每次都连接超时，无法使用，仓库同目录下的proxy_bak.py是可以使用的

import sys
import socket
import threading


# 十六进制导出函数
def hexdump(src, length=16):
    result = []

    # 判断输入是否为字符串
    # isinstance(object, classinfo)
    digits = 4 if isinstance(src, str) else 2

    # range(start, stop[, step])
    for i in range(0, len(src), length):

        # 16个字节为一组进行切片
        s = src[i:i + length]

        # 用16进制来输出,x是digits的值，表示输出宽度
        hexa = ' '.join(["%0*X" % (digits, (x))  for x in s])

        # 用来输出原值
        text = ''.join([chr(x) if 0x20 <= x < 0x7F else '.' for x in s])

        #%-*s, 星号是length*(digits + 1)的值
        result.append(
            "%04X   %-*s   %s" % (i, length*(digits + 1), hexa, text)
            )

    print('\n'.join(result))


def receive_from(connection):
    # 初始化缓冲区
    buffer = b''

    # 超时设置有问题
    connection.settimeout(10)

    try:

        # 持续从缓存中读取数据直到没有数据或者超时
        while True:
            data = connection.recv(4096)
            if not data:
                break
            buffer += data

    except TimeoutError:
        pass # pass是空语句,是为了保持程序结构的完整性,防止报错

    return buffer


# 对目标主机的请求数据进行修改
def request_handler(buffer):
    return buffer


# 对返回本地主机的响应数据进行修改
def response_handler(buffer):
    return buffer


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    
    # 连接目标主机
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    # 必要时从目标主机接收数据
    if receive_first:
        remote_buffer = receive_from(remote_socket)

        # 调用hexdump函数处理数据
        hexdump(remote_buffer)

        # 发送给response_handler处理
        remote_buffer = response_handler(remote_buffer)

        # 如果要发生数据给本地客户端，发送它
        if len(remote_buffer):
            print("[<==] Sending %d bytes to localhost." % len(remote_buffer))
            client_socket.send(remote_buffer)

    # 现在我们从本地循环读取数据，发送给远程主机和本地主机
    while True:
        # 从本地读取数据
        local_buffer = receive_from(client_socket)

        if len(local_buffer):
            print("[==>] Received %d bytes from localhost." % len(local_buffer))
            hexdump(local_buffer)
            # 发送到请求处理函数
            local_buffer = request_handler(local_buffer)
            # 发送给目标主机
            remote_socket.send(local_buffer)
            print("[==>] Sent to remote.")

        # 接收响应数据
        remote_buffer = receive_from(remote_socket)

        if len(remote_buffer):
            print("[<==] Received %d bytes from remote." % len(remote_buffer))
            hexdump(remote_buffer)
            # 发送到响应处理函数
            remote_buffer = response_handler(remote_buffer)
            # 将响应发送到本地socket
            client_socket.send(remote_buffer)
            print("[<==] Sent to localhost.")
        
        # 当两边都没有数据时，关闭连接
        if not len(local_buffer) or not len(remote_buffer):
            client_socket.close
            remote_socket.close
            print("[*] No more data. Closing connections.")
            break


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server.bind((local_host, local_port))
    except socket.error as exc:
        print("[!!] Failed to listen on %s:%d" % (local_host, local_port))
        print("[!!] Check for other listening sockets or correct permissions.")
        print(f"[!!] Caught exception error: {exc}")
        sys.exit(0)

    print("[*] Listening on %s:%d" % (local_host, local_port))

    server.listen(5)

    while True:
        client_socket, addr = server.accept()
        # 打印本地连接信息
        print("[==>] Received incoming connection from %s:%d" % (addr[0], addr[1]))
        # 创建线程和目标主机通信
        proxy_thread = threading.Thread(target=proxy_handler, args=(
            client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()


def main():
    # 如果输入参数个数不等于5，则打印使用方法
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport] [remotehost] "
              "[remoteport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    
    # 本地参数
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    # 目标参数
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    # 在连接之前发送的数据
    receive_first = sys.argv[5]

    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False

    # 开始监听
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)


main()