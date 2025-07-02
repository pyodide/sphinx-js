/**
 * A definition of a class
 */
export class ClassDefinition {
  field: string;

  /**
   * ClassDefinition constructor
   * @param simple A parameter with a simple type
   */
  constructor(simple: number) {}

  /**
   * This is a method without return type
   * @param simple A parameter with a simple type
   */
  method1(simple: number): void {}

  /**
   * This is a method (should be before method 'method1', but after fields)
   */
  anotherMethod() {}
}

export interface Interface {}

export abstract class ClassWithSupersAndInterfacesAndAbstract
  extends ClassDefinition
  implements Interface
{
  /** I construct. */
  constructor() {
    super(8);
  }
}

export interface InterfaceWithSupers extends Interface {}

export class ExportedClass {
  constructor() {}
}

export class ConstructorlessClass {}

export interface OptionalThings {
  foop?(): void;
  boop?: boolean;
}

/**
 * Words words words
 * @param a An optional thing
 * @returns The result
 */
export function blah(a: OptionalThings): ConstructorlessClass {
  return 0 as ConstructorlessClass;
}

export function thunk(b: typeof blah) {}

/**
 * A problematic self referential function
 * @param b troublemaker
 */
export function selfReferential(b: typeof selfReferential) {}

/**
 * @deprecated since v20!
 */
export function deprecatedFunction1() {}

/**
 * @deprecated
 */
export function deprecatedFunction2() {}

/**
 * @example This is an example.
 * @example This is another example.
 * ```py
 * Something python
 * ```
 */
export function exampleFunction() {}

export async function asyncFunction() {}

export class Iterable {
  *[Symbol.iterator](): Iterator<number, string, undefined> {
    yield 1;
    yield 2;
    yield 3;
    return "abc";
  }
}

export function predicate(c): c is ConstructorlessClass {
  return false;
}

/**
 * This shouldn't crash the renderer:
 * ```things```
 */
export function weirdCodeInDescription() {}

/**
 * `abc <http://example.com>`_
 */
export function spinxLinkInDescription() {}

export class GetSetDocs {
  readonly x: number;
  y: number;

  /**
   * Getter with comment
   */
  get a() {
    return 7;
  }

  /**
   * Setter with comment
   */
  set b(x: number) {}
}

export class Base {
  /** Some docs for f */
  f() {}

  get a() {
    return 7;
  }
}

export class Extension extends Base {
  /** Some docs for g */
  g() {}
}
