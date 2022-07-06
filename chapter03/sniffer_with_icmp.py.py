import os
import socket
import struct
from ctypes import *

# 监听主机
host = "192.168.124.2"

# ip头定义
class IP(Structure):
    _fields_ = [
        ("ihl",                 c_ubyte, 4),    # ip head length:头长度
        ("version",             c_ubyte, 4),    # 版本
        ("tos",                 c_ubyte),       # 服务类型
        ("len",                 c_ushort),      # ip数据包总长度
        ("id",                  c_ushort),      # 标识符
        ("offset",              c_ushort),      # 片偏移
        ("ttl",                 c_ubyte),       # 生存时间
        ("protocol_num",        c_ubyte),       # 协议数字，应该是协议类型,这里用数字来代表时哪个协议,下面构造函数有设置映射表
        ("sun",                 c_ushort),      # 头部校验和
        ("src",                 c_ulong),       # 源ip地址
        ("dst",                 c_ulong)        # 目的ip地址
    ]


    # 创建对象时调用，返回当前对象的一个实例;注意：这里的第一个参数是cls即class本身
    def __new__(cls, socket_buffer=None):
        return cls.from_buffer_copy(socket_buffer)

    # 创建完对象后调用，对当前对象的实例的一些初始化，无返回值,即在调用__new__之后，根据返回的实例初始化；注意，这里的第一个参数是self即对象本身【注意和new的区别】
    def __init__(self, socket_buffer=None):
        # 协议字段与协议名称的对应
        self.protocol_map = {1:"ICMP", 6:"TCP", 17:"UDP"}
        
        # 可读性更强的ip地址(转换32位打包的IPV4地址为IP地址的标准点号分隔字符串表示。)
        self.src_address = socket.inet_ntoa(struct.pack("@I", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("@I", self.dst))

        # 协议类型
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            self.protocol = str(self.protocol_num)


class ICMP(Structure):
    _fields_ = [
        ("type",            c_ubyte),   # 类型
        ("code",            c_ubyte),   # 代码值
        ("checksum",        c_ushort),  # 头部校验和
        ("unused",          c_ushort),  # 未使用
        ("next_hop_mtu",    c_ushort)   # 下一跳的MTU
    ]

    def __new__(cls, socket_buffer):
        return cls.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer):
        self.socket_buffer = socket_buffer


if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP
else:
    socket_protocol = socket.IPPROTO_ICMP

sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)

# 这里端口为0,监听所有端口
sniffer.bind((host, 0))

# 设置在捕获的数据包中包含IP头
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# 在Windows平台上,我们需要设置IOCTL以启用混杂模式
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

try:
    while True:
        # 读取数据包
        raw_buffer = sniffer.recvfrom(65565)[0]

        # 将缓冲区的前20个字节按IP头进行解析
        ip_header = IP(raw_buffer[0:20])

        # 输出协议和通信双方IP地址
        print("Protocol: %s %s -> %s" % (
            ip_header.protocol,
            ip_header.src_address,
            ip_header.dst_address
        ))

        # 如果为ICMP,进行处理
        if ip_header.protocol == "ICMP":

             # 计算ICMP包的起始位置,并获取ICMP包的数据
             # ihl是头部长度,代表32位(即4字节)长的分片的个数
            offset = ip_header.ihl * 4
            buf = raw_buffer[offset:offset + sizeof(ICMP)]

            # 解析ICMP数据
            icmp_header = ICMP(buf)

            print("ICMP -> Type: %d Code: %d" % (
                icmp_header.type,
                icmp_header.code
        ))


# 处理CTRL-C
except KeyboardInterrupt:
    # 如果运行在Windows上,关闭混杂模式
    if os.name == "nt":
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
