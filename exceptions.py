class AnswerTypeException(TypeError):
    """Exception for required type of data."""
    def __init__(self, required_type: type):
        self.required_type = print(
            f'Error checking data type. Required type: {required_type}')


class KeyErrorException(Exception):
    """Exception for keys in the "homework" dictionary."""
    def __init__(self, message):
        super.__init__(message)
