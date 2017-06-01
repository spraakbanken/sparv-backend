from jsonschema import Draft3Validator
import logging
import json

log = logging.getLogger('pipeline.' + __name__)


class DefaultValidator(Draft3Validator):
    """This validator populates missing values with the default values in a schema."""
    def validate_properties(self, properties, instance, schema):
        super(DefaultValidator, self).validate_properties(properties, instance, schema)
        for k, v in properties.iteritems():
            if k not in instance and "default" in v:
                default = v["default"]
                super(DefaultValidator, self).validate(default, v)
                instance[k] = default


def open_json(schema_file):
    """
    Open JSON Schema settings.
    Location of these files is set in config.py.
    """
    try:
        with open(schema_file, "r") as f:
            schema_str = f.read()
    except:
        log.exception("Error reading JSON schema settings file")
        schema_str = "{}"
    return schema_str


def load_json(schema_file):
    schema_str = open_json(schema_file)
    try:
        settings_schema = json.loads(schema_str)
    except:
        log.exception("Error parsing JSON is schema settings")
        settings_schema = {}
    return settings_schema


def validate_json(settings_schema):
    try:
        settings_validator = DefaultValidator(settings_schema)
        return settings_validator
    except:
        log.exception("Error starting validator for JSON schema settings")
