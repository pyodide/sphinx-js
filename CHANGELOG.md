## Changelog

### 5.0.1: (September 17th, 2025)
- Fixed a bug that comment of the arrow function in the interface is not rendered correctly.
  (pyodide/sphinx-js#284)

### 5.0.0: (July 2nd, 2025)

- Dropped support for Python 3.9 (pyodide/sphinx-js-fork#7)
- Dropped support for typedoc 0.15, added support for typedoc 0.25--0.28 (
  pyodide/sphinx-js-fork#11, pyodide/sphinx-js-fork#22,
  pyodide/sphinx-js-fork#31, pyodide/sphinx-js-fork#39,
  pyodide/sphinx-js-fork#41, pyodide/sphinx-js-fork#43
  pyodide/sphinx-js-fork#52, pyodide/sphinx-js-fork#53,
  pyodide/sphinx-js-fork#54, pyodide/sphinx-js-fork#174,
  #266)
- Added handling for TypeScript type parameters and type bounds.
  (pyodide/sphinx-js-fork#25)
- Only monkeypatch Sphinx classes when sphinx_js extension is used
  (pyodide/sphinx-js-fork#27)
- Allow using installation of `typedoc` or `jsdoc` from `node_modules`
  instead of requiring global install. (pyodide/sphinx-js-fork#33)
- Handle markdown style codepens correctly in typedoc comments.
  (pyodide/sphinx-js-fork#47)
- Added support for destructuring the documentation of keyword arguments in
  TypeScript using the `@destructure` tag or the
  `shouldDestructureArg` hook. (
  pyodide/sphinx-js-fork#48, pyodide/sphinx-js-fork#74,
  pyodide/sphinx-js-fork#75, pyodide/sphinx-js-fork#101,
  pyodide/sphinx-js-fork#128)
- Added rendering for cross references in TypeScript types. (
  pyodide/sphinx-js-fork#51, pyodide/sphinx-js-fork#56,
  pyodide/sphinx-js-fork#67, pyodide/sphinx-js-fork#81,
  pyodide/sphinx-js-fork#82, pyodide/sphinx-js-fork#83,
  pyodide/sphinx-js-fork#153, pyodide/sphinx-js-fork#160)
- Added rendering for function types in TypeScript documentation. (
  pyodide/sphinx-js-fork#55, pyodide/sphinx-js-fork#58,
  pyodide/sphinx-js-fork#59)
- Add async prefix to async functions (pyodide/sphinx-js-fork#65).
- Added the `sphinx-js_type` css class around all types in documentation. This
  allows applying custom css just to types (pyodide/sphinx-js-fork#85)
- Added `ts_type_bold` config option that applies css to `.sphinx-js_type`
  to render all types as bold.
- Added `js:automodule` directive (pyodide/sphinx-js-fork#108)
- Added `js:autosummary` directive (pyodide/sphinx-js-fork#109)
- Added rendering for `queryType` (e.g., `let y: typeof x;`)
  (pyodide/sphinx-js-fork#124)
- Added rendering for `typeOperator` (e.g., `let y: keyof x`)
  (pyodide/sphinx-js-fork#125)
- Fixed crash when objects are reexported. (pyodide/sphinx-js-fork#126)
- Added `jsdoc_tsconfig_path` which can specify the path to the
  `tsconfig.json` file that should be used. (pyodide/sphinx-js-fork#116)
- Added a `js:interface` directive (pyodide/sphinx-js-fork#138).
- Removed parentheses from xrefs to classes (pyodide/sphinx-js-fork#155).
- Added a `:js:typealias:` directive (pyodide/sphinx-js-fork#156).
- Added rendering for conditional, indexed access, inferred, mapped, optional,
  rest, and template litreal types (pyodide/sphinx-js-fork#157).
- Added readonly prefix to readonly properties (pyodide/sphinx-js-fork#158).

### 4.0.0: (December 23rd, 2024)

- Drop support for Python 3.8.
- Add support for Python 3.12 and 3.13.
- Add support for Sphinx 8.x.x.
- Get CI working again.
- Drop pin for MarkupSafe. (#244)
- Add dependabot checking for GitHub actions. (Christian Clauss)
- Fix wheel contents to not include tests. (#241)

Thank you to Will Kahn-Greene and Christian Clauss!

### 3.2.2: (September 20th, 2023)

- Remove Sphinx upper-bound requirement. (#227)
- Drop support for Python 3.7. (#228)

Thank you to Will Kahn-Greene!

### 3.2.1: (December 16th, 2022)

- Fix xrefs to static functions. (#178)
- Add support for jsdoc 4.0.0. (#215)

Thank you to xsjad0 and Will Kahn-Greene!

### 3.2.0: (December 13th, 2022)

- Add "static" in front of static methods.
- Pin Jinja2 and markupsafe versions. (#190)
- Track dependencies; do not read all documents. This improves speed of
  incremental updates. (#194)
- Support Python 3.10 and 3.11. (#186)
- Support Sphinx >= 4.1.0. (#209)
- Fix types warning for `js_source_path` configuration item. (#182)

Thank you Stefan 'hr' Berder, David Huggins-Daines, Nick Alexander,
mariusschenzle, Erik Rose, lonnen, and Will Kahn-Greene!

### 3.1.2: (April 15th, 2021)

- Remove our declared dependency on `docutils` to work around the way pip's
  greedy dependency resolver reacts to the latest version of Sphinx. pip
  fails when pip-installing sphinx-js because pip sees our "any version of
  docutils" declaration first (which resolves greedily to the latest version,
  0.17) but later encounters Sphinx's apparently new `<0.17` constraint and
  gives up. We can revert this when pip's `--use-feature=2020-resolver`
  becomes the default.

### 3.1.1: (March 23rd, 2021)

- Rewrite large parts of the suffix tree that powers path lookup. This fixes
  several crashes.

### 3.1: (September 10th, 2020)

- Re-architect language analysis. There is now a well-documented intermediate
  representation between JSDoc- and TypeDoc-emitted JSON and the renderers.
  This should make it much faster to merge PRs.
- Rewrite much of the TypeScript analysis engine so it feeds into the new IR.

  - TypeScript analysis used to crash if your codebase contained any
    overloaded functions. This no longer happens; we now arbitrarily use only
    the first function signature of each overloaded function.
  - Add support for static properties on TS classes.
  - Support variadic args in TS.
  - Support intersection types (`foo & bar`) in TS.
  - Remove the "exported from" module links from classes and interfaces.
    Functions never had them. Let's see if we miss them.
  - Pathnames for TypeScript objects no longer spuriously use `~` after the
    filename path segment; now they use `.` as in JS.
  - More generally, TS pathnames are now just like JS ones. There is no more
    `external:` prefix in front of filenames or `module:` in front of
    namespace names.
  - TS analyzer no longer cares with the current working directory is.
  - Tests now assert only what they care about rather than being brittle to
    the point of prohibiting any change.

- No longer show args in the arg list that are utterly uninformative, lacking
  both description and type info.
- Class attributes are now listed before methods unless manally ordered with
  `:members:`.

### 3.0.1: (August 10th, 2020)

- Don't crash when encountering a `../` prefix on an object path. This can
  happen behind the scenes when `root_for_relative_js_paths` is set inward
  of the JS code.

### 3.0: (July 14th, 2020)

- Make compatible with Sphinx 3, which requires Python 3.
- Drop support for Python 2.
- Make sphinx-js not care what the current working directory is, except for
  the TypeScript analyzer, which needs further work.
- Properly RST-escape return types.

### 2.8: (September 16th, 2019)

- Display generic TypeScript types properly. Make fields come before methods.
  (Paul Grau)
- Combine constructor and class documentation at the top TypeScript classes.
  (Sebastian Weigand)
- Switch to pytest as the testrunner. (Sebastian Weigand)
- Add optional caching of JSDoc output, for large codebases. (Patrick Browne)
- Fix the display of union types in TypeScript. (Sebastian Weigand)
- Fix parsing breakage that began in typedoc 0.14.0. (Paul Grau)
- Fix a data-intake crash with TypeScript. (Cristiano Santos)

### 2.7.1: (November 16th, 2018)

- Fix a crash that would happen sometimes with UTF-8 on Windows. #67.
- Always use conf.py's dir for JSDoc's working dir. #78. (Thomas Khyn)

### 2.7: (August 2nd, 2018))

- Add experimental TypeScript support. (Wim Yedema)

### 2.6: (July 26th, 2018)

- Add support for `@deprecated` and `@see`. (David Li)
- Notice and document JS variadic params nicely. (David Li)
- Add linter to codebase.

### 2.5: (April 20th, 2018)

- Use documented `@params` to help fill out the formal param list for a
  function. This keeps us from missing params that use destructuring. (flozz)
- Improve error reporting when JSDoc is missing.
- Add extracted default values to generated formal param lists. (flozz and
  erikrose)

### 2.4: (March 21, 2018)

- Support the `@example` tag. (lidavidm)
- Work under Windows. Before, we could hardly find any documentation. (flozz)
- Properly unwrap multiple-line JSDoc tags, even if they have Windows line
  endings. (Wim Yedema)
- Drop support for Python 3.3, since Sphinx has also done so.
- Fix build-time crash when using recommonmark (for Markdown support) under
  Sphinx >=1.7.1. (jamrizzi)

### 2.3.1: (January 11th, 2018)

- Find the `jsdoc` command on Windows, where it has a different name. Then
  patch up process communication so it doesn't hang.

### 2.3: (November 1st, 2017)

- Add the ability to say "\*" within the `autoclass :members:` option,
  meaning "and all the members that I didn't explicitly list".

### 2.2: (October 10th, 2017)

- Add `autofunction` support for `@callback` tags. (krassowski)
- Add experimental `autofunction` support for `@typedef` tags. (krassowski)
- Add a nice error message for when JSDoc can't find any JS files.
- Pin six more tightly so `python_2_unicode_compatible` is sure to be around.

### 2.1: (August 30th, 2017)

- Allow multiple folders in `js_source_path`. This is useful for gradually
  migrating large projects, one folder at a time, to JSDoc. Introduce
  `root_for_relative_js_paths` to keep relative paths unambiguous in the
  face of multiple source paths.
- Aggregate PathTaken errors, and report them all at once. This means you
  don't have to run JSDoc repeatedly while cleaning up large projects.
- Fix a bytes-vs-strings issue that crashed on versions of Python 3 before
  3.6. (jhkennedy)
- Tolerate JS files that have filename extensions other than ".js". Before,
  when combined with custom JSDoc configuration that ingested such files,
  incorrect object pathnames were generated, which led to spurious "No JSDoc
  documentation was found for object ..." errors.

### 2.0.1: (July 13th, 2017)

- Fix spurious syntax errors while loading large JSDoc output by writing it
  to a temp file first. (jhkennedy)

### 2.0: (May 4th, 2017)

- Deal with ambiguous object paths. Symbols with identical JSDoc longnames
  (such as two top-level things called "foo" in different files) will no
  longer have one shadow the other. Introduce an unambiguous path convention
  for referring to objects. Add a real parser to parse them rather than the
  dirty tricks we were using before. Backward compatibility breaks a little,
  because ambiguous references are now a fatal error, rather than quietly
  referring to the last definition JSDoc happened to encounter.
- Index everything into a suffix tree so you can use any unique path suffix
  to refer to an object.
- Other fallout of having a real parser:

  - Stop supporting "-" as a namepath separator.
  - No longer spuriously translate escaped separators in namepaths into dots.
  - Otherwise treat paths and escapes properly. For example, we can now
    handle symbols that contain "(".

- Fix KeyError when trying to gather the constructor params of a plain old
  object labeled as a `@class`.

### 1.5.2: (March 22th, 2017)

- Fix crash while warning that a specified longname isn't found.

### 1.5.1: (March 20th, 2017)

- Sort `:members:` alphabetically when an order is not explicitly specified.

### 1.5: (March 17th, 2017)

- Add `:members:` option to `autoclass`.
- Add `:private-members:` and `:exclude-members:` options to go with it.
- Significantly refactor to allow directive classes to talk to each other.

### 1.4: (March 10th, 2017)

- Add `jsdoc_config_path` option.

### 1.3.1: (March 6th, 2017)

- Tolerate @args and other info field lines that are wrapped in the source
  code.
- Cite the file and line of the source comment in Sphinx-emitted warnings and
  errors.

### 1.3: (February 21st, 2017)

- Add `autoattribute` directive.

### 1.2: (February 14th, 2017)

- Always do full rebuilds; don't leave pages stale when JS code has changed
  but the RSTs have not.
- Make Python-3-compatible.
- Add basic `autoclass` directive.

### 1.1: (February 13th, 2017)

- Add `:short-name:` option.

### 1.0: (February 7th, 2017)

- Initial release, with just `js:autofunction`
