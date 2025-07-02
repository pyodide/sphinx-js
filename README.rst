=========
sphinx-js
=========

Why
===

When you write a JavaScript library, how do you explain it to people? If it's a
small project in a domain your users are familiar with, JSDoc's alphabetical
list of routines might suffice. But in a larger project, it is useful to
intersperse prose with your API docs without having to copy and paste things.

sphinx-js lets you use the industry-leading `Sphinx <https://sphinx-doc.org/>`__
documentation tool with JS projects. It provides a handful of directives,
patterned after the Python-centric `autodoc
<https://www.sphinx-doc.org/en/latest/ext/autodoc.html>`__ ones, for pulling
JSDoc-formatted documentation into reStructuredText pages. And, because you can
keep using JSDoc in your code, you remain compatible with the rest of your JS
tooling, like Google's Closure Compiler.

sphinx-js also works with TypeScript, using the TypeDoc tool in place of JSDoc
and emitting all the type information you would expect.

Setup
=====

1. Install JSDoc (or TypeDoc if you're writing TypeScript).

        npm install jsdoc

   or::

        npm install typedoc@0.28

  JSDoc 3.6.3 and 4.0.0 and TypeDoc 0.25--0.28 are known to work.


2. Install sphinx-js, which will pull in Sphinx itself as a dependency::

       pip install sphinx-js

3. Make a documentation folder in your project by running ``sphinx-quickstart``
   and answering its questions::

       cd my-project
       sphinx-quickstart

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

4. In the generated Sphinx ``conf.py`` file, turn on ``sphinx_js`` by adding it
   to ``extensions``::

       extensions = ['sphinx_js']

5. If you want to document TypeScript, add::

       js_language = 'typescript'

   to ``conf.py`` as well.

6. If your JS source code is anywhere but at the root of your project, add::

       js_source_path = '../somewhere/else'

   on a line by itself in ``conf.py``. The root of your JS source tree should be
   where that setting points, relative to the ``conf.py`` file.

   The default, ``../``, works well when there is a ``docs`` folder at the root
   of your project and your source code lives directly inside the root.

7. If you have special JSDoc or TypeDoc configuration, add::

       jsdoc_config_path = '../conf.json'

   to ``conf.py`` as well.

8. If you're documenting only JS or TS and no other languages (like C), you can
   set your "primary domain" to JS in ``conf.py``::

       primary_domain = 'js'

   The domain is ``js`` even if you're writing TypeScript. Then you can omit
   all the "js:" prefixes in the directives below.

Use
===

In short, in a Sphinx project, use the following directives to pull in your
JSDoc documentation, then tell Sphinx to render it all by running ``make html``
in your docs directory. If you have never used Sphinx or written
reStructuredText before, here is `where we left off in its tutorial
<https://www.sphinx-doc.org/en/stable/tutorial.html#defining-document-structure>`__.
For a quick start, just add things to index.rst until you prove things are
working.

autofunction
------------

First, document your JS code using standard JSDoc formatting::

    /**
     * Return the ratio of the inline text length of the links in an element to
     * the inline text length of the entire element.
     *
     * @param {Node} node - Types or not: either works.
     * @throws {PartyError|Hearty} Multiple types work fine.
     * @returns {Number} Types and descriptions are both supported.
     */
    function linkDensity(node) {
        const length = node.flavors.get('paragraphish').inlineLength;
        const lengthWithoutLinks = inlineTextLength(node.element,
                                                    element => element.tagName !== 'A');
        return (length - lengthWithoutLinks) / length;
    }

Then, reference your documentation using sphinx-js directives. Our directives
work much like Sphinx's standard autodoc ones. You can specify just a
function's name::

    .. js:autofunction:: someFunction

and a nicely formatted block of documentation will show up in your docs.

You can also throw in your own explicit parameter list, if you want to note
optional parameters::

    .. js:autofunction:: someFunction(foo, bar[, baz])

Parameter properties and destructuring parameters also work fine, using
`standard JSDoc syntax
<https://jsdoc.app/tags-param.html#parameters-with-properties>`__::

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

Extraction of default parameter values works as well. These act as expected,
with a few caveats::

    /**
     * You must declare the params, even if you have nothing else to say, so
     * JSDoc will extract the default values.
     *
     * @param [num]
     * @param [str]
     * @param [bool]
     * @param [nil]
     */
    function defaultsDocumentedInCode(num=5, str="true", bool=true, nil=null) {}

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

You can even add additional content. If you do, it will appear just below any
extracted documentation::

    .. js:autofunction:: someFunction

        Here are some things that will appear...

        * Below
        * The
        * Extracted
        * Docs

        Enjoy!

``js:autofunction`` has one option, ``:short-name:``, which comes in handy for
chained APIs whose implementation details you want to keep out of sight. When
you use it on a class method, the containing class won't be mentioned in the
docs, the function will appear under its short name in indices, and cross
references must use the short name as well (``:func:`someFunction```)::

    .. js:autofunction:: someClass#someFunction
       :short-name:

``autofunction`` can also be used on callbacks defined with the `@callback tag
<https://jsdoc.app/tags-callback.html>`__.

There is experimental support for abusing ``autofunction`` to document
`@typedef tags <https://jsdoc.app/tags-typedef.html>`__ as well, though the
result will be styled as a function, and ``@property`` tags will fall
misleadingly under an "Arguments" heading. Still, it's better than nothing
until we can do it properly.

If you are using typedoc, it also is possible to destructure keyword arguments
by using the `@destructure` tag::

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

will be documented like::

    options.x (number) The x value
    options.y (number) The y value

autoclass
---------

We provide a ``js:autoclass`` directive which documents a class with the
concatenation of its class comment and its constructor comment. It shares all
the features of ``js:autofunction`` and even takes the same ``:short-name:``
flag, which can come in handy for inner classes. The easiest way to use it is
to invoke its ``:members:`` option, which automatically documents all your
class's public methods and attributes::

    .. js:autoclass:: SomeEs6Class(constructor, args, if, you[, wish])
       :members:

You can add private members by saying::

    .. js:autoclass:: SomeEs6Class
       :members:
       :private-members:

Privacy is determined by JSDoc ``@private`` tags or TypeScript's ``private``
keyword.

Exclude certain members by name with ``:exclude-members:``::

    .. js:autoclass:: SomeEs6Class
       :members:
       :exclude-members: Foo, bar, baz

Or explicitly list the members you want. We will respect your ordering. ::

    .. js:autoclass:: SomeEs6Class
       :members: Qux, qum

When explicitly listing members, you can include ``*`` to include all
unmentioned members. This is useful to have control over ordering of some
elements, without having to include an exhaustive list. ::

    .. js:autoclass:: SomeEs6Class
       :members: importMethod, *, uncommonlyUsedMethod

Finally, if you want full control, pull your class members in one at a time by
embedding ``js:autofunction`` or ``js:autoattribute``::

    .. js:autoclass:: SomeEs6Class

       .. js:autofunction:: SomeEs6Class#someMethod

       Additional content can go here and appears below the in-code comments,
       allowing you to intersperse long prose passages and examples that you
       don't want in your code.

autoattribute
-------------

This is useful for documenting public properties::

    class Fnode {
        constructor(element) {
            /**
             * The raw DOM element this wrapper describes
             */
            this.element = element;
        }
    }

And then, in the docs::

    .. autoclass:: Fnode

       .. autoattribute:: Fnode#element

This is also the way to document ES6-style getters and setters, as it omits the
trailing ``()`` of a function. The assumed practice is the usual JSDoc one:
document only one of your getter/setter pair::

    class Bing {
        /** The bong of the bing */
        get bong() {
            return this._bong;
        }

        set bong(newBong) {
            this._bong = newBong * 2;
        }
    }

And then, in the docs::

   .. autoattribute:: Bing#bong

automodule
----------

This directive documents all exports on a module. For example::

  .. js:automodule:: package.submodule

autosummary
-----------

This directive should be paired with an automodule directive (which may occur in
a distinct rst file). It makes a summary table with links to the entries
generated by the automodule directive. Usage::

  .. js:automodule:: package.submodule

Dodging Ambiguity With Pathnames
--------------------------------

If you have same-named objects in different files, use pathnames to
disambiguate them. Here's a particularly long example::

    .. js:autofunction:: ./some/dir/some/file.SomeClass#someInstanceMethod.staticMethod~innerMember

You may recognize the separators ``#.~`` from `JSDoc namepaths
<https://jsdoc.app/about-namepaths.html>`__; they work the same here.

For conciseness, you can use any unique suffix, as long as it consists of
complete path segments. These would all be equivalent to the above, assuming
they are unique within your source tree::

    innerMember
    staticMethod~innerMember
    SomeClass#someInstanceMethod.staticMethod~innerMember
    some/file.SomeClass#someInstanceMethod.staticMethod~innerMember

Things to note:

* We use simple file paths rather than JSDoc's ``module:`` prefix or TypeDoc's
  ``external:`` or ``module:`` ones.
* We use simple backslash escaping exclusively rather than switching escaping
  schemes halfway through the path; JSDoc itself `is headed that way as well
  <https://github.com/jsdoc3/jsdoc/issues/876>`__. The characters that need to
  be escaped are ``#.~(/``, though you do not need to escape the dots in a
  leading ``./`` or ``../``. A really horrible path might be::

      some/path\ with\ spaces/file.topLevelObject#instanceMember.staticMember\(with\(parens

* Relative paths are relative to the ``js_source_path`` specified in the
  config. Absolute paths are not allowed.

Behind the scenes, sphinx-js will change all separators to dots so that:

* Sphinx's "shortening" syntax works: ``:func:`~InwardRhs.atMost``` prints as
  merely ``atMost()``. (For now, you should always use dots rather than other
  namepath separators: ``#~``.)
* Sphinx indexes more informatively, saying methods belong to their classes.

Saving Keystrokes By Setting The Primary Domain
-----------------------------------------------

To save some keystrokes, you can set::

    primary_domain = 'js'

in ``conf.py`` and then use ``autofunction`` rather than ``js:autofunction``.

TypeScript: Getting Superclass and Interface Links To Work
----------------------------------------------------------

To have a class link to its superclasses and implemented interfaces, you'll
need to document the superclass (or interface) somewhere using ``js:autoclass``
or ``js:class`` and use the class's full (but dotted) path when you do::

    .. js:autoclass:: someFile.SomeClass

Unfortunately, Sphinx's ``~`` syntax doesn't work in these spots, so users will
see the full paths in the documentation.

Typescript: Cross references
----------------------------

Typescript types will be converted to cross references. To render cross
references, you can define a hook in ``conf.py`` called `ts_type_xref_formatter`. It
should take two arguments: the first argument is the sphinx confix, and the
second is an ``sphinx_js.ir.TypeXRef`` object. This has a ``name`` field and two
variants:

* a ``sphinx_js.ir.TypeXRefInternal`` with fields ``path`` and ``kind``
* a ``sphinx_js.ir.TypeXRefExternal`` with fields ``name``, ``package``,
``sourcefilename`` and ``qualifiedName``

The return value should be restructured text that you wish to be inserted in
place of the type. For example:

.. code-block:: python

    def ts_xref_formatter(config, xref):
        if isinstance(xref, TypeXRefInternal):
            name = rst.escape(xref.name)
            return f":js:{xref.kind}:`{name}`"
        else:
            # Otherwise, don't insert a xref 
            return xref.name


Configuration Reference
-----------------------

``js_language``
  Use 'javascript' or 'typescript' depending on the language you use. The
  default is 'javascript'.

``js_source_path``
  A list of directories to scan (non-recursively) for JS or TS source files,
  relative to Sphinx's conf.py file. Can be a string instead if there is only
  one. If there is more than one, ``root_for_relative_js_paths`` must be
  specified as well. Defaults to ``../``.

``root_for_relative_js_paths``
  Relative JS entity paths are resolved relative to this path. Defaults to
  ``js_source_path`` if not present.

``jsdoc_config_path``
  A conf.py-relative path to a JSDoc config file, which is useful if you want to
  specify your own JSDoc options, like recursion and custom filename matching.
  If using TypeDoc, you can also point to a ``typedoc.json`` file.

``jsdoc_tsconfig_path``
  If using TypeDoc, specify the path of ``tsconfig.json`` file

``ts_type_xref_formatter``
  A function for formatting typescript type cross referenes. See the
  "Typescript: Cross references" section below.

``ts_type_bold``
  Make all typescript types bold if `true`.

``ts_sphinx_js_config``
  A link to a typescript config file.

The `ts_sphinx_js_config` file
------------------------------

This file should be a typescript module. It's executed in a context where it can
import `typedoc` and `sphinx_js`. These functions take TypeDoc IR objects as
arguments. Since the TypeDoc IR is unstable, this config may often break when
switching TypeDoc versions. However, these hooks are very powerful so using them
may be worthwhile anyways. This API is experimental and may change in the
future.

For an example, you can see Pyodide's config file `here <shouldDestructureArg>`__.

This file should export a config object with some of the three following
functions::

* ``shouldDestructureArg: (param: ParameterReflection) => boolean``

  This function takes a ``ParameterReflection`` and decides if it should be
  destructured. If so, it's equivalent to putting a `@destructure` tag for the
  argument. For example:

  .. code_block:: ts

    function shouldDestructureArg(param: ParameterReflection) {
      return param.name === "options";
    }

* ``preConvert?: (app: Application) => Promise<void>;``

  This hook is called with the TypeDoc application as argument before the
  typescript files are parsed. For example, it can be used to add extra TypeDoc
  plugins.

* ``postConvert: (app: Application, project: ProjectReflection, typeDocToIRMap: Map<DeclarationReflection, TopLevelIR>) => void``

  This hook is called after the sphinx_js IR is created. It can be used to
  modify the IR arbitrarily. It is very experimental and subject to breaking
  changes.

  For example, this ``postConvert`` hook removes the constructor from classes marked with
  `@hideconstructor`.

  .. code_block:: ts

    function postConvert(app, project, typeDocToIRMap) {
      for (const [key, value] of typeDocToIRMap.entries()) {
        if (value.kind === "class" && value.modifier_tags.includes("@hideconstructor")) {
          value.constructor_ = null;
        }
      }
    }

  To use it, you'll also need to add a tag defintion for `@hideconstructor` to your `tsdoc.json` file:

  .. code_block:: json

    "tagDefinitions": [
      {
        "tagName": "@hideconstructor",
        "syntaxKind": "modifier"
      }
    ]

  This ``postConvert`` hook hides external attributes and functions from the documentation:

  .. code_block:: ts

    function postConvert(app, project, typeDocToIRMap) {
      for (const [key, value] of typeDocToIRMap.entries()) {
        if (value.kind === "attribute" || value.kind === "function") {
          value.is_private = key.flags.isExternal || key.flags.isPrivate;
        }
      }
    }


How sphinx-js finds typedoc / jsdoc
-----------------------------------

1. If the environment variable ``SPHINX_JS_NODE_MODULES`` is defined, it is
   expected to point to a ``node_modules`` folder in which typedoc / jsdoc is installed.

2. If ``SPHINX_JS_NODE_MODULES`` is not defined, we look in the directory of
   ``conf.py`` for a ``node_modules`` folder in which typedoc / jsdoc. If this is
   not found, we look for a ``node_modules`` folder in the parent directories
   until we make it to the root of the file system.

3. We check if ``typedoc`` / ``jsdoc`` are on the PATH, if so we use that.

4. If none of the previous approaches located ``typedoc`` / ``jsdoc`` we raise an error.

Example
=======

A good example using most of sphinx-js's functionality is the Fathom
documentation. A particularly juicy page is
`<https://mozilla.github.io/fathom/ruleset.html>`__. Click the "View page
source" link to see the raw directives.

For a typescript example, see `the Pyodide api docs
<https://pyodide.org/en/stable/usage/api/js-api.html>`__.

`ReadTheDocs <https://readthedocs.org/>`__ is the canonical hosting platform for
Sphinx docs and now supports sphinx-js. Put this in the
``.readthedocs.yml`` file at the root of your repo:

.. code_block:: yaml

    python:
      install:
        - requirements: docs/requirements.txt

Then put the version of sphinx-js you want in ``docs/requirements.txt``. For
example::

    sphinx-js==3.1.2

Caveats
=======

* We don't understand the inline JSDoc constructs like ``{@link foo}``; you
  have to use Sphinx-style equivalents for now, like ``:js:func:`foo``` (or
  simply ``:func:`foo``` if you have set ``primary_domain = 'js'`` in conf.py.
* So far, we understand and convert the JSDoc block tags ``@param``,
  ``@returns``, ``@throws``, ``@example`` (without the optional ``<caption>``),
  ``@deprecated``, ``@see``, and their synonyms. Other ones will go *poof* into
  the ether.

Tests
=====

Run the tests using nox, which will also install JSDoc and TypeDoc at pinned
versions::

    pip install nox
    nox

Provenance
==========

sphinx-js was originally written and maintained by Erik Rose and various
contributors within and without the Mozilla Corporation and Foundation.
See ``CONTRIBUTORS`` for details.

Version History
===============

5.0.0: (Unreleased)
  * Droped support for Python 3.9 (pyodide/sphinx-js-fork#7)
  * Dropped support for typedoc 0.15, added support for typedoc 0.25, 0.26, and
    0.27 (pyodide/sphinx-js-fork#11, pyodide/sphinx-js-fork#22,
    pyodide/sphinx-js-fork#31, pyodide/sphinx-js-fork#39,
    pyodide/sphinx-js-fork#41, pyodide/sphinx-js-fork#43
    pyodide/sphinx-js-fork#52, pyodide/sphinx-js-fork#53,
    pyodide/sphinx-js-fork#54, pyodide/sphinx-js-fork#174)
  * Added handling for Typescript type parameters and type bounds.
    (pyodide/sphinx-js-fork#25)
  * Only monkeypatch Sphinx classes when sphinx_js extension is used
    (pyodide/sphinx-js-fork#27)
  * Allow using installation of ``typedoc`` or ``jsdoc`` from `node_modules`
    instead of requiring global install. (pyodide/sphinx-js-fork#33)
  * Handle markdown style codepens correctly in typedoc comments.
    (pyodide/sphinx-js-fork#47)
  * Added support for destructuring the documentation of keyword arguments in
    Typescript using the ``@destructure`` tag or the
    ``shouldDestructureArg`` hook.
    (pyodide/sphinx-js-fork#48, pyodide/sphinx-js-fork#74,
     pyodide/sphinx-js-fork#75, pyodide/sphinx-js-fork#101,
     pyodide/sphinx-js-fork#128)
  * Added rendering for cross references in Typescript types.
    (pyodide/sphinx-js-fork#51, pyodide/sphinx-js-fork#56,
     pyodide/sphinx-js-fork#67, pyodide/sphinx-js-fork#81,
     pyodide/sphinx-js-fork#82, pyodide/sphinx-js-fork#83,
     pyodide/sphinx-js-fork#153, pyodide/sphinx-js-fork#160)
  * Added rendering for function types in Typescript documentation.
    (pyodide/sphinx-js-fork#55, pyodide/sphinx-js-fork#58,
    pyodide/sphinx-js-fork#59)
  * Add async prefix to async functions (pyodide/sphinx-js-fork#65).
  * Added the ``sphinx-js_type`` css class around all types in documentation. This
    allows applying custom css just to types (pyodide/sphinx-js-fork#85)
  * Added ``ts_type_bold`` config option that applies css to ``.sphinx-js_type``
    to render all types as bold.
  * Added ``js:automodule`` directive (pyodide/sphinx-js-fork#108)
  * Added ``js:autosummary`` directive (pyodide/sphinx-js-fork#109)
  * Added rendering for ``queryType`` (e.g.,  ``let y: typeof x;``)
    (pyodide/sphinx-js-fork#124)
  * Added rendering for ``typeOperator`` (e.g., ``let y: keyof x``)
    (pyodide/sphinx-js-fork#125)
  * Fixed crash when objects are reexported. (pyodide/sphinx-js-fork#126)
  * Added ``jsdoc_tsconfig_path`` which can specify the path to the
    ``tsconfig.json`` file that should be used. (pyodide/sphinx-js-fork#116)
  * Added a `js:interface` directive (pyodide/sphinx-js-fork#138).
  * Removed parentheses from xrefs to classes (pyodide/sphinx-js-fork#155).
  * Added a ``:js:typealias:`` directive (pyodide/sphinx-js-fork#156).
  * Added rendering for conditional, indexed access, inferred, mapped, optional,
    rest, and template litreal types (pyodide/sphinx-js-fork#157).
  * Added readonly prefix to readonly properties (pyodide/sphinx-js-fork#158).

4.0.0: (December 23rd, 2024)
  * Drop support for Python 3.8.
  * Add support for Python 3.12 and 3.13.
  * Add support for Sphinx 8.x.x.
  * Get CI working again.
  * Drop pin for MarkupSafe. (#244)
  * Add dependabot checking for GitHub actions. (Christian Clauss)
  * Fix wheel contents to not include tests. (#241)

  Thank you to Will Kahn-Greene and Christian Clauss!

3.2.2: (September 20th, 2023)
  * Remove Sphinx upper-bound requirement. (#227)
  * Drop support for Python 3.7. (#228)

  Thank you to Will Kahn-Greene!

3.2.1: (December 16th, 2022)
  * Fix xrefs to static functions. (#178)
  * Add support for jsdoc 4.0.0. (#215)

  Thank you to xsjad0 and Will Kahn-Greene!

3.2.0: (December 13th, 2022)
  * Add "static" in front of static methods.
  * Pin Jinja2 and markupsafe versions. (#190)
  * Track dependencies; do not read all documents. This improves speed of
    incremental updates. (#194)
  * Support Python 3.10 and 3.11. (#186)
  * Support Sphinx >= 4.1.0. (#209)
  * Fix types warning for ``js_source_path`` configuration item. (#182)

  Thank you Stefan 'hr' Berder, David Huggins-Daines, Nick Alexander,
  mariusschenzle, Erik Rose, lonnen, and Will Kahn-Greene!

3.1.2: (April 15th, 2021)
  * Remove our declared dependency on ``docutils`` to work around the way pip's
    greedy dependency resolver reacts to the latest version of Sphinx. pip
    fails when pip-installing sphinx-js because pip sees our "any version of
    docutils" declaration first (which resolves greedily to the latest version,
    0.17) but later encounters Sphinx's apparently new ``<0.17`` constraint and
    gives up. We can revert this when pip's ``--use-feature=2020-resolver``
    becomes the default.

3.1.1: (March 23rd, 2021)
  * Rewrite large parts of the suffix tree that powers path lookup. This fixes
    several crasher.

3.1: (September 10th, 2020)
  * Re-architect language analysis. There is now a well-documented intermediate
    representation between JSDoc- and TypeDoc-emitted JSON and the renderers.
    This should make it much faster to merge PRs.
  * Rewrite much of the TypeScript analysis engine so it feeds into the new IR.

    * TypeScript analysis used to crash if your codebase contained any
      overloaded functions. This no longer happens; we now arbitrarily use only
      the first function signature of each overloaded function.
    * Add support for static properties on TS classes.
    * Support variadic args in TS.
    * Support intersection types (``foo & bar``) in TS.
    * Remove the "exported from" module links from classes and interfaces.
      Functions never had them. Let's see if we miss them.
    * Pathnames for TypeScript objects no longer spuriously use ``~`` after the
      filename path segment; now they use ``.`` as in JS.
    * More generally, TS pathnames are now just like JS ones. There is no more
      ``external:`` prefix in front of filenames or ``module:`` in front of
      namespace names.
    * TS analyzer no longer cares with the current working directory is.
    * Tests now assert only what they care about rather than being brittle to
      the point of prohibiting any change.
  * No longer show args in the arg list that are utterly uninformative, lacking
    both description and type info.
  * Class attributes are now listed before methods unless manally ordered with
    ``:members:``.

3.0.1: (August 10th, 2020)
  * Don't crash when encountering a ``../`` prefix on an object path. This can
    happen behind the scenes when ``root_for_relative_js_paths`` is set inward
    of the JS code.

3.0: (July 14th, 2020)
  * Make compatible with Sphinx 3, which requires Python 3.
  * Drop support for Python 2.
  * Make sphinx-js not care what the current working directory is, except for
    the TypeScript analyzer, which needs further work.
  * Properly RST-escape return types.

2.8: (September 16th, 2019)
  * Display generic TypeScript types properly. Make fields come before methods.
    (Paul Grau)
  * Combine constructor and class documentation at the top TypeScript classes.
    (Sebastian Weigand)
  * Switch to pytest as the testrunner. (Sebastian Weigand)
  * Add optional caching of JSDoc output, for large codebases. (Patrick Browne)
  * Fix the display of union types in TypeScript. (Sebastian Weigand)
  * Fix parsing breakage that began in typedoc 0.14.0. (Paul Grau)
  * Fix a data-intake crash with TypeScript. (Cristiano Santos)

2.7.1: (November 16th, 2018)
  * Fix a crash that would happen sometimes with UTF-8 on Windows. #67.
  * Always use conf.py's dir for JSDoc's working dir. #78. (Thomas Khyn)

2.7: (August 2nd, 2018))
  * Add experimental TypeScript support. (Wim Yedema)

2.6: (July 26th, 2018)
  * Add support for ``@deprecated`` and ``@see``. (David Li)
  * Notice and document JS variadic params nicely. (David Li)
  * Add linter to codebase.

2.5: (April 20th, 2018)
  * Use documented ``@params`` to help fill out the formal param list for a
    function. This keeps us from missing params that use destructuring. (flozz)
  * Improve error reporting when JSDoc is missing.
  * Add extracted default values to generated formal param lists. (flozz and
    erikrose)

2.4: (March 21, 2018)
  * Support the ``@example`` tag. (lidavidm)
  * Work under Windows. Before, we could hardly find any documentation. (flozz)
  * Properly unwrap multiple-line JSDoc tags, even if they have Windows line
    endings. (Wim Yedema)
  * Drop support for Python 3.3, since Sphinx has also done so.
  * Fix build-time crash when using recommonmark (for Markdown support) under
    Sphinx >=1.7.1. (jamrizzi)

2.3.1: (January 11th, 2018)
  * Find the ``jsdoc`` command on Windows, where it has a different name. Then
    patch up process communication so it doesn't hang.

2.3: (November 1st, 2017)
  * Add the ability to say "*" within the ``autoclass :members:`` option,
    meaning "and all the members that I didn't explicitly list".

2.2: (October 10th, 2017)
  * Add ``autofunction`` support for ``@callback`` tags. (krassowski)
  * Add experimental ``autofunction`` support for ``@typedef`` tags. (krassowski)
  * Add a nice error message for when JSDoc can't find any JS files.
  * Pin six more tightly so ``python_2_unicode_compatible`` is sure to be around.

2.1: (August 30th, 2017)
  * Allow multiple folders in ``js_source_path``. This is useful for gradually
    migrating large projects, one folder at a time, to JSDoc. Introduce
    ``root_for_relative_js_paths`` to keep relative paths unambiguous in the
    face of multiple source paths.
  * Aggregate PathTaken errors, and report them all at once. This means you
    don't have to run JSDoc repeatedly while cleaning up large projects.
  * Fix a bytes-vs-strings issue that crashed on versions of Python 3 before
    3.6. (jhkennedy)
  * Tolerate JS files that have filename extensions other than ".js". Before,
    when combined with custom JSDoc configuration that ingested such files,
    incorrect object pathnames were generated, which led to spurious "No JSDoc
    documentation was found for object ..." errors.

2.0.1: (July 13th, 2017)
  * Fix spurious syntax errors while loading large JSDoc output by writing it
    to a temp file first. (jhkennedy)

2.0: (May 4th, 2017)
  * Deal with ambiguous object paths. Symbols with identical JSDoc longnames
    (such as two top-level things called "foo" in different files) will no
    longer have one shadow the other. Introduce an unambiguous path convention
    for referring to objects. Add a real parser to parse them rather than the
    dirty tricks we were using before. Backward compatibility breaks a little,
    because ambiguous references are now a fatal error, rather than quietly
    referring to the last definition JSDoc happened to encounter.
  * Index everything into a suffix tree so you can use any unique path suffix
    to refer to an object.
  * Other fallout of having a real parser:

    * Stop supporting "-" as a namepath separator.
    * No longer spuriously translate escaped separators in namepaths into dots.
    * Otherwise treat paths and escapes properly. For example, we can now
      handle symbols that contain "(".
  * Fix KeyError when trying to gather the constructor params of a plain old
    object labeled as a ``@class``.

1.5.2: (March 22th, 2017)
  * Fix crash while warning that a specified longname isn't found.

1.5.1: (March 20th, 2017)
  * Sort ``:members:`` alphabetically when an order is not explicitly specified.

1.5: (March 17th, 2017)
  * Add ``:members:`` option to ``autoclass``.
  * Add ``:private-members:`` and ``:exclude-members:`` options to go with it.
  * Significantly refactor to allow directive classes to talk to each other.

1.4: (March 10th, 2017)
  * Add ``jsdoc_config_path`` option.

1.3.1: (March 6th, 2017)
  * Tolerate @args and other info field lines that are wrapped in the source
    code.
  * Cite the file and line of the source comment in Sphinx-emitted warnings and
    errors.

1.3: (February 21st, 2017)
  * Add ``autoattribute`` directive.

1.2: (February 14th, 2017)
  * Always do full rebuilds; don't leave pages stale when JS code has changed
    but the RSTs have not.
  * Make Python-3-compatible.
  * Add basic ``autoclass`` directive.

1.1: (February 13th, 2017)
  * Add ``:short-name:`` option.

1.0: (February 7th, 2017)
  * Initial release, with just ``js:autofunction``
