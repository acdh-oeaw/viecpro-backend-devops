class DTSTypeError(TypeError):
    pass


class DTSValidationError(Exception):
    pass


class DTSParsingError(Exception):
    pass


class DTSCircularDependencyError(Exception):
    pass


class TypesenseFieldSerializationError(Exception):
    pass


class TypesenseClientError(Exception):
    pass


class DTSSettingsValidationError(DTSValidationError):
    pass


class DTSFieldValidationError(DTSValidationError):
    pass


class DTSSchemaValidationError(DTSValidationError):
    pass


class TypesenseDefaultSettingsNotFoundError(FileNotFoundError):
    pass


class TypesenseProjectSettingsNotFoundError(NotImplementedError):
    pass


class TypesenseSettingsNotFoundError(NotImplementedError):
    pass


class TypesenseFieldTypeMapError(Exception):
    pass
