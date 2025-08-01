class TypeDataError(ValueError):
    def __str__(self):
        return 'Invalid type data'


class RefTableError(ValueError):
    def __str__(self):
        return 'References table is not exist'
