__all__ = ["EXPLICIT_NULL"]


# this object is a sentinel value used to disambiguate values which are being
# intentionally nulled from values which are incidentally `None` because no
# argument was provided
EXPLICIT_NULL = object()
