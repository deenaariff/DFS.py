import sys
import socket
import os
import subprocess
import helpers.responseHelper as cmd
import helpers.storageHelper as storage
import helpers.loggingHelper as logging

DISPLAY_LOGS = True # Choose Whether to Display Contexted debug statements
logger = logging.Logger(DISPLAY_LOGS)


if len(sys.argv) < 3:
    raise Exception("Invalid/Insufficient Command Line Arguments Replicate Data Across Machines")
    exit(1)

# Number of unique partitions for consistent hashing
PARTITIONS = sys.argv[1]

# Obtain the list of nodes to replicate files to
nodes = sys.argv[2:]


for host in nodes:
    try:
        socket.gethostbyaddr(host)
    except socket.herror:
        raise Exception("One or More Hosts given is Invalid")
        exit(1)


def main():

    print "Number of Storage Destinations: %i" % (len(sys.argv[2:]))

    # Create a socket object
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print

    ips = subprocess.check_output(['hostname', '--ip-address'])
    print "Server IP Address : " + ips.strip()

    # Bind the Socket to localhost at a given port
    try:
        s.bind(('', 0))
        print "Server Listening on Port: " + str(s.getsockname()[1])
        print "Run Client in project/Client: python client.py " + ips.strip() + " " + str(s.getsockname()[1])
    except socket.error as err:
        print "Socket Connection Error %s" % err

    # Listen for incoming messages
    s.listen(6)

    # Create storage helper instance and inject into Command Handler as dependency
    _storage = storage.Storage(logger, nodes, PARTITIONS)
    handler = cmd.CmdHandler(logger, _storage)

    # Listen for incoming clients and handle requests
    while True:

        try:

            # conn is a new socket object
            conn, address = s.accept()

            payload = conn.recv(100000)

            if not payload:
                result = cmd.no_data_exists_response()
            else:
                result = handler.handle_commands(payload)

            conn.send(result)

        except KeyboardInterrupt:
            conn.close()
            break

        conn.close()


if __name__ == "__main__":

    print
    print "Remote Authentication User: " + os.environ['USER']

    print
    print "Free Ports on Remote Host Machines"
    print "-------------------------------------"

    f = open('check_ports.sh', 'r')
    script = f.read()

    # List Available Ports
    for node in nodes:
        login = os.environ['USER'] + "@" + node
        out = subprocess.Popen(["ssh", login, script],
                               stdout=subprocess.PIPE,
                               universal_newlines=True)
        out.wait()  # wait until the script has finished
        stdout_data, stderr_data = out.communicate()
        port = stdout_data.strip()

        if len(port) > 0:
            print node + " : " + port

    main()

