from reviewer.diff import FileDiff
from reviewer.filtering import DEFAULT_IGNORE, filter_files, parse_patterns


def fd(path: str, binary: bool = False) -> FileDiff:
    return FileDiff(path=path, is_binary=binary)


def test_default_patterns_ignore_noise():  # AC1
    paths = [
        "poetry.lock",
        "web/package-lock.json",
        "composer.lock",
        "dist/app/bundle.js",
        "static/app.min.js",
        "img/logo.svg",
        "app/migrations/0002_auto_20240101.py",
    ]
    kept, ignored = filter_files([fd(p) for p in paths + ["src/app.py"]])
    assert [f.path for f in kept] == ["src/app.py"]
    assert [f.path for f in ignored] == paths
    assert DEFAULT_IGNORE


def test_custom_patterns_replace_defaults():  # AC2
    kept, ignored = filter_files([fd("a.lock"), fd("docs/x.md")], ["docs/**"])
    assert [f.path for f in kept] == ["a.lock"]
    assert [f.path for f in ignored] == ["docs/x.md"]
    assert parse_patterns("a, b ,") == ["a", "b"]
    assert parse_patterns("") == []


def test_binary_ignored_and_order_preserved():  # AC3
    kept, ignored = filter_files([fd("z.py"), fd("pic.png", binary=True), fd("a.py")])
    assert [f.path for f in kept] == ["z.py", "a.py"]
    assert [f.path for f in ignored] == ["pic.png"]
