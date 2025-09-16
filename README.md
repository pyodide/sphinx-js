# sphinx-js

## Why

When you write a JavaScript library, how do you explain it to people? If it's a
small project in a domain your users are familiar with, JSDoc's alphabetical
list of routines might suffice. But in a larger project, it is useful to
intersperse prose with your API docs without having to copy and paste things.

sphinx-js lets you use the industry-leading [Sphinx](https://sphinx-doc.org/)
documentation tool with JS projects. It provides a handful of directives,
patterned after the Python-centric [autodoc](https://www.sphinx-doc.org/en/latest/ext/autodoc.html) ones, for pulling
JSDoc-formatted documentation into reStructuredText pages. And, because you can
keep using JSDoc in your code, you remain compatible with the rest of your JS
tooling, like Google's Closure Compiler.

sphinx-js also works with TypeScript, using the TypeDoc tool in place of JSDoc
and emitting all the type information you would expect.

## Setup

1. Install JSDoc (or TypeDoc if you're writing TypeScript):

   ```bash
   npm install jsdoc
   ```

   or:

   ```bash
   npm install typedoc@0.28
   ```

   JSDoc 3.6.3 and 4.0.0 and TypeDoc 0.25--0.28 are known to work.

2. Install sphinx-js, which will pull in Sphinx itself as a dependency:

   ```bash
   pip install sphinx-js
   ```

3. Make a documentation folder in your project by running `sphinx-quickstart`
   and answering its questions:

   ```bash
   cd my-project
   sphinx-quickstart
   ```

   ```
   Please enter values for the following settings (just press Enter to
   accept a default value, if one is given in brackets).

   Selected root path: .

   You have two options for placing the build directory for Sphinx output.
   Either, you use a directory "_build" within the root path, or you separate
   "source" and "build" directories within the root path.
   > Separate source and build directories (y/n) [n]:

   The project name will occur in several places in the built documentation.
   > Project name: My Project
   > Author name(s): Fred Fredson
   > Project release []: 1.0

   If the documents are to be written in a language other than English,
   you can select a language here by its language code. Sphinx will then
   translate text that it generates into that language.

   For a list of supported codes, see
   https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-language.
   > Project language [en]:

   Selected root path: .

   You have two options for placing the build directory for Sphinx output.
   Either, you use a directory "_build" within the root path, or you separate
   "source" and "build" directories within the root path.
   > Separate source and build directories (y/n) [n]:

   The project name will occur in several places in the built documentation.
   > Project name: My Project
   > Author name(s): Fred Fredson
   > Project release []: 1.0

   If the documents are to be written in a language other than English,
   you can select a language here by its language code. Sphinx will then
   translate text that it generates into that language.

   For a list of supported codes, see
   https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-language.
   > Project language [en]:
   ```

4. In the generated Sphinx `conf.py` file, turn on `sphinx_js` by adding it
   to `extensions`:

   ```python
   extensions = ['sphinx_js']
   ```

5. If you want to document TypeScript, add:

   ```python
   js_language = 'typescript'
   ```

   to `conf.py` as well.

6. If your JS source code is anywhere but at the root of your project, add:

   ```python
   js_source_path = '../somewhere/else'
   ```

   on a line by itself in `conf.py`. The root of your JS source tree should be
   where that setting points, relative to the `conf.py` file.

   The default, `../`, works well when there is a `docs` folder at the root
   of your project and your source code lives directly inside the root.

7. If you have special JSDoc or TypeDoc configuration, add:

   ```python
   jsdoc_config_path = '../conf.json'
   ```

   to `conf.py` as well.

8. If you're documenting only JS or TS and no other languages (like C), you can
   set your "primary domain" to JS in `conf.py`:

   ```python
   primary_domain = 'js'
   ```

   The domain is `js` even if you're writing TypeScript. Then you can omit
   all the "js:" prefixes in the directives below.

## History

sphinx-js was created in 2017 by Erik Rose at Mozilla. It was transferred from
Mozilla to the Pyodide organization in 2025.

## Use

In short, in a Sphinx project, use the following directives to pull in your
JSDoc documentation, then tell Sphinx to render it all by running `make html`
in your docs directory. If you have never used Sphinx or written
reStructuredText before, here is [where we left off in its tutorial](https://www.sphinx-doc.org/en/stable/tutorial.html#defining-document-structure).
For a quick start, just add things to index.rst until you prove things are
working.

### autofunction

First, document your JS code using standard JSDoc formatting:

```javascript
/**
 * Return the ratio of the inline text length of the links in an element to
 * the inline text length of the entire element.
 *
 * @param {Node} node - Types or not: either works.
 * @throws {PartyError|Hearty} Multiple types work fine.
 * @returns {Number} Types and descriptions are both supported.
 */
function linkDensity(node) {
  const length = node.flavors.get("paragraphish").inlineLength;
  const lengthWithoutLinks = inlineTextLength(
    node.element,
    (element) => element.tagName !== "A",
  );
  return (length - lengthWithoutLinks) / length;
}
```

Then, reference your documentation using sphinx-js directives. Our directives
work much like Sphinx's standard autodoc ones. You can specify just a
function's name:

```rst
.. js:autofunction:: someFunction
```

and a nicely formatted block of documentation will show up in your docs.

You can also throw in your own explicit parameter list, if you want to note
optional parameters:

```rst
.. js:autofunction:: someFunction(foo, bar[, baz])
```

Parameter properties and destructuring parameters also work fine, using
[standard JSDoc syntax](https://jsdoc.app/tags-param.html#parameters-with-properties):

```javascript
/**
 * Export an image from the given canvas and save it to the disk.
 *
 * @param {Object} options Output options
 * @param {string} options.format The output format (``jpeg``,  ``png``, or
 *     ``webp``)
 * @param {number} options.quality The output quality when format is
 *     ``jpeg`` or ``webp`` (from ``0.00`` to ``1.00``)
 */
function saveCanvas({ format, quality }) {
  // ...
}
```

Extraction of default parameter values works as well. These act as expected,
with a few caveats:

```javascript
/**
 * You must declare the params, even if you have nothing else to say, so
 * JSDoc will extract the default values.
 *
 * @param [num]
 * @param [str]
 * @param [bool]
 * @param [nil]
 */
function defaultsDocumentedInCode(
  num = 5,
  str = "true",
  bool = true,
  nil = null,
) {}

/**
 * JSDoc guesses types for things like "42". If you have a string-typed
 * default value that looks like a number or boolean, you'll need to
 * specify its type explicitly. Conversely, if you have a more complex
 * value like an arrow function, specify a non-string type on it so it
 * isn't interpreted as a string. Finally, if you have a disjoint type like
 * {string|Array} specify string first if you want your default to be
 * interpreted as a string.
 *
 * @param {function} [func=() => 5]
 * @param [str=some string]
 * @param {string} [strNum=42]
 * @param {string|Array} [strBool=true]
 * @param [num=5]
 * @param [nil=null]
 */
function defaultsDocumentedInDoclet(func, strNum, strBool, num, nil) {}
```

You can even add additional content. If you do, it will appear just below any
extracted documentation:

```rst
.. js:autofunction:: someFunction

    Here are some things that will appear...

    * Below
    * The
    * Extracted
    * Docs

    Enjoy!
```

`js:autofunction` has one option, `:short-name:`, which comes in handy for
chained APIs whose implementation details you want to keep out of sight. When
you use it on a class method, the containing class won't be mentioned in the
docs, the function will appear under its short name in indices, and cross
references must use the short name as well (`:func:`someFunction``):

```rst
.. js:autofunction:: someClass#someFunction
   :short-name:
```

`autofunction` can also be used on callbacks defined with the [@callback tag](https://jsdoc.app/tags-callback.html).

There is experimental support for abusing `autofunction` to document
[@typedef tags](https://jsdoc.app/tags-typedef.html) as well, though the
result will be styled as a function, and `@property` tags will fall
misleadingly under an "Arguments" heading. Still, it's better than nothing
until we can do it properly.

If you are using typedoc, it also is possible to destructure keyword arguments
by using the `@destructure` tag:

```typescript
/**
* @param options
* @destructure options
*/
function f({x , y } : {
    /** The x value */
    x : number,
    /** The y value */
    y : string
}){ ... }
```

will be documented like:

```
options.x (number) The x value
options.y (number) The y value
```

### autoclass

We provide a `js:autoclass` directive which documents a class with the
concatenation of its class comment and its constructor comment. It shares all
the features of `js:autofunction` and even takes the same `:short-name:`
flag, which can come in handy for inner classes. The easiest way to use it is
to invoke its `:members:` option, which automatically documents all your
class's public methods and attributes:

```rst
.. js:autoclass:: SomeEs6Class(constructor, args, if, you[, wish])
   :members:
```

You can add private members by saying:

```rst
.. js:autoclass:: SomeEs6Class
   :members:
   :private-members:
```

Privacy is determined by JSDoc `@private` tags or TypeScript's `private`
keyword.

Exclude certain members by name with `:exclude-members:`:

```rst
.. js:autoclass:: SomeEs6Class
   :members:
   :exclude-members: Foo, bar, baz
```

Or explicitly list the members you want. We will respect your ordering.

```rst
.. js:autoclass:: SomeEs6Class
   :members: Qux, qum
```

When explicitly listing members, you can include `*` to include all
unmentioned members. This is useful to have control over ordering of some
elements, without having to include an exhaustive list.

```rst
.. js:autoclass:: SomeEs6Class
   :members: importMethod, *, uncommonlyUsedMethod
```

Finally, if you want full control, pull your class members in one at a time by
embedding `js:autofunction` or `js:autoattribute`:

```rst
.. js:autoclass:: SomeEs6Class

   .. js:autofunction:: SomeEs6Class#someMethod

   Additional content can go here and appears below the in-code comments,
   allowing you to intersperse long prose passages and examples that you
   don't want in your code.
```

### autoattribute

This is useful for documenting public properties:

```javascript
class Fnode {
  constructor(element) {
    /**
     * The raw DOM element this wrapper describes
     */
    this.element = element;
  }
}
```

And then, in the docs:

```rst
.. autoclass:: Fnode

   .. autoattribute:: Fnode#element
```

This is also the way to document ES6-style getters and setters, as it omits the
trailing `()` of a function. The assumed practice is the usual JSDoc one:
document only one of your getter/setter pair:

```javascript
class Bing {
  /** The bong of the bing */
  get bong() {
    return this._bong;
  }

  set bong(newBong) {
    this._bong = newBong * 2;
  }
}
```

And then, in the docs:

```rst
.. autoattribute:: Bing#bong
```

### automodule

This directive documents all exports on a module. For example:

```rst
.. js:automodule:: package.submodule
```

### autosummary

This directive should be paired with an automodule directive (which may occur in
a distinct rst file). It makes a summary table with links to the entries
generated by the automodule directive. Usage:

```rst
.. js:automodule:: package.submodule
```

## Dodging Ambiguity With Pathnames

If you have same-named objects in different files, use pathnames to
disambiguate them. Here's a particularly long example:

```rst
.. js:autofunction:: ./some/dir/some/file.SomeClass#someInstanceMethod.staticMethod~innerMember
```

You may recognize the separators `#.~` from [JSDoc namepaths](https://jsdoc.app/about-namepaths.html); they work the same here.

For conciseness, you can use any unique suffix, as long as it consists of
complete path segments. These would all be equivalent to the above, assuming
they are unique within your source tree:

```
innerMember
staticMethod~innerMember
SomeClass#someInstanceMethod.staticMethod~innerMember
some/file.SomeClass#someInstanceMethod.staticMethod~innerMember
```

Things to note:

- We use simple file paths rather than JSDoc's `module:` prefix or TypeDoc's
  `external:` or `module:` ones.
- We use simple backslash escaping exclusively rather than switching escaping
  schemes halfway through the path; JSDoc itself [is headed that way as well](https://github.com/jsdoc3/jsdoc/issues/876). The characters that need to
  be escaped are `#.~(/`, though you do not need to escape the dots in a
  leading `./` or `../`. A really horrible path might be:

  ```
  some/path\ with\ spaces/file.topLevelObject#instanceMember.staticMember\(with\(parens
  ```

- Relative paths are relative to the `js_source_path` specified in the
  config. Absolute paths are not allowed.

Behind the scenes, sphinx-js will change all separators to dots so that:

- Sphinx's "shortening" syntax works: ":func:\`~InwardRhs.atMost\`" prints as
merely`atMost()`. (For now, you should always use dots rather than other
namepath separators: `#~`.)
- Sphinx indexes more informatively, saying methods belong to their classes.

## Saving Keystrokes By Setting The Primary Domain

To save some keystrokes, you can set:

```python
primary_domain = 'js'
```

in `conf.py` and then use `autofunction` rather than `js:autofunction`.

## TypeScript: Getting Superclass and Interface Links To Work

To have a class link to its superclasses and implemented interfaces, you'll
need to document the superclass (or interface) somewhere using `js:autoclass`
or `js:class` and use the class's full (but dotted) path when you do:

```rst
.. js:autoclass:: someFile.SomeClass
```

Unfortunately, Sphinx's `~` syntax doesn't work in these spots, so users will
see the full paths in the documentation.

## TypeScript: Cross references

TypeScript types will be converted to cross references. To render cross
references, you can define a hook in `conf.py` called `ts_type_xref_formatter`. It
should take two arguments: the first argument is the sphinx confix, and the
second is an `sphinx_js.ir.TypeXRef` object. This has a `name` field and two
variants:

- a `sphinx_js.ir.TypeXRefInternal` with fields `path` and `kind`
- a `sphinx_js.ir.TypeXRefExternal` with fields `name`, `package`,
  `sourcefilename` and `qualifiedName`

The return value should be restructured text that you wish to be inserted in
place of the type. For example:

```python
def ts_xref_formatter(config, xref):
    if isinstance(xref, TypeXRefInternal):
        name = rst.escape(xref.name)
        return f":js:{xref.kind}:`{name}`"
    else:
        # Otherwise, don't insert a xref
        return xref.name
```

## Configuration Reference

### `js_language`

Use 'javascript' or 'typescript' depending on the language you use. The
default is 'javascript'.

### `js_source_path`

A list of directories to scan (non-recursively) for JS or TS source files,
relative to Sphinx's conf.py file. Can be a string instead if there is only
one. If there is more than one, `root_for_relative_js_paths` must be
specified as well. Defaults to `../`.

### `root_for_relative_js_paths`

Relative JS entity paths are resolved relative to this path. Defaults to
`js_source_path` if not present.

### `jsdoc_config_path`

A conf.py-relative path to a JSDoc config file, which is useful if you want to
specify your own JSDoc options, like recursion and custom filename matching.
If using TypeDoc, you can also point to a `typedoc.json` file.

### `jsdoc_tsconfig_path`

If using TypeDoc, specify the path of `tsconfig.json` file

### `ts_type_xref_formatter`

A function for formatting TypeScript type cross references. See the
"TypeScript: Cross references" section below.

### `ts_type_bold`

Make all TypeScript types bold if `true`.

### `ts_sphinx_js_config`

A link to a TypeScript config file.

## The `ts_sphinx_js_config` file

This file should be a TypeScript module. It's executed in a context where it can
import `typedoc` and `sphinx_js`. These functions take TypeDoc IR objects as
arguments. Since the TypeDoc IR is unstable, this config may often break when
switching TypeDoc versions. However, these hooks are very powerful so using them
may be worthwhile anyways. This API is experimental and may change in the
future.

For an example, you can see Pyodide's config file [here](shouldDestructureArg).

This file should export a config object with some of the three following
functions:

- `shouldDestructureArg: (param: ParameterReflection) => boolean`

This function takes a `ParameterReflection` and decides if it should be
destructured. If so, it's equivalent to putting a `@destructure` tag for the
argument. For example:

```typescript
function shouldDestructureArg(param: ParameterReflection) {
  return param.name === "options";
}
```

- `preConvert?: (app: Application) => Promise<void>;`

This hook is called with the TypeDoc application as argument before the
TypeScript files are parsed. For example, it can be used to add extra TypeDoc
plugins.

- `postConvert: (app: Application, project: ProjectReflection, typeDocToIRMap: Map<DeclarationReflection, TopLevelIR>) => void`

This hook is called after the sphinx_js IR is created. It can be used to
modify the IR arbitrarily. It is very experimental and subject to breaking
changes.

For example, this `postConvert` hook removes the constructor from classes marked with
`@hideconstructor`.

```typescript
function postConvert(app, project, typeDocToIRMap) {
  for (const [key, value] of typeDocToIRMap.entries()) {
    if (
      value.kind === "class" &&
      value.modifier_tags.includes("@hideconstructor")
    ) {
      value.constructor_ = null;
    }
  }
}
```

To use it, you'll also need to add a tag definition for `@hideconstructor` to your `tsdoc.json` file:

```json
{
  "tagDefinitions": [
    {
      "tagName": "@hideconstructor",
      "syntaxKind": "modifier"
    }
  ]
}
```

This `postConvert` hook hides external attributes and functions from the documentation:

```typescript
function postConvert(app, project, typeDocToIRMap) {
  for (const [key, value] of typeDocToIRMap.entries()) {
    if (value.kind === "attribute" || value.kind === "function") {
      value.is_private = key.flags.isExternal || key.flags.isPrivate;
    }
  }
}
```

## How sphinx-js finds typedoc / jsdoc

1. If the environment variable `SPHINX_JS_NODE_MODULES` is defined, it is
   expected to point to a `node_modules` folder in which typedoc / jsdoc is installed.

2. If `SPHINX_JS_NODE_MODULES` is not defined, we look in the directory of
   `conf.py` for a `node_modules` folder in which typedoc / jsdoc. If this is
   not found, we look for a `node_modules` folder in the parent directories
   until we make it to the root of the file system.

3. We check if `typedoc` / `jsdoc` are on the PATH, if so we use that.

4. If none of the previous approaches located `typedoc` / `jsdoc` we raise an error.

## Example

A good example using most of sphinx-js's functionality is the Fathom
documentation. A particularly juicy page is
<https://mozilla.github.io/fathom/ruleset.html>. Click the "View page
source" link to see the raw directives.

For a TypeScript example, see [the Pyodide api docs](https://pyodide.org/en/stable/usage/api/js-api.html).

[ReadTheDocs](https://readthedocs.org/) is the canonical hosting platform for
Sphinx docs and now supports sphinx-js. Put this in the
`.readthedocs.yml` file at the root of your repo:

```yaml
python:
  install:
    - requirements: docs/requirements.txt
```

Then put the version of sphinx-js you want in `docs/requirements.txt`. For
example:

```
sphinx-js==3.1.2
```

## Caveats

- We don't understand the inline JSDoc constructs like `{@link foo}`; you
  have to use Sphinx-style equivalents for now, like `:js:func:`foo`` (or
simply `:func:`foo`` if you have set `primary_domain = 'js'` in conf.py.
- So far, we understand and convert the JSDoc block tags `@param`,
  `@returns`, `@throws`, `@example` (without the optional `<caption>`),
  `@deprecated`, `@see`, and their synonyms. Other ones will go _poof_ into
  the ether.

## Tests

Run the tests using nox, which will also install JSDoc and TypeDoc at pinned
versions:

```bash
pip install nox
nox
```

## Provenance

sphinx-js was originally written and maintained by Erik Rose and various
contributors within and without the Mozilla Corporation and Foundation.
See `CONTRIBUTORS` for details.
