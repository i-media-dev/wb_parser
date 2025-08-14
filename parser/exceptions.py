class TypeDataError(ValueError):
    def __str__(self):
        return 'Invalid type data'


class RefTableError(ValueError):
    def __str__(self):
        return 'References table is not exist'


class TableNameError(ValueError):
    pass


class SizeTokenError(ValueError):
    pass


class VerificationError(ValueError):
    pass


class EmptyTokenError(ValueError):
    pass


class BinaryTokenError(ValueError):
    pass


class ModelTokenError(ValueError):
    pass


class EnvFileError(ValueError):
    pass
