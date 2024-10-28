class InstallerException(Exception):
    pass


class UnknownDistroFormatException(InstallerException):
    pass


class DistroNotFoundException(InstallerException):
    pass
