"""Test against sample modules using the ignore option in all supported config sources."""

import os
from distutils.spawn import find_executable

import flake8.main
import pytest

from tests import check_output, STDOUT

EXPECTED = """\
stdin:1:1: D100 Missing docstring in public module
stdin:5:1: D300 Use \"\"\"triple double quotes\"\"\" (found '''-quotes)
stdin:5:1: D401 First line should be in imperative mood ('Print', not 'Prints')
stdin:14:1: D203 1 blank line required before class docstring (found 0)
stdin:14:1: D204 1 blank line required after class docstring (found 0)
stdin:14:1: D300 Use \"\"\"triple double quotes\"\"\" (found '''-quotes)
"""


@pytest.mark.parametrize('stdin', ['', 'sample.py'])
@pytest.mark.parametrize('which_cfg', ['tox.ini', 'tox.ini flake8', 'setup.cfg', '.pep257'])
def test_direct(capsys, monkeypatch, tempdir, stdin, which_cfg):
    """Test by calling flake8.main.main() using the same running python process.

    :param capsys: pytest fixture.
    :param monkeypatch: pytest fixture.
    :param tempdir: conftest fixture.
    :param str ignore: Config value for ignore option.
    :param str stdin: Pipe this file to stdin of flake8.
    :param str which_cfg: Which config file to test with.
    """
    # Prepare.
    monkeypatch.chdir(tempdir.join('empty' if stdin else ''))
    monkeypatch.setattr('sys.argv', ['flake8', '-' if stdin else '.', '-j1'])
    if stdin:
        monkeypatch.setattr('pep8.stdin_get_value', lambda: tempdir.join(stdin).read())

    # Write configuration.
    cfg = which_cfg.split()
    section = cfg[1] if len(cfg) > 1 else 'pep257'
    tempdir.join('empty' if stdin else '', cfg[0]).write('[{0}]\nmatch = "(?!sample).*\.py"\n'.format(section))

    # Execute.
    if stdin:
        with pytest.raises(SystemExit):
            flake8.main.main()
    else:
        # pep257 shouldn't run since the file doesn't match
        flake8.main.main()
    out, err = capsys.readouterr()
    assert not err

    # Clean.
    if stdin:
        expected = EXPECTED
    else:
        # pep257 shouldn't run since the file doesn't match
        expected = ''
    out = '\n'.join(l.rstrip() for l in out.splitlines())

    assert out == expected


@pytest.mark.parametrize('stdin', ['', 'sample.py'])
@pytest.mark.parametrize('which_cfg', ['tox.ini', 'tox.ini flake8', 'setup.cfg', '.pep257'])
def test_subprocess(tempdir, stdin, which_cfg):
    """Test by calling flake8 through subprocess using a dedicated python process.

    :param tempdir: conftest fixture.
    :param str ignore: Config value for ignore option.
    :param str stdin: Pipe this file to stdin of flake8.
    :param str which_cfg: Which config file to test with.
    """
    # Prepare.
    cwd = str(tempdir.join('empty' if stdin else ''))
    stdin_handle = tempdir.join(stdin).open() if stdin else None

    # Write configuration.
    cfg = which_cfg.split()
    section = cfg[1] if len(cfg) > 1 else 'pep257'
    tempdir.join('empty' if stdin else '', cfg[0]).write('[{0}]\nmatch = "(?!sample).*\.py"\n'.format(section))

    # Execute.
    command = [find_executable('flake8'), '--exit-zero', '-' if stdin else '.']
    environ = os.environ.copy()
    environ['COV_CORE_DATAFILE'] = ''  # Disable pytest-cov's subprocess coverage feature. Doesn't work right now.
    out = check_output(command, stderr=STDOUT, cwd=cwd, stdin=stdin_handle, env=environ).decode('utf-8')

    # Clean.
    if stdin:
        expected = EXPECTED
    else:
        # pep257 shouldn't run since the file doesn't match
        expected = ''
    out = '\n'.join(l.rstrip() for l in out.splitlines())

    assert out == expected
