from distutils.version import LooseVersion

# single source of truth for package version,
# see https://packaging.python.org/en/latest/single_source_version/
__version__ = "1.14.0"

# app name to send as part of SDK requests
app_name = "Globus CLI v{}".format(__version__)


# pull down version data from PyPi
def get_versions():
    """
    Wrap in a function to ensure that we don't run this every time a CLI
    command runs (yuck!)

    Also protects import of `requests` from issues when grabbed by setuptools.
    More on that inline
    """
    # import in the func (rather than top-level scope) so that at setup time,
    # `requests` isn't required -- otherwise, setuptools will fail to run
    # because requests isn't installed yet.
    import requests

    try:
        version_data = requests.get(
            "https://pypi.python.org/pypi/globus-cli/json"
        ).json()
        latest = max(LooseVersion(v) for v in version_data["releases"])
        return latest, LooseVersion(__version__)
    # if the fetch from pypi fails
    except requests.RequestException:
        return None, LooseVersion(__version__)
