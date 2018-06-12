## HashBox

![alt text](https://raw.githubusercontent.com/deenaariff/DFS.py/master/media/hashbox.png)


### Background

#### OpenStack-Swift

Swift is an project under the OpenStack organization designed to offer Object Stores that simplified API. It's goals include acheiving durabilit, availability, and concurrency across all objects stores. This project is a simplified version of OpenStack Swift, to store files across a distributed cluster of nodes.

#### Consistent Hashing Approach

![alt text](https://raw.githubusercontent.com/deenaariff/DFS.py/master/media/ConsistentHashing.png)

### Directory Structure

	-- README.md
	-- Server
		-- server.py
		-- check_ports.sh
		-- run.sh (automation script)
		-- helpers/
	-- Client
		-- client.py
		-- run.sh (automation script)
		-- helpers/
		-- test (test files directory)

### Running the Application

#### Run Server

NOTE: sh run.sh will run server with cmd arguments

    python server.py 16 129.210.16.80 129.210.16.81 129.210.16.83 129.210.16.86

 server.py should be run with the following arguments

arg[0] : num partiions (2 ^ arg[0])
arg[1-n] : ip addresses / host of machines to store files on

This will start the server in whatever machine it is being run on. It will output the following information before listening for request on a random port. It will get login information for all machine in the network from the environment variable $USER.

 - Number of disks being used for file storage
 - Random available port available on each machine/disk
 - IP address of current machine
 - Random Port server is listening on
 - command to run in ./Client directory to connect client to server (ex: python client.py <arg1> <arg2>)

#### Run client

Client.py should be run with two command line arguments, after server.py is run.

    python client.py <server-ip-address> <server-port>

arg[0]: server-ip-address as listed in server output
arg[1]: server-port as listed in server output

#### How to Use Client

Client will ask for user-name by interact with clients in first user prompt.

Client will display prompt to enter the following commands as specified by the Assignment Instructions.


```
# |   Command   |   Argument   |           Description"
---------------------------------------------------------------
1 |  download   | filename.ext |  Display where the object is saved
2 |    list     |   <no_arg>   |  Display all files for the user
3 |   upload    | filename.ext |  Display in which disks object is saved
4 |   delete    | filename.ext |  Delete object
5 |     add     |  ip_address  |  Add a node to the cluster
6 |   remove    |  ip_address  |  Remove a node from the cluster
7 |      q      |   <no_arg>   |  Delete object
```

All commands can be entered into the >> shell as 'cmd arg'.

Example, upon >>, if one wished to upload  a file

    upload test.txt.

**NOTE:** For upload, all files upload will be searched for in path relative to *Client/* Folder ( directory relative to client.py).

Example: The following will search in the directory Client/test/data.txt.

    upload test/data.txt

The *download* command will store files in the path relative to client.py (Client/ directory).

#### Testing Deletion of File / Simulate Disk Failure

At least one copy of the file the cluster stores can be deleted from either the original disk or backup disk. The machine will accomodate this delete by healing the cluster as needed when any other command is run. It will 
necessarily attempt to check for any corruption upon the list, add, and remove commands to ensure consistency amongst the data. 

The 'remove' command will move the files to different nodes in the table to adjust for any files that exist on a node being deleted prior to deletion.
