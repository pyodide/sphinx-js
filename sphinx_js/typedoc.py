"""Converter from TypeDoc output to IR format"""

import os
import pathlib
import posixpath
import re
import subprocess
from collections.abc import Iterable, Iterator, Sequence
from errno import ENOENT
from functools import cache
from json import load
from operator import attrgetter
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Literal

from sphinx.application import Sphinx
from sphinx.errors import SphinxError

from . import ir
from .analyzer_utils import Command, search_node_modules
from .suffix_tree import SuffixTree

__all__ = ["Analyzer"]

MIN_TYPEDOC_VERSION = (0, 25, 0)


@cache
def typedoc_version_info(typedoc: str) -> tuple[tuple[int, ...], tuple[int, ...]]:
    command = Command("node")
    command.add(typedoc, "--version")
    result = subprocess.run(
        command.make(),
        capture_output=True,
        encoding="utf8",
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    m = re.search(r"TypeDoc ([0-9]+\.[0-9]+\.[0-9]+)", lines[0])
    assert m
    typedoc_version = tuple(int(x) for x in m.group(1).split("."))
    m = re.search(r"TypeScript ([0-9]+\.[0-9]+\.[0-9]+)", lines[1])
    assert m
    typescript_version = tuple(int(x) for x in m.group(1).split("."))
    return typedoc_version, typescript_version


def version_to_str(t: Sequence[int]) -> str:
    return ".".join(str(x) for x in t)


def typedoc_output(
    abs_source_paths: Sequence[str],
    base_dir: str,
    sphinx_conf_dir: str | pathlib.Path,
    typedoc_config_path: str | None,
    tsconfig_path: str | None,
    ts_sphinx_js_config: str | None,
) -> tuple[list[ir.TopLevelUnion], dict[str, Any]]:
    """Return the loaded JSON output of the TypeDoc command run over the given
    paths."""
    typedoc = search_node_modules("typedoc", "typedoc/bin/typedoc", sphinx_conf_dir)
    typedoc_version, _ = typedoc_version_info(typedoc)
    if typedoc_version < MIN_TYPEDOC_VERSION:
        raise RuntimeError(
            f"Typedoc version {version_to_str(typedoc_version)} is too old, minimum required is {version_to_str(MIN_TYPEDOC_VERSION)}"
        )

    env = os.environ.copy()
    env["TYPEDOC_NODE_MODULES"] = str(Path(typedoc).parents[3].resolve())
    command = Command("npx")
    command.add("tsx@4.15.8")
    dir = Path(__file__).parent.resolve() / "js"
    command.add("--tsconfig", str(dir / "tsconfig.json"))
    command.add("--import", "file:///" + str(dir / "registerImportHook.mjs"))
    command.add(str(dir / "main.ts"))
    if ts_sphinx_js_config:
        command.add("--sphinxJsConfig", ts_sphinx_js_config)
    command.add("--entryPointStrategy", "expand")

    if typedoc_config_path:
        typedoc_config_path = str(
            (Path(sphinx_conf_dir) / typedoc_config_path).absolute()
        )
        command.add("--options", typedoc_config_path)

    if tsconfig_path:
        tsconfig_path = str((Path(sphinx_conf_dir) / tsconfig_path).absolute())
        command.add("--tsconfig", tsconfig_path)

    command.add("--basePath", base_dir)
    command.add("--excludePrivate", "false")

    with NamedTemporaryFile(mode="w+b", delete=False) as temp:
        source_paths = abs_source_paths
        if os.name == "nt":
            source_paths = map(
                lambda path: str(posixpath.join(*str(path).split(os.sep))),
                abs_source_paths,
            )

        command.add("--json", temp.name, *source_paths)
        try:
            subprocess.run(command.make(), check=True, env=env)
        except OSError as exc:
            if exc.errno == ENOENT:
                raise SphinxError(
                    '%s was not found. Install it using "npm install -g typedoc".'
                    % command.program
                )
            else:
                raise
        # typedoc emits a valid JSON file even if it finds no TS files in the dir:
        json_ir, extra_data = load(temp)
        return ir.json_to_ir(json_ir), extra_data


class Analyzer:
    _objects_by_path: SuffixTree[ir.TopLevel]
    _modules_by_path: SuffixTree[ir.Module]
    _extra_data: dict[str, Any]

    def __init__(
        self, objects: Sequence[ir.TopLevel], extra_data: dict[str, Any], base_dir: str
    ) -> None:
        self._extra_data = extra_data
        self._base_dir = base_dir
        self._objects_by_path = SuffixTree()
        self._objects_by_path.add_many((obj.path.segments, obj) for obj in objects)
        modules = self._create_modules(objects)
        self._modules_by_path = SuffixTree()
        self._modules_by_path.add_many((obj.path.segments, obj) for obj in modules)

    def get_object(
        self,
        path_suffix: Sequence[str],
        as_type: Literal["function", "class", "attribute"] = "function",
    ) -> ir.TopLevel:
        """Return the IR object with the given path suffix.

        :arg as_type: Ignored
        """
        return self._objects_by_path.get(path_suffix)

    @classmethod
    def from_disk(
        cls, abs_source_paths: Sequence[str], app: Sphinx, base_dir: str
    ) -> "Analyzer":
        json, extra_data = typedoc_output(
            abs_source_paths,
            base_dir=base_dir,
            sphinx_conf_dir=app.confdir,
            typedoc_config_path=app.config.jsdoc_config_path,
            tsconfig_path=app.config.jsdoc_tsconfig_path,
            ts_sphinx_js_config=app.config.ts_sphinx_js_config,
        )
        return cls(json, extra_data, base_dir)

    def _get_toplevel_objects(
        self, ir_objects: Sequence[ir.TopLevel]
    ) -> Iterator[tuple[ir.TopLevel, str, str]]:
        for obj in ir_objects:
            if not obj.documentation_root:
                continue
            assert obj.deppath
            yield (obj, obj.deppath, obj.kind)

    def _create_modules(self, ir_objects: Sequence[ir.TopLevel]) -> Iterable[ir.Module]:
        """Search through the doclets generated by JsDoc and categorize them by
        summary section. Skip docs labeled as "@private".
        """
        modules = {}
        singular_kind_to_plural_kind = {
            "class": "classes",
            "interface": "interfaces",
            "function": "functions",
            "attribute": "attributes",
            "typeAlias": "type_aliases",
        }
        for obj, path, kind in self._get_toplevel_objects(ir_objects):
            pathparts = path.split("/")
            for i in range(len(pathparts) - 1):
                pathparts[i] += "/"
            if path not in modules:
                modules[path] = ir.Module(
                    filename=path, deppath=path, path=ir.Pathname(pathparts), line=1
                )
            mod = modules[path]
            getattr(mod, singular_kind_to_plural_kind[kind]).append(obj)

        for mod in modules.values():
            mod.attributes = sorted(mod.attributes, key=attrgetter("name"))
            mod.functions = sorted(mod.functions, key=attrgetter("name"))
            mod.classes = sorted(mod.classes, key=attrgetter("name"))
            mod.interfaces = sorted(mod.interfaces, key=attrgetter("name"))
            mod.type_aliases = sorted(mod.type_aliases, key=attrgetter("name"))
        return modules.values()
