
class UnknownError(Exception):
    def __init__(self, code, message):
        super(UnknownError, self).__init__("%s: %s" % (code, message))


class EntityAlreadyExists(Exception):
    pass


class AccessDenied(Exception):
    pass


class NoSuchEntity(Exception):
    pass


class DeleteConflict(Exception):
    pass
