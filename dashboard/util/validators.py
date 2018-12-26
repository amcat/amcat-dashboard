from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


def page_filters_validator(val):
    if not isinstance(val, dict):
        raise ValidationError
    if not all(isinstance(v, list) for v in val.values()):
        raise ValidationError
    if not all(isinstance(v, str) for vs in val.values() for v in vs):
        raise ValidationError


@deconstructible
class HighchartsCustomizationValidator:

    def __init__(self, properties):
        self.properties = properties

    def __call__(self, value):
        errors = []
        custom_props = dict(self.properties)
        if not isinstance(value, dict):
            raise ValidationError("Root element must be a dict, got {}".format(type(value)))

        for k, v in value.items():
            try:
                prop = custom_props[k]
            except KeyError:
                errors.append(ValidationError("Unknown property {}".format(k)))
                continue
            if not isinstance(v, prop.type):
                raise ValidationError("Invalid type for {}, expected {!s}, got {!s}".format(k, prop.type, type(v)))

        if errors:
            raise ValidationError(errors)
