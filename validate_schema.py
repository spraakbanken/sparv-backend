# Validates the json schema in settings_schema.json
# and tries in on the example example_corpus.json.
#
# A successful run should only print the default settings back.

from schema_utils import DefaultValidator
import json

"""
Loading the schema and making a validator
"""
with open("settings_schema.json", "r") as f:
    schema_str = f.read()

schema = json.loads(schema_str)

validator = DefaultValidator(schema)

"""
Testing the schema against an instance
"""
with open("example_corpus.json", "r") as f:
    instance_str = f.read()

instance = json.loads(instance_str)

validator.validate(instance)

"""
Test using the default populator
"""

e = {}
validator.validate(e)
print json.dumps(e, indent=4)
