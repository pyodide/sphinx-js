/**
 * Return the ratio of the inline text length of the links in an element to
 * the inline text length of the entire element.
 *
 * @param {Node} node - Something of a single type
 * @throws {PartyError|FartyError} Something with multiple types and a line
 *    that wraps
 * @returns {Number} What a thing
 */
function linkDensity(node) {
  const length = node.flavors.get("paragraphish").inlineLength;
  const lengthWithoutLinks = inlineTextLength(
    node.element,
    (element) => element.tagName !== "A",
  );
  return (length - lengthWithoutLinks) / length;
}

/**
 * Class doc.
 */
class ContainingClass {
  /**
   * Constructor doc.
   *
   * @arg ho A thing
   */
  constructor(ho) {
    /**
     * A var
     */
    this.someVar = 4;
  }

  /**
   * Here.
   * @protected
   */
  someMethod(hi) {}

  /**
   * Setting this also frobs the frobnicator.
   */
  get bar() {
    return this._bar;
  }
  set bar(baz) {
    this._bar = _bar;
  }

  /**
   * Another.
   */
  anotherMethod() {}

  /**
   * More.
   */
  yetAnotherMethod() {}

  /**
   * Private thing.
   * @private
   */
  secret() {}
}

// We won't add any new members to this class, because it would break some tests.
/** Closed class. */
class ClosedClass {
  /**
   * Public thing.
   */
  publical() {}

  /**
   * Public thing 2.
   */
  publical2() {}

  /**
   * Public thing 3.
   */
  publical3() {}
}

/** Non-alphabetical class. */
class NonAlphabetical {
  /** Fun z. */
  z() {}

  /** Fun a. */
  a() {}
}

/**
 * This doesn't emit a paramnames key in meta.code.
 * @class
 */
const NoParamnames = {};

/** Thing to be shadowed in more_code.js */
function shadow() {}

/**
 * @typedef {Object} TypeDefinition
 * @property {Number} width - width in pixels
 */

/**
 * Some global callback
 * @callback requestCallback
 * @param {number} responseCode
 */

/**
 * JSDoc example tag
 *
 * @example
 * // This is the example.
 * exampleTag();
 */
function exampleTag() {}

/**
 * JSDoc example tag for class
 *
 * @example
 * // This is the example.
 * new ExampleClass();
 */
class ExampleClass {}

/**
 * JSDoc example tag for attribute
 *
 * @example
 * // This is the example.
 * console.log(ExampleAttribute);
 */
const ExampleAttribute = null;

/**
 * @param {number} p1
 * @param {Object} p2
 * @param {string} p2.foo
 * @param {string} p2.bar
 */
function destructuredParams(p1, { foo, bar }) {}

/**
 * @param a_ Snorf
 * @param {type_} b Borf_
 * @returns {rtype_} Dorf_
 */
function injection() {}

/**
 * @param {function} [func=() => 5]
 * @param [str=a string with " quote]
 * @param {string} [strNum=42]
 * @param {string} [strBool=true]
 * @param [num=5]
 * @param [nil=null]
 */
function defaultsDocumentedInDoclet(func, str, strNum, strBool, num, nil) {}

/**
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
 * Variadic parameter
 * @param a
 * @param args
 */
function variadicParameter(a, ...args) {}

/** @deprecated */
function deprecatedFunction() {}
/** @deprecated don't use anymore */
function deprecatedExplanatoryFunction() {}

/** @deprecated */
const DeprecatedAttribute = null;
/** @deprecated don't use anymore */
const DeprecatedExplanatoryAttribute = null;

/** @deprecated */
class DeprecatedClass {}
/** @deprecated don't use anymore */
class DeprecatedExplanatoryClass {}

/**
 * @see DeprecatedClass
 * @see deprecatedFunction
 * @see DeprecatedAttribute
 */
function seeFunction() {}
/**
 * @see DeprecatedClass
 * @see deprecatedFunction
 * @see DeprecatedAttribute
 */
const SeeAttribute = null;
/**
 * @see DeprecatedClass
 * @see deprecatedFunction
 * @see DeprecatedAttribute
 */
class SeeClass {}

/**
 * @arg fnodeA {Node|Fnode}
 */
function union(fnodeA) {}

/**
 * Once upon a time, there was a large bear named Sid. Sid wore green pants
 * with blue stripes and pink polka dots.
 *
 * * List!
 *
 * @param a A is the first letter of the Roman alphabet. It is used in such
 *     illustrious words as aardvark and artichoke.
 * @param b Next param, which should be part of the same field list
 */
function longDescriptions(a, b) {}

/**
 * Class doc.
 */
class SimpleClass {
  /**
   * Static.
   *
   * @see nonStaticMethod
   */
  static staticMethod() {}

  /**
   * Non-static member.
   *
   * @see staticMethod
   */
  nonStaticMethod() {}
}
