class AnswerTypeException(TypeError):
    """Exception for type of API answer."""
    def __init__(self, answer, required_type: type):
        self.answer = answer
        self.required_type = required_type
        self.message = (
            f'Error checking data type of answer: {type(self.answer)}. '
            f'Required type: {self.required_type}')
        super().__init__(self.message)


class KeyErrorException(Exception):
    """Exception for keys in the "homework" dictionary."""
    def __str__(self):
        return 'Missing "homework_name" key in homework list.'


class UnexpectedFromDateException(Exception):
    """Exception for unexpected 'from_date' parameter."""
    def __init__(self, error):
        self.error = error
        self.message = f'Unexpected from_date parameter. {self.error}'
        super().__init__(self.message)


class AccessDeniedException(Exception):
    """Exception for invalid or incorrect tokens."""
    def __init__(self, error):
        self.error = error
        self.message = f'Access denied. {self.error}'
        super().__init__(self.message)


class StatusErrorException(Exception):
    """Exception for statuses of homework."""
    def __init__(self, status):
        self.status = status
        self.message = f'Unknown status of homework: {self.status}'
        super().__init__(self.message)


class ServerAccessException(Exception):
    """An exception if there is something wrong with the request to the server.
    """
