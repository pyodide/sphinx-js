extensions = ["sphinx_js"]

# Minimal stuff needed for Sphinx to work:
source_suffix = ".rst"
master_doc = "index"
author = "Nick Alexander"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
js_language = "typescript"
js_source_path = [".", "inner"]
root_for_relative_js_paths = "."
# Temp directories on macOS have internal directories starting with
# "_", running afoul of https://github.com/jsdoc/jsdoc/issues/1328.
jsdoc_config_path = "tsconfig.json"
