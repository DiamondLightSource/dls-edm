import subprocess
import sys

from dls_edm import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "dls_edm", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
