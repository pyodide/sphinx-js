import subprocess
from pathlib import Path

import pytest
from conftest import TYPEDOC_VERSION
from sphinx.errors import SphinxError

from sphinx_js.analyzer_utils import search_node_modules


@pytest.fixture(autouse=True)
def clear_node_modules_env(monkeypatch):
    monkeypatch.delenv("SPHINX_JS_NODE_MODULES")


@pytest.fixture
def global_install(tmp_path_factory, monkeypatch):
    tmpdir = tmp_path_factory.mktemp("my_program_global")
    my_program = tmpdir / "my_program"
    my_program.write_text("")
    my_program.chmod(0o777)
    monkeypatch.setenv("PATH", str(tmpdir), prepend=":")
    return tmpdir


@pytest.fixture
def no_local_install(tmp_path_factory):
    my_program = tmp_path_factory.mktemp("my_program_local")
    working_dir = my_program / "a" / "b" / "c"
    return working_dir


my_prog_path = Path("my_program/sub/bin.js")


@pytest.fixture
def local_install(no_local_install):
    working_dir = no_local_install
    bin_path = working_dir.parents[1] / "node_modules" / my_prog_path
    bin_path.parent.mkdir(parents=True)
    bin_path.write_text("")
    return (working_dir, bin_path)


@pytest.fixture
def env_install(monkeypatch):
    env_path = Path("/a/b/c")
    monkeypatch.setenv("SPHINX_JS_NODE_MODULES", str(env_path))
    return env_path / my_prog_path


def test_global(global_install, no_local_install):
    # If no env or local, use global
    working_dir = no_local_install
    assert search_node_modules("my_program", my_prog_path, working_dir) == str(
        global_install / "my_program"
    )


def test_node_modules1(global_install, local_install):
    # If local and global, use local
    [working_dir, bin_path] = local_install
    assert search_node_modules("my_program", my_prog_path, working_dir) == str(bin_path)


def test_node_modules2(local_install):
    # If local only, use local
    [working_dir, bin_path] = local_install
    assert search_node_modules("my_program", my_prog_path, working_dir) == str(bin_path)


def test_env1(env_install):
    # If env only, use env
    assert search_node_modules("my_program", my_prog_path, "/x/y/z") == str(env_install)


def test_env2(env_install, local_install, global_install):
    # If env, local, and global, use env
    [working_dir, _] = local_install
    assert search_node_modules("my_program", my_prog_path, working_dir) == str(
        env_install
    )


def test_err():
    with pytest.raises(
        SphinxError,
        match='my_program was not found. Install it using "npm install my_program"',
    ):
        search_node_modules("my_program", my_prog_path, "/a/b/c")


@pytest.mark.xfail(reason="Isn't working right now. Not sure why.")
def test_global_install(tmp_path_factory, monkeypatch):
    tmpdir = tmp_path_factory.mktemp("global_root")
    tmpdir2 = tmp_path_factory.mktemp("blah")
    monkeypatch.setenv("npm_config_prefix", str(tmpdir))
    monkeypatch.setenv("PATH", str(tmpdir / "bin"), prepend=":")
    version = ".".join(str(x) for x in TYPEDOC_VERSION)
    subprocess.run(["npm", "i", "-g", f"typedoc@{version}", "typescript"])
    typedoc = search_node_modules("typedoc", "typedoc/bin/typedoc", str(tmpdir2))
    monkeypatch.setenv("TYPEDOC_NODE_MODULES", str(Path(typedoc).parents[3]))
    dir = Path(__file__).parents[1].resolve() / "sphinx_js/js"

    res = subprocess.run(
        [
            "npx",
            "tsx@4.15.8",
            "--import",
            dir / "registerImportHook.mjs",
            dir / "main.ts",
            "--version",
        ],
        capture_output=True,
        encoding="utf8",
    )
    print(res.stdout)
    print(res.stderr)
    res.check_returncode()
    assert f"TypeDoc {version}" in res.stdout
