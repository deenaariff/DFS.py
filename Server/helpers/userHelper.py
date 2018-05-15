class Users:

    def __init__(self):
        self.users = {}

    # Add a user by creating a dict
    def add_user(self, user):
        self.users[user] = {}

    # get all the filenames for a given user
    def get_files(self, user):
        result = []
        if user not in self.users:
            return result
        for key, value in self.users[user].iteritems():
            result.append(key)
        return result

    # Does user have a file
    def file_exists(self, user, filename):
        if user not in self.users:
            return False
        if filename not in self.users[user]:
            return False
        return True

    # Add a file to the users data structure
    def add_file(self, user, filename, metadata):
        if user not in self.users:
            self.add_user(user)
        entry = {
            'description': metadata
        }
        self.users[user][filename] = entry

    # Remove a file from the users data structure
    def remove_file(self, user, filename):
        try:
            user = self.users[user]
            del user[filename]
            return "The File Was Successfully removed", 0
        except KeyError:
            return "The File Does Not Exist in the Object Storage", 1

    # Get the ls -lrt data for a file for a given user
    def get_user_ls_lrt(self, user):

        try:
            user_obj = self.users[user]
            if len(user_obj) == 0:
                return "No Files Stored for user " + user, 0
        except KeyError:
            return "No Files Stored for user " + user, 0

        result = ""

        for filename, entry in user_obj.iteritems():
            result += entry['description'] + "\n"

        return result, 0


