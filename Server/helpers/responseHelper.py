import json


# Format Serialized JSON repsonse to client
def generate_server_response(result, msg, payload):
    return json.dumps({
        "result": result,
        "msg": msg,
        "payload": payload
    })


# Format Response for No Data From Client
def no_data_exists_response():
    return generate_server_response(1, "No Data Received Over Network", "")


# A Class to handle and delegate commands sent from the client
class CmdHandler:

    def __init__(self, logger, storage):
        self.logger = logger
        self.storage = storage
        self.context = ""

    def log(self, msg):
        self.logger.output(self.context, msg)

    # Handle the Payload from the client and format response appropriately
    def handle_commands(self, payload):

        self.context = "commandHandler.handle_commands()"

        # Attempt to load user payload as json
        try:
            data = json.loads(payload)
            index = data['cmd_index']
        except Exception as err:
            result = "Error with deserialization of data %s" % err.message
            success_code = 1
            return generate_server_response(success_code, result, {})

        self.log("Command Sent By User (" + data['user'] + "): " + index)
        console_output = []

        # Based on user cmd-number mapping call the appropriate method from storage
        if index == '1':
            result, success_code, console_output = self.storage.download_file(data)
        elif index == '2':
            result, success_code, console_output = self.storage.get_user_files(data['user'])
        elif index == '3':
            result, success_code = self.storage.store_file(data)
        elif index == '4':
            result, success_code = self.storage.delete_file(data)
        elif index == '5':
            result, success_code = self.storage.add_node(data)
        elif index == '6':
            result, success_code = self.storage.remove_node(data)
        else:
            result = "Server Was Unable to Handle Command (Invalid Command)"
            success_code = 1

        # return formatted response as serialized JSON object
        return generate_server_response(success_code, result, console_output)

