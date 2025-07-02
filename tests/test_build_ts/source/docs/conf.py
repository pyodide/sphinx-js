extensions = ["sphinx_js"]

# Minimal stuff needed for Sphinx to work:
source_suffix = ".rst"
master_doc = "index"
author = "Erik Rose"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

jsdoc_config_path = "../typedoc.json"
jsdoc_tsconfig_path = "../tsconfig.json"
js_language = "typescript"
from sphinx.util import rst

from sphinx_js.ir import TypeXRef, TypeXRefInternal


def ts_type_xref_formatter(config, xref: TypeXRef) -> str:
    if isinstance(xref, TypeXRefInternal):
        name = rst.escape(xref.name)
        return f":js:{xref.kind}:`{name}`"
    else:
        return xref.name
