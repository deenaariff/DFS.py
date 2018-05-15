import json

import dataHelper as dataHelper
import clientMessageHelper as um


# Print All Commands User Can Enter
def print_user_options():
    print
    print (" # |  Command  |   Argument   |           Description")
    print ("---------------------------------------------------------------")
    print (" 1 |  download   | filename.ext |  Display where the object is saved")
    print (" 2 |    list     |   <no_arg>   |  Display all files for the user")
    print (" 3 |   upload    | filename.ext |  Display in which disks object is saved")
    print (" 4 |   delete    | filename.ext |  Delete object")
    print (" 5 |     add     |  ip_address  |  Add a node to the cluster")
    print (" 6 |   remove    |  ip_address  |  Remove a node from the cluster")
    print (" 7 |      q      |   <no_arg>   |  Delete object")
    print


# Handle Response using conn socket object
def handle_server_response(conn, cmd):
    payload = conn.recv(4096)

    try:
        data = json.loads(payload)
        rsp = data['msg']
        result = int(data['result'])

        if cmd == 'download': # handle download response
            console_output = data['payload']
            print '\n'.join(console_output)
            
            if result == 0:  # if the return message was successful
                dataHelper.get_remote(rsp)
                filename = rsp.split('/')[-1]
                with open(filename, 'r') as f:
                    print f.read()

            else:  # print the output
                print rsp

        else:
            if cmd == 'list':
                console_output = data['payload']
                print '\n'.join(console_output)
            if result == 0:
                print
                print um.SUCCESS_BANNER
                print um.DELIM
                print rsp
            else:
                print
                print um.ERROR_BANNER
                print um.DELIM
                print rsp

    except Exception as err:
        print err.message


# Format response if user sends command 'download'
def handle_download(tokens, user):
    try:
        filename = tokens[1]
        msg = dataHelper.serialize_data('1', filename, "", user, "")
        return True, msg
    except IndexError:
        print um.MISSING_ARGS
        return False, ""


# Format response if user sends command 'list'
def handle_list(user):
    msg = dataHelper.serialize_data('2', "", "", user, "")
    return True, msg


# Format response if user sends command 'upload'
def handle_upload(tokens, user):
    try:
        file_path = tokens[1]
        filename = file_path.split("/")[-1]
        exists, result, metadata = dataHelper.read_file(file_path, filename, user)
        if not exists:
            print result
            print um.FILE_ERROR
            return False, ""
        else:
            msg = dataHelper.serialize_data('3', filename, result, user, metadata)
            return True, msg

    except IndexError:
        print um.MISSING_ARGS
        return False, ""


# Format response if user sends command 'delete'
def handle_delete(tokens, user):
    try:
        filename = tokens[1]
        msg = dataHelper.serialize_data('4', filename, "", user, "")
        return True, msg
    except IndexError:
        print um.MISSING_ARGS
        return False, ""


# Format response for add
def handle_add(tokens, user):
    msg = dataHelper.serialize_data('5', '', '', user, tokens[1])
    return True, msg


# Format response for remove
def handle_remove(tokens, user):
    msg = dataHelper.serialize_data('6', '', '', user, tokens[1])
    return True, msg
