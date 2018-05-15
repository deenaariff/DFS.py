import subprocess
import os.path
import socket
import shutil
import os


# Create a user/filename string
def create_path(file_data):
    return file_data['user'] + "/" + file_data['filename']


# Get a ip address for given hostname
def resolve_host_name(host):
    try:
        ip = socket.gethostbyname(host)
        return True, ip
    except socket.error:
        return False, ""


class IO:

    # Constructor
    def __init__(self, logger):
        self.logger = logger
        self.cache_path = "cache/"
        self.tmp_files = dict()
        self.context = ""
        self.auth = os.environ['USER']
        self.remote_path = "/tmp/" + self.auth + "/"

    # Output a Log with context
    def log(self, msg):
        self.logger.output(self.context, msg)

    # Obtain total cache path for any file to be added
    def get_cache_path(self, sub_path):
        return self.cache_path + sub_path

    # Cleanup all temporary files created
    def cleanup(self):
        if os.path.exists(self.cache_path):
            shutil.rmtree(self.cache_path)

    # Write a temporary file to await scp transfer
    def write_tmp_file(self, file_data):
        key = create_path(file_data)

        tmp_file_path = self.get_cache_path(key)
        new_dir = self.cache_path + file_data['user'] + "/"

        # Create the temporary file directory if it does not exist
        subprocess.call('mkdir -p ' + new_dir, shell=True)

        print tmp_file_path

        with open(tmp_file_path, 'w') as f:
            f.write(file_data['text'])
            f.close()

        self.tmp_files[key] = True
        return tmp_file_path

    # Delete a temporary file
    def delete_tmp_file(self, file_data):
        os.remove(self.get_cache_path(create_path(file_data)))
        key = create_path(file_data)
        self.tmp_files[key] = False

    # Check if tmp_file exists for a given key
    def tmp_file_exists(self, file_data):
        key = create_path(file_data)
        exists = False
        if key in self.tmp_file:
            exists = self.tmp_file[key]
        return exists

    # Test if a Remote File Exists
    def does_remote_file_exist(self, machine, file_data):

        self.context = "rpcHelper.does_remote_file_exist()"
        self.log("Method Called.")

        # Use user/obj as a the key
        key = create_path(file_data)

        remote_path = self.remote_path + key

        login = self.auth + '@' + str(machine)

        try:
            status = subprocess.call(["ssh", login, "test", "-f", remote_path])
        except Exception as err:
            print 'SSH failed to ' + machine
            return False

        if status == 0:
            return True
        elif status == 1:
            return False

    # Change authorization on remote destination
    def authorize(self, login, key):

        out = subprocess.Popen(
            ["ssh", "-o", "StrictHostKeyChecking=no", login, "chmod -R 777 " + self.remote_path],
            shell=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out.wait()

        out = subprocess.Popen(
            ["ssh", "-o", "StrictHostKeyChecking=no", login, "chmod 666 " + self.remote_path + key],
            shell=False,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out.wait()

    # SCP a file to another machine
    # Will call delete_tmp_file during execution
    def copy_file(self, origin, destination, file_data):

        self.context = "rpcHelper.copyFile()"
        self.log("Method Called.")

        # Use user/obj as a the key
        key = create_path(file_data)
        remote_path = self.remote_path + key

        # origin cmds
        login_origin = self.auth + "@" + origin
        scp_from = login_origin + ":" + remote_path

        # destination cmds
        login_destination = self.auth + "@" + destination
        scp_to = login_destination + ":" + remote_path

        self.log("Writing to " + scp_to)

        try:

            cmd = ["ssh","-o", "StrictHostKeyChecking=no", login_destination, 'mkdir','-p', self.remote_path + file_data['user'] + "/"]
            out = subprocess.Popen(cmd)
            out.wait()

            cmd = ["scp","-o", "StrictHostKeyChecking=no","-3","-B", scp_from, scp_to]
            print ' '.join(cmd)

            out = subprocess.Popen(cmd)
            out.wait()

            self.authorize(login_destination, key)

        except subprocess.CalledProcessError:

            return "ERROR: An Error Occured over SSH/SCP", 1

        return "File Successfully Written to Remote Machine (" + destination + ")", 0

    # SCP a file to another machine
    # Will call delete_tmp_file during execution
    def send_file(self, machine, file_data):

        self.context = "rpcHelper.sendFile()"
        self.log("Method Called.")

        # Use user/obj as a the key
        key = create_path(file_data)

        user = file_data['user']
        tmp_file_path = self.write_tmp_file(file_data)

        # Construct ssh and scp commands from substrings
        login = self.auth + "@" + machine
        scp_to = login + ":" + self.remote_path + key
        cmd = "mkdir -p " + self.remote_path + user

        self.log("Writing to " + scp_to)

        #For each disk on a machine, you need put objects/files under each
        #machine's /tmp/<yourLoginName>/<user>/<fileName>, and make
        #/tmp/<yourLoginName> and /tmp/<yourLoginName>/<user> mode 777, and
        #make /tmp/<yourLoginName>/<user>/<fileName> mode 666.

        try:

            out = subprocess.Popen(["ssh", "-o", "StrictHostKeyChecking=no", login, cmd], shell=False,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out.wait()

            out = subprocess.Popen(["scp", "-B", tmp_file_path, scp_to])
            out.wait()

            self.authorize(login, key)

        except subprocess.CalledProcessError:

            return "ERROR: An Error Occured over SSH/SCP", 1

        # Delete the local_tmp file
        #self.delete_tmp_file(file_data)

        return "File Successfully Written to Remote Machine (" + machine + ")", 0

