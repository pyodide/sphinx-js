from pathlib import Path
from textwrap import dedent

import nox
from nox.sessions import Session

PROJECT_ROOT = Path(__file__).parent


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session: Session) -> None:
    session.install(".[test]")
    venvroot = Path(session.bin).parent
    (venvroot / "node_modules").mkdir()
    with session.chdir(venvroot):
        session.run(
            "npm", "i", "--no-save", "jsdoc@4.0.0", "typedoc@0.25", external=True
        )
    session.run(
        "pytest",
        "--junitxml=test-results.xml",
        "--cov=sphinx_js",
        "--cov-report",
        "xml",
    )


@nox.session(python=["3.12"])
@nox.parametrize("typedoc", ["0.25", "0.26", "0.27", "0.28"])
def test_typedoc(session: Session, typedoc: str) -> None:
    # Install python dependencies
    session.install(".[test]")
    venvroot = Path(session.bin).parent
    node_modules = (venvroot / "node_modules").resolve()
    node_modules.mkdir()
    with session.chdir(venvroot):
        # Install node dependencies
        session.run(
            "npm",
            "i",
            "--no-save",
            "tsx",
            "jsdoc@4.0.0",
            f"typedoc@{typedoc}",
            external=True,
        )
        # Run typescript tests
        test_file = (PROJECT_ROOT / "tests/test.ts").resolve()
        register_import_hook = PROJECT_ROOT / "sphinx_js/js/registerImportHook.mjs"
        ts_tests = Path(venvroot / "ts_tests")
        # Write script to a file so that it is easy to rerun without reinstalling dependencies.
        ts_tests.write_text(
            dedent(
                f"""\
                #!/bin/sh
                npx typedoc --version
                TYPEDOC_NODE_MODULES={venvroot} node --import {register_import_hook} --import {node_modules/"tsx/dist/loader.mjs"} --test {test_file}
                """
            )
        )
        ts_tests.chmod(0o777)
        session.run(ts_tests, external=True)

    # Run Python tests
    session.run("pytest", "--junitxml=test-results.xml", "-k", "not js")


@nox.session(python=["3.12"])
def test_sphinx_6(session: Session) -> None:
    session.install("sphinx<7")
    session.install(".[test]")
    venvroot = Path(session.bin).parent
    (venvroot / "node_modules").mkdir()
    with session.chdir(venvroot):
        session.run(
            "npm", "i", "--no-save", "jsdoc@4.0.0", "typedoc@0.25", external=True
        )
    session.run("pytest", "--junitxml=test-results.xml", "-k", "not js")
