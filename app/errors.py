class HttpError(Exception):
    """
    Класс для обработки ошибок HTTP
    """
    def __init__(self, status_code: int, message: str | dict):
        self.status_code = status_code
        self.message = message
