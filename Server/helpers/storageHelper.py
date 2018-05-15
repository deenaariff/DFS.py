import hashlib
from ioHelper import resolve_host_name
from ioHelper import IO as IO
import math
import os

from userHelper import Users


# A Class to abstract away details of storing files
# Implements consistent hashing, and keeps tracks of machines available for replication
# Uses Round Robin for assigning nodes to hashed table
class Storage:

    def __init__(self, logger, nodes, partitions, redundancy=2):

        # initialize all module dependencies
        self.context = ""
        self.logger = logger
        self.io = IO(self.logger)

        # set number of partitions
        self.partitions_exp = int(partitions)
        self.num_partitions = int(math.pow(2, self.partitions_exp))

        # initialize all nodes in the cluster
        self.locations = dict()
        self.nodes = []
        for node in nodes:
            result, ip = resolve_host_name(node)
            if result:
                self.new_node(ip)

        # initialize consistent hashing table with given redundancy for backups
        self.tables = []
        self.redundancy = redundancy

        # Create the number of tables that redundancy dictates
        for i in range(0, redundancy):
            table = [-1] * self.num_partitions  # table for consistent hashing
            self.tables.append(table)

        self.roundRobin = 0  # Start the round robin at index 0
        self.users = Users()

    # Add a node
    def new_node(self, ip):
        self.nodes.append(ip)
        self.locations[ip] = list()

    # Return a unique has for a given user name and file
    def hash_user_file(self, user, filename):
        m = hashlib.md5()
        m.update(user + "/" + filename)
        h = m.hexdigest()

        # Reduce hash to given size based on number of partitions
        right_shift = 128 - self.partitions_exp
        return int(h, 16) >> right_shift

    # Debug statement with context
    def log(self, msg):
        self.logger.output(self.context, msg)

    # Heal A Corrupted Disk for any given file
    def heal(self, user, filename):

        self.context = "storageHelper.heal()"
        self.log("Method called")

        console_output = []
        failed = []

        tmp_file_data = {
            'user': user,
            'filename': filename
        }

        found = False
        found_machine = None

        for i in range(0, self.redundancy):

            h = self.hash_user_file(user, filename)
            machine = self.tables[i][h]

            # Test if the remote file exists on a machine
            if self.io.does_remote_file_exist(machine, tmp_file_data):
                if not found:
                    found = True
                    found_machine = machine
                console_output.append(filename + " found on " + machine)

            # Notify user of file not being found on a given machine
            else:
                failed.append(machine)  # Record which machines have failed for subsequent repair
                console_output.append(filename + " not found on: " + machine)
                if not found:
                    console_output.append("Searching for " + filename + " in Backup Servers ... ")

        # Copy intact file to all failed drives
        # Eventually return found file to user
        if found:

            # Iterate over all failed disks
            for failed_disk in failed:
                # Copy the file from intact disk to failed disk
                console_output.append("Attempting to resolve " + filename + " failure in : " + str(failed_disk))
                response, result = self.io.copy_file(found_machine, failed_disk, tmp_file_data)
                if result == 1:
                    console_output.append("Error: Unable to resolve failure in " + str(failed_disk))
                else:
                    console_output.append("Success: Resolved failure in " + str(failed_disk))

            return console_output, 0

        else:
            return console_output, 1

    # Store a file on remote machine
    # Implement consistent hashing and assign file
    def store_file(self, file_data):

        self.context = "storageHelper.store_file()"
        self.log("Method called")

        machines = []
        response = []

        user = file_data['user']
        filename = file_data['filename']

        if self.users.file_exists(user, filename):
            mock_file_data = {
                'user': user,
                'filename': filename
            }
            self.delete_file(mock_file_data)
            response.append("Overwriting Existing Copies of " + filename + " stored for " + user)

        for i in range(0, self.redundancy):

            index = (self.roundRobin + i) % len(self.nodes)
            machine = self.nodes[index]

            # use ssh/scp to send file over the network to target machine
            rsp, result = self.io.send_file(machine, file_data)

            # Update consistent hashing for further use after successful write
            if result == 0:
                if len(response) == 0:
                    response.append("File successfully Written to Machine: " + machine)
                else:
                    response.append("Backup File successfully to Machine: " + machine)
                h = self.hash_user_file(user, filename)
                self.tables[i][h] = machine
                machines.append(machine)

        self.roundRobin = (self.roundRobin + 1) % len(self.nodes)
        self.users.add_file(user, filename, file_data['metadata'])

        for mach in machines:
            self.locations[mach].append(user + "/" + filename)

        return '\n'.join(response), result

    # Get what Machine a file is stored on
    def download_file(self, file_data):

        self.context = "storageHelper.download()"
        self.log("Method called")

        user = file_data['user']
        filename = file_data['filename']

        if self.users.file_exists(user, filename) is False:
            return "File Doesn't Exist on Cluster for " + user, 1, []

        # heal any file corruptions across partitions
        output, result = self.heal(user, filename)

        if result == 0:
            h = self.hash_user_file(user, filename)
            machine = self.tables[0][h]
            auth = os.environ['USER']
            user_response = auth + "@" + machine + ":" + "/tmp/" + auth + "/" + user + "/" + filename
            return user_response, 0, output
        else:
            return "Total Corruption Across Disks for: " + filename, 1, output

    # Delete a file from the table
    def delete_file(self, file_data):

        user = file_data['user']
        filename = file_data['filename']

        response, result = self.users.remove_file(user, filename)

        if result == 1:
            return response, result

        # Remove the file from the table
        h = self.hash_user_file(user, filename)
        for i in range(0, self.redundancy):
            tmp_ip = self.tables[i][h]
            self.locations[tmp_ip].remove(user + "/" + filename)
            self.tables[i][h] = -1

        return response, result

    # Get the users files
    def get_user_files(self, user):
        console_output = []
        for filename in self.users.get_files(user):
            output, result = self.heal(user, filename)
            console_output.append('')
            console_output.extend(output)
        user_ls = self.users.get_user_ls_lrt(user)
        return user_ls[0], user_ls[1], console_output

    # Add a node to the cluster
    def add_node(self, node_data):

        resolved, node_ip = resolve_host_name(node_data['metadata'])

        if not resolved:
            return "This Machine/Node: " + node_ip + " is not reachable on the network", 1
        elif node_ip in self.locations:
            return node_ip + " is already present in the cluster", 1
        else:
            self.new_node(node_ip)

        return self.get_machine_files(node_data['user'], [], True), 0

    # Remove a node and move its contents else where
    def remove_node(self, node_data):

        resolved, node_ip = resolve_host_name(node_data['metadata'])

        if len(self.nodes) == self.redundancy:
            return "Cannot Remove Node, Below Threshold for redundancy of " + str(self.redundancy), 1

        if node_ip not in self.locations:  # check if the node is in the cluster at all
            return "This node is not present in the cluster", 1

        heal_res = ["Checking for File Failures", "---------------------"]

        for file_data in self.locations[node_ip]:  # look at all files store in the given node

            file_split = file_data.split("/")
            user = file_split[0]
            filename = file_split[1]

            output, result = self.heal(user, filename)
            heal_res.append('')
            heal_res.extend(output)

            mock_file_data = {
                'user': user,
                'filename': filename
            }

            h = self.hash_user_file(user, filename)  # obtain the unique hash

            ip_set = dict()  # create set of all ips where that file is stored

            for table in self.tables:  # find the table which keeps the file on the node to be removed
                ip_set[table[h]] = True
                if table[h] == node_ip:
                    resolve_table = table

            new_machine = self.nodes[self.roundRobin]  # determine a new_machine
            while new_machine in ip_set:
                self.roundRobin = (self.roundRobin + 1)  % len(self.nodes)
                new_machine = self.nodes[self.roundRobin]
            resolve_table[h] = new_machine
            self.io.copy_file(node_ip, new_machine, mock_file_data)  # copy it to the new machine
            self.locations[new_machine].append(file_data)

            self.roundRobin = (self.roundRobin + 1) % len(self.nodes)

        del self.locations[node_ip]  # delete node from the locations dictionary pass
        self.nodes.remove(node_ip)  # remove the node from self.nodes

        self.roundRobin = self.roundRobin % len(self.nodes)  # Ensure we don't get an index error

        return self.get_machine_files(node_data['user'], heal_res), 0

    # return a users files across a nodes and format as a response message
    def get_machine_files(self, user, heal_res=[], perform_heal=False):

        results = list()
        results.append("\nFiles Per Machine for " + user)
        results.append("------------------------------")

        healed = {}

        for key, value in self.locations.iteritems():
            results.append(key)
            for file_p in value:
                user_file = file_p.split("/")
                if user_file[0] == user:

                    filename = user_file[1]
                    if perform_heal and filename not in healed:
                        output, result = self.heal(user_file[0], filename)
                        heal_res.append('')
                        heal_res.extend(output)
                        healed[filename] = True

                    results.append("   -" + user_file[1])

        heal_res.extend(results)
        results = heal_res
        return '\n'.join(results)
