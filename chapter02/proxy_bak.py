#!/usr/bin/env python3
#coding=utf-8
import sys
from socket import *
import threading
 
 
 
# 16进制导出函数
def hexdump(src, length=16):
    result = []
    # 判读输入是否为字符串    
    digits = 4 if isinstance(src, str) else 2
    for i in range(0, len(src), length):
       # 将字符串切片为16个为一组
       s = src[i:i+length]
       # 用16进制来输出,x是digits的值，表示输出宽度
       hexa = ' '.join(["%0*X" % (digits, (x))  for x in s])
       # 用来输出原值
       text = ''.join([chr(x) if 0x20 <= x < 0x7F else '.'  for x in s])
       #%-*s, 星号是length*(digits + 1)的值
       result.append( "%04X   %-*s   %s" % (i, length*(digits + 1), hexa, text) )
    print('\n'.join(result))
# 设置延时有问题，后续更改
def receive_from(connection):    
    buffer = b""
    # 设置5s延迟,connection=socket(AF_INET, SOCK_STREAM)
    connection.settimeout(5)
    try:
            # 保持数据的读取直到没有数据或超时
            while True:
                    data = connection.recv(4096)
                    if not data:
                            break
                    buffer += data        
    except:
        pass       
    return buffer
 
# 对目标主机的请求数据进行修改
def request_handler(buffer):
    return buffer
 
# 对返回本地主机的响应数据进行修改
def response_handler(buffer):
    return buffer
 
def proxy_handler(client_socket, target_host, target_port, receive_first):
        
        # 连接目标主机
        target_socket = socket(AF_INET, SOCK_STREAM)
        target_socket.connect((target_host,target_port))
 
        # 必要时从目标主机接收数据
        if receive_first:
            target_buffer = receive_from(target_socket)
            hexdump(target_buffer)
            # 发送给我们的响应处理程序
            target_buffer = response_handler(target_buffer)
            # 如果要发送数据给本地客户端，发送它
            if len(target_buffer):
                print("[<==] Sending %d bytes to localhost." % len(target_buffer))
                client_socket.send(target_buffer)
                        
    # 现在我们从本地循环读取数据，发送给远程主机和本地主机
        while True:
            # 从本地读取数据
            local_buffer = receive_from(client_socket)
            if len(local_buffer):    
                print("[==>] Received %d bytes from localhost." % len(local_buffer))
                hexdump(local_buffer)
                # 发送给我们的本地请求
                local_buffer = request_handler(local_buffer)
                # 发送数据给目标主机
                target_socket.send(local_buffer)
                print("[==>] Sent to target.")
            
            # 接收响应的数据
            target_buffer = receive_from(target_socket)
 
            if len(target_buffer):
                print("[<==] Received %d bytes from target." % len(target_buffer))
                hexdump(target_buffer)
                # 发送到响应处理函数
                target_buffer = response_handler(target_buffer)
                # 将响应发送给本地socket
                client_socket.send(target_buffer)
                print("[<==] Sent to localhost.")
            
            # 两边没有数据了，就关闭连接
            if not len(local_buffer) or not len(target_buffer):
                client_socket.close()
                target_socket.close()
                print("[*] No more data. Closing connections.")
                break
        
def server_loop(local_host,local_port,target_host,target_port,receive_first):        
        server = socket(AF_INET, SOCK_STREAM)
        try:
                server.bind((local_host,local_port))
        except:
                print("[!!] Failed to listen on %s:%d" % (local_host,local_port))
                print("[!!] Check for other listening sockets or correct permissions.")
                sys.exit(0)
                
        print("[*] Listening on %s:%d" % (local_host,local_port))
        
        server.listen(5)        
        
        while True:
                client_socket, addr = server.accept()
                # 本地连接信息
                print("[==>] Received incoming connection from %s:%d" % (addr[0],addr[1]))
                # 开启线程和目标主机通信
                proxy_thread = threading.Thread(target=proxy_handler,args=(client_socket,target_host,target_port,receive_first))
                proxy_thread.start()
 
def main():
    if len(sys.argv[1:]) != 5:
        print("Usage: ./proxy.py [localhost] [localport] [targethost] [targetport] [receive_first]")
        print("Example: ./proxy.py 127.0.0.1 9000 10.12.132.1 9000 True")
        sys.exit(0)
    # 本地参数
    local_host  = sys.argv[1]
    local_port  = int(sys.argv[2])
    # 目标参数
    target_host = sys.argv[3]
    target_port = int(sys.argv[4])
 
    receive_first = sys.argv[5]
    
    if "True" in receive_first:
        receive_first = True
    else:
        receive_first = False
        
    # 开始监听
    server_loop(local_host,local_port,target_host,target_port,receive_first)
main()