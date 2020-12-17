import re

import click


class LocationType(click.ParamType):
    """
    Validates that given location string is two comma separated floats
    """

    name = "LATTITUDE,LONGITUDE"

    def convert(self, value, param, ctx):
        try:
            match = re.match("^(.*),(.*)$", value)
            float(match.group(1))
            float(match.group(2))
            return value
        except (ValueError, AttributeError):
            self.fail(
                (
                    "location {} is not two comma separated floats "
                    "for lattitude and longitude".format(value)
                )
            )
