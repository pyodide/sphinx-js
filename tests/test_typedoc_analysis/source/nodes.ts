export class Superclass {
  method() {}
}

export interface SuperInterface {}

export interface Interface extends SuperInterface {}

export interface InterfaceWithMembers {
  callableProperty(): void;
}

/**
 * An empty subclass
 */
export abstract class EmptySubclass extends Superclass implements Interface {}

export abstract class EmptySubclass2
  extends Promise<number>
  implements Interface {}

export const topLevelConst = 3;

/**
 * @param a Some number
 * @param b Some strings
 * @return The best number
 */
export function func(a: number = 1, ...b: string[]): number {
  return 4;
}

export class ClassWithProperties {
  static someStatic: number;
  someOptional?: number;
  private somePrivate: number;
  /**
   * This is totally normal!
   */
  someNormal: number;

  constructor(a: number) {}

  get gettable(): number {
    return 5;
  }

  set settable(value: string) {}
}

export class Indexable {
  [id: string]: any; // smoketest
}

// Test that we don't fail on a reexport
export { Blah } from "./exports";

/**
 * A super special type alias
 * @typeparam T The whatsit
 */
export type TestTypeAlias<T> = 1 | 2 | T;
