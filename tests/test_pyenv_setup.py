import pathlib


def test_python_version_file_exists_and_is_31113():
    p = pathlib.Path(__file__).resolve().parents[1] / ".python-version"
    assert p.exists(), ".python-version file is missing in project root"
    content = p.read_text().strip()
    assert content == "3.11.13", f"Expected '3.11.13' in .python-version, got: {content}"
