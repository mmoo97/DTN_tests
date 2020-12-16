def detect_and_decorate(decorator, args, kwargs):
    """
    Helper for applying a decorator when it is applied directly, and also
    applying it when it is given arguments and then applied to a function.
    """
    # special behavior when invoked with only one non-keyword argument: act as
    # a normal decorator, decorating and returning that argument with
    # click.option
    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        return decorator(args[0])

    # if we're not doing that, we should see no positional args
    # the alternative behavior is to fall through and discard *args, but this
    # will probably confuse someone in the future when their arguments are
    # silently discarded
    elif len(args) != 0:
        raise ValueError("this decorator cannot take positional args")

    # final case: got 0 or more kwargs, no positionals
    # do the function-which-returns-a-decorator dance to produce a
    # new decorator based on the arguments given
    else:

        def inner_decorator(f):
            return decorator(f, **kwargs)

        return inner_decorator
