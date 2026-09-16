class NotFoundError(Exception):
    pass


class HasDependentsError(Exception):
    pass


class ValidationError(Exception):
    pass


HAS_DEPENDENTS_MESSAGE = "Cannot delete: it still has dependent records"
