from __future__ import unicode_literals

import json

import click
import six
from globus_sdk import GlobusResponse

from globus_cli.safeio.awscli_text import unix_formatted_print
from globus_cli.safeio.get_option_vals import (
    get_jmespath_expression,
    outformat_is_json,
    outformat_is_unix,
)

# make sure this is a tuple
# if it's a list, pylint will freak out
__all__ = (
    "formatted_print",
    "FORMAT_SILENT",
    "FORMAT_JSON",
    "FORMAT_TEXT_TABLE",
    "FORMAT_TEXT_RECORD",
    "FORMAT_TEXT_RAW"
    # NOTE: we don't export FORMAT_TEXT_CUSTOM as actually passing it is
    # incorrect usage -- it's used internally, but similarly to the other
    # format constants
)


FORMAT_SILENT = "silent"
FORMAT_JSON = "json"
FORMAT_TEXT_TABLE = "text_table"
FORMAT_TEXT_RECORD = "text_record"
FORMAT_TEXT_RAW = "text_raw"
FORMAT_TEXT_CUSTOM = "text_custom"


def _key_to_keyfunc(k):
    """
    We allow for 'keys' which are functions that map columns onto value
    types -- they may do formatting or inspect multiple values on the
    object. In order to support this, wrap string keys in a simple function
    that does the natural lookup operation, but return any functions we
    receive as they are.
    """
    # if the key is a string, then the "keyfunc" is just a basic lookup
    # operation -- return that
    if isinstance(k, six.string_types):

        def lookup(x):
            return x[k]

        return lookup
    # otherwise, the key must be a function which is executed on the item
    # to produce a value -- return it verbatim
    return k


def _jmespath_preprocess(res):
    jmespath_expr = get_jmespath_expression()

    if isinstance(res, GlobusResponse):
        res = res.data

    if not isinstance(res, six.string_types):
        if jmespath_expr is not None:
            res = jmespath_expr.search(res)

    return res


def print_json_response(res):
    res = _jmespath_preprocess(res)
    res = json.dumps(res, indent=2, separators=(",", ": "), sort_keys=True)
    click.echo(res)


def print_unix_response(res):
    res = _jmespath_preprocess(res)
    try:
        unix_formatted_print(res)
    # Attr errors indicate that we got data which cannot be unix formatted
    # likely a scalar + non-scalar in an array, though there may be other cases
    # print good error and exit(2) (Count this as UsageError!)
    except AttributeError:
        click.echo(
            "UNIX formatting of output failed."
            "\n  "
            "This usually means that data has a structure which cannot be "
            "handled by the UNIX formatter."
            "\n  "
            "To avoid this error in the future, ensure that you query the "
            'exact properties you want from output data with "--jmespath"',
            err=True,
        )
        click.get_current_context().exit(2)


def colon_formatted_print(data, named_fields):
    maxlen = max(len(n) for n, f in named_fields) + 1
    for name, field in named_fields:
        field_keyfunc = _key_to_keyfunc(field)
        click.echo("{} {}".format((name + ":").ljust(maxlen), field_keyfunc(data)))


def print_table(iterable, headers_and_keys, print_headers=True):
    # the iterable may not be safe to walk multiple times, so we must walk it
    # only once -- however, to let us write things naturally, convert it to a
    # list and we can assume it is safe to walk repeatedly
    iterable = list(iterable)

    # extract headers and keys as separate lists
    headers = [h for (h, k) in headers_and_keys]
    keys = [k for (h, k) in headers_and_keys]

    # convert all keys to keyfuncs
    keyfuncs = [_key_to_keyfunc(key) for key in keys]

    # use the iterable to find the max width of an element for each column, in
    # the same order as the headers_and_keys array
    # use a special function to handle empty iterable
    def get_max_colwidth(kf):
        def _safelen(x):
            try:
                return len(x)
            except TypeError:
                return len(str(x))

        lengths = [_safelen(kf(i)) for i in iterable]
        if not lengths:
            return 0
        else:
            return max(lengths)

    widths = [get_max_colwidth(kf) for kf in keyfuncs]
    # handle the case in which the column header is the widest thing
    widths = [max(w, len(h)) for w, h in zip(widths, headers)]

    # create a format string based on column widths
    format_str = " | ".join("{:" + str(w) + "}" for w in widths)

    def none_to_null(val):
        if val is None:
            return "NULL"
        return val

    # print headers
    if print_headers:
        click.echo(format_str.format(*[h for h in headers]))
        click.echo(format_str.format(*["-" * w for w in widths]))
    # print the rows of data
    for i in iterable:
        click.echo(format_str.format(*[none_to_null(kf(i)) for kf in keyfuncs]))


def formatted_print(
    response_data,
    simple_text=None,
    text_preamble=None,
    text_epilog=None,
    text_format=FORMAT_TEXT_TABLE,
    json_converter=None,
    fields=None,
    response_key=None,
):
    """
    A generic output formatter. Consumes the following pieces of data:

    ``response_data`` is a dict or GlobusResponse object. It contains either an
    API response or synthesized data for printing.

    ``simple_text`` is a text override -- normal printing is skipped and this
    string is printed instead (text output only)
    ``text_preamble`` is text which prints before normal printing (text output
    only)
    ``text_epilog`` is text which prints after normal printing (text output
    only)
    ``text_format`` is one of the FORMAT_TEXT_* constants OR a callable which
    takes ``response_data`` and prints output. Note that when a callable is
    given, it does the actual printing

    ``json_converter`` is a callable that does preprocessing of JSON output. It
    must take ``response_data`` and produce another dict or dict-like object
    (json/unix output only)

    ``fields`` is an iterable of (fieldname, keyfunc) tuples. When keyfunc is
    a string, it is implicitly converted to `lambda x: x[keyfunc]` (text output
    only)

    ``response_key`` is a key into the data to print. When used with table
    printing, it must get an iterable out, and when used with raw printing, it
    gets a string. Necessary for certain formats like text table (text output
    only)
    """

    def _assert_fields():
        if fields is None:
            raise ValueError(
                "Internal Error! Output format requires fields; none given. "
                "You can workaround this error by using `--format JSON`"
            )

    def _print_as_json():
        print_json_response(
            json_converter(response_data) if json_converter else response_data
        )

    def _print_as_unix():
        print_unix_response(
            json_converter(response_data) if json_converter else response_data
        )

    def _print_as_text():
        # if we're given simple text, print that and exit
        if simple_text is not None:
            click.echo(simple_text)
            return

        # if there's a preamble, print it beofre any other text
        if text_preamble is not None:
            click.echo(text_preamble)

        # if there's a response key, key into it
        data = response_data if response_key is None else response_data[response_key]

        #  do the various kinds of printing
        if text_format == FORMAT_TEXT_TABLE:
            _assert_fields()
            print_table(data, fields)
        elif text_format == FORMAT_TEXT_RECORD:
            _assert_fields()
            colon_formatted_print(data, fields)
        elif text_format == FORMAT_TEXT_RAW:
            click.echo(data)
        elif text_format == FORMAT_TEXT_CUSTOM:
            _custom_text_formatter(data)

        # if there's an epilog, print it after any text
        if text_epilog is not None:
            click.echo(text_epilog)

    if isinstance(text_format, six.string_types):
        text_format = text_format
        _custom_text_formatter = None
    else:
        _custom_text_formatter = text_format
        text_format = FORMAT_TEXT_CUSTOM

    if outformat_is_json():
        _print_as_json()
    elif outformat_is_unix():
        _print_as_unix()
    else:
        # silent does nothing
        if text_format == FORMAT_SILENT:
            return
        _print_as_text()
