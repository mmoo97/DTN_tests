import click


class OneUseOption(click.Option):
    """
    Overwrites the type_cast_value function inherited from click.Parameter
    to assert an option was only used once, and then converts it back
    to the original value type.
    """

    def type_cast_value(self, ctx, value):

        # get the result of a normal type_cast
        converted_val = super(OneUseOption, self).type_cast_value(ctx, value)

        # if the option takes arguments (multiple was set to true)
        # assert no more than one argument was gotten, and if an argument
        # was gotten, take it out of the tuple and return it
        if self.multiple:
            if len(converted_val) > 1:
                raise click.BadParameter("Option used multiple times.", ctx=ctx)
            if len(converted_val):
                return converted_val[0]
            else:
                return None

        # if the option was a flag (converted to a count) assert that the flag
        # count is no more than one, and type cast back to a bool
        elif self.count:
            if converted_val > 1:
                raise click.BadParameter("Option used multiple times.", ctx=ctx)
            return bool(converted_val)

        else:
            raise ValueError(
                (
                    "Internal error, OneUseOption expected either "
                    "multiple or count, but got neither."
                )
            )


def one_use_option(*args, **kwargs):
    """
    Wrapper of the click.option decorator that replaces any instances of
    the Option class with the custom OneUseOption class
    """
    # cannot force a multiple or count option to be single use
    if "multiple" in kwargs or "count" in kwargs:
        raise ValueError(
            "Internal error, one_use_option cannot be used with multiple or count."
        )

    # cannot force a non Option Paramater (argument) to be a OneUseOption
    if kwargs.get("cls"):
        raise TypeError(
            "Internal error, one_use_option cannot overwrite "
            "cls {}.".format(kwargs.get("cls"))
        )

    # use our OneUseOption class instead of a normal Option
    kwargs["cls"] = OneUseOption

    # if dealing with a flag, switch to a counting option,
    # and then assert if the count is not greater than 1 and cast to a bool
    if kwargs.get("is_flag"):
        kwargs["is_flag"] = False  # mutually exclusive with count
        kwargs["count"] = True

    # if not a flag, this option takes an argument(s), switch to a multiple
    # option, assert the len is 1, and treat the first element as the value
    else:
        kwargs["multiple"] = True

    # decorate with the click.option decorator, but with our custom kwargs
    def decorator(f):
        return click.option(*args, **kwargs)(f)

    return decorator
