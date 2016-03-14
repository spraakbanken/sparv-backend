# This validator populates missing values with the default values in a schema.

from jsonschema import Draft3Validator

class DefaultValidator(Draft3Validator):
    def validate_properties(self, properties, instance, schema):
        super(DefaultValidator, self).validate_properties(properties, instance, schema)
        for k, v in properties.iteritems():
            if k not in instance and "default" in v:
                default = v["default"]
                super(DefaultValidator, self).validate(default, v)
                instance[k] = default
