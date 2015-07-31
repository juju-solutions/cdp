import json
from . import exceptions

def uhoh(exception):
    if not hasattr(exception, 'response'):
        return exception

    error = exception.response.get('Error', None)

    if not error:
        return Exception(exception)

    if hasattr(exceptions, error['Code']):
        return getattr(exceptions, error['Code'])(error['Message'])

    return exceptions.UnknownError(error['code'], error['Message'])
