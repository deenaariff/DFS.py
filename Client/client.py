import sys
import socket

import helpers.clientMessageHelper as um
import helpers.inputHelper as ih

# Ensure Correct Number of Command Line Args
if len(sys.argv) < 3:
    raise Exception(um.NETWORK_ERR)
    exit(1)

# Set HOST and PORT INFO
HOST = sys.argv[1]
PORT = int(sys.argv[2])

# Get User for Client From Environment Variable
user = raw_input("Provide Your User Name: ")


run_client = True  # Run Client in Loop Until User Quits

while run_client:

    # New Socket Object
    s = socket.socket()

    try:

        # Connect to the host and port
        s.connect((HOST, PORT))

        # Print Commands User Can Enter
        ih.print_user_options()

        # Handle User Response
        text = raw_input(">> ")
        tokens = text.split(" ")

        send = True
        msg = ""
        cmd = tokens[0]

        # Create Appropriate MSG Given User cmd
        # Handle Invalid User cmd if necessary
        if cmd == 'q':
            run_client = False
            send = False
        elif cmd == 'download':
            send, msg = ih.handle_download(tokens, user)
        elif cmd == 'list':
            send, msg = ih.handle_list(user)
        elif cmd == 'upload':
            send, msg = ih.handle_upload(tokens, user)
        elif cmd == 'delete':
            send, msg = ih.handle_delete(tokens, user)
        elif cmd == 'add':
            send, msg = ih.handle_add(tokens, user)
        elif cmd == 'remove':
            send,msg = ih.handle_remove(tokens, user)
        else:
            print um.INVALID_CMD
            send = False

        # If send = True send the data and handle server response
        if send:
            s.sendall(msg)
            ih.handle_server_response(s, cmd)

    # Handle any socket errors
    except socket.error as err:

        print um.SOCKET_ERROR
        print err
        exit(1)

    except KeyboardInterrupt:
        s.close()
        exit(0)

    # Close the socket connection
    s.close()


