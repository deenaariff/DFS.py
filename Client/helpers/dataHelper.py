import json
import subprocess


# Serialize the data into JSON Object to be send to server
def serialize_data(cmd_index, file_name, file_string, user, metadata):
    data = {
        'cmd_index': cmd_index,
        'user': user,
        'filename': file_name,
        'text': file_string,
        'metadata': metadata
    }
    return json.dumps(data)


# Retrieve a file from a remote server
# @param path is in form user@machine:file_path
def get_remote(path):
    filename = path.split("/")[-1]
    machine = path.split("@")[1].split(":")[0]
    print "Downloading File From " + machine + " ... "
    p = subprocess.Popen(["scp", "-B", path, filename], shell=False, stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)
    for line in iter(p.stdout.readline, b''):
        print(">>> " + line.rstrip())


# Read a file and return if file exists, its contents, and ls -lrt output
def read_file(file_path,filename,user):

    exists = True
    metadata = ""

    try:
        f = open(file_path, 'r')
        data = f.read()
    except IOError as e:
        data = e
        exists = False

    # Use a subprocess to obtain ls -lrt info for the file
    if exists:
        try:
            p = subprocess.Popen(['ls', '-lrt', file_path], stdout=subprocess.PIPE)
            output = p.stdout.read()
            tokens = output.split(" ")
            tokens[-1] = filename
            tokens[-7] = user
            metadata = " ".join(tokens)
        except Exception as e:
            print e.message
            return False, data, metadata

    return exists, data, metadata

