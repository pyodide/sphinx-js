/**
 * Function
 */
export function foo(): void {
  /**
   * An inner function
   */
  function inner(): void {}
}
foo.adHocInner = "innerValue";

/**
 * Foo class
 */
export class Foo {
  /**
   * Static member
   */
  static staticMember = 8;

  /**
   * Num instance var
   */
  numInstanceVar: number;

  /**
   * Weird var
   */
  "weird#Var": number;

  /**
   * Constructor
   */
  constructor(num: number) {
    this.numInstanceVar = num;
  }

  /**
   * Method
   */
  someMethod(): void {}

  /**
   * Static method
   */
  static staticMethod(): void {}

  /**
   * Getter
   */
  get getter(): number {
    return 5;
  }

  /**
   * Setter
   */
  set setter(n: number) {}
}

export interface Face {
  /**
   * Interface property
   */
  moof: string;
}

export namespace SomeSpace {
  /**
   * Namespaced number
   */
  export const spacedNumber = 4;
}
