import paramiko

def ssh_command(ip, user, passwd, command):
    # 创建一个sshclient对象
    client = paramiko.SSHClient()
    # 允许将信任的主机自动加入到host_allow列表，此方法必须放在connect方法的前面
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 连接服务器
    client.connect(ip, username=user, password=passwd)
    # 打开会话
    ssh_session = client.get_transport().open_session()

    # 如果会话存在，则执行指定命令
    if ssh_session.active:
        # 执行命令
        ssh_session.exec_command(command)
        # 返回命令执行结果
        print(ssh_session.recv(1024).decode("utf-8"))
    return


def main():
    import getpass
    ip = "192.168.10.129"
    user = input('Username: ')
    # 调用getpass函数，在屏幕上不显示密码
    passwd = getpass.getpass()
    command = input('Command: ')
    ssh_command(ip, user, passwd, command)


if __name__ == "__main__":
    main()