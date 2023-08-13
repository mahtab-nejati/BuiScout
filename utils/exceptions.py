class DebugException(Exception):
    pass


class ConfigurationException(Exception):
    pass


class MissingRootException(Exception):
    def __init__(self, root_type, file_saved_as):
        self.file_saved_as = file_saved_as
        self.root_type = root_type
        self.message = f"Root node of type {self.root_type} not found in file {self.file_saved_as}."
        self.message += (
            " Please make sure your language support configurations are correct."
        )
        super().__init__(self.message)


class MissingArgumentsException(Exception):
    def __init__(self, command_id, location):
        self.command_id = command_id
        self.location = location
        self.message = f"{self.command_id} command at {self.location} is missing expected arguments."
        super().__init__(self.message)
