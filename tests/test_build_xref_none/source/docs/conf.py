extensions = ["sphinx_js"]

js_language = "typescript"
js_source_path = ["../main.ts"]
root_for_relative_js_paths = "../"

suppress_warnings = ["config.cache"]


def ts_type_xref_formatter(config, xref):
    """Always return an invalid :js:None: role to test error propagation."""
    return f":js:None:`{xref.name}`"
