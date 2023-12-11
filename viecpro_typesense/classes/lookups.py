""" 



NOT USED AT THE MOMENT; THE WHOLE FILE IS NOT USED. It is the basis for a later implementation.



"""


# this is the default mapping from django field type to typesense field type
field_type_lookup = {
    "DateField": "string",
    "CharField": "string",
    "BooleanField": "bool",
    "FloatField": "float",
    "TextField": "string",
    "AutoField": "string",
    "BigIntegerField": "string",
    "JSONField": "string",
    "IntegerField": "string",
    "PositiveBigIntegerField": "string",
    "SlugField": "string",
    "SmallAutoField": "string",
    "SmallIntegerField": "string",
    "TimeField": "string",
    "BinaryField": "string",
    "DateTimeField": "string",
    "URLField": "string",
}


# These ar all valid typesense field types.
typesense_types = (
    "string",
    "string[]",
    "int32",
    "int32[]",
    "int64",
    "int64[]",
    "float",
    "float[]",
    "bool",
    "bool[]",
    "geopoint",
    "geopoint[]",
    "object",
    "object[]",
    "string*",
    "auto",
)
