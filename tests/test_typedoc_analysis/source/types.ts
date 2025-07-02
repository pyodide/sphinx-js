// Basic types: https://www.typescriptlang.org/docs/handbook/basic-types.html

import { Blah } from "./exports";

export enum Color {
  Red = 1,
  Green = 2,
}

export let bool: boolean;
export let num: number;
export let str: string;
export let array: number[];
export let genericArray: Array<number>;
export let tuple: [string, number];
export let color: Color;
export let unk: unknown;
export let whatever: any;
export let voidy: void;
export let undef: undefined;
export let nully: null;
export let nev: never;
export let obj: object;
export let sym: symbol;

// Interfaces (https://www.typescriptlang.org/docs/handbook/interfaces.html)

export interface Interface {
  readonly readOnlyNum: number;
  [someProp: number]: string; // Just a smoketest for now. (IOW, make sure the analysis engine doesn't crash on it.) We'll need more work to handle members with no names.
}

export function interfacer(a: Interface) {}

export interface FunctionInterface {
  (thing: string, ding: number): boolean; // just a smoketest for now
}

// Functions. Basic function types are covered by ConvertNodeTests.test_function.

export function noThis(this: void) {
  // smoketest
}

// Make sure multi-signature functions don't crash us:
export function overload(x: string[]): number;
export function overload(x: number): number;
export function overload(x): any {}

// Literal types (https://www.typescriptlang.org/docs/handbook/literal-types.html)

export type CertainNumbers = 1 | 2 | 4;
export let certainNumbers: CertainNumbers = 2;

// Unions and intersections (https://www.typescriptlang.org/docs/handbook/unions-and-intersections.html)

export let union: number | string | Color = Color.Red;

export interface FooHaver {
  foo: string;
}

export interface BarHaver {
  bar: string;
}

export let intersection: FooHaver & BarHaver;

// Generics (https://www.typescriptlang.org/docs/handbook/generics.html)

export function aryIdentity<T>(things: T[]): T[] {
  console.log(things.length);
  return things;
}

export class GenericNumber<T> {
  add: (x: T, y: T) => T;
}

// Generic constraints:

export interface Lengthwise {
  length: number;
}

/**
 * @typeParam T - the identity type
 */
export function constrainedIdentity<T extends Lengthwise>(arg: T): T {
  return arg;
}

/**
 * @typeParam T - The type of the object
 * @typeParam K - The type of the key
 */
export function getProperty<T, K extends keyof T>(obj: T, key: K) {
  return obj[key];
}

export class A {}

export function create1(c: { new (x: number): A }): A {
  return new c(7);
}

export function create2<T>(c: { new (): T }): T {
  return new c();
}

/**
 * @typeParam S - The type we contain
 */
export class ParamClass<S extends number[]> {
  constructor() {}
}

// Utility types (https://www.typescriptlang.org/docs/handbook/utility-types.html)

// Most type references in here have ResolvedReferences. These test cases are
// for "SymbolReference". See typedoc/src/lib/models/types.ts

// Partial should generate a SymbolReference that we turn into a
// TypeXRefExternal
export let partial: Partial<string>;

// Blah should generate a SymbolReference that we turn into a
// TypeXRefInternal
export let internalSymbolReference: Blah;

// Complex: nested nightmares that show our ability to handle compound typing constructs

export function objProps(
  a: { label: string },
  b: { label: string; [key: number]: string },
) {}

export let option: { a: number; b?: string };

/**
 * Code 1 had `single ticks around it`.
 * Code 2 has ``double ticks around it``.
 * Code 3 has a :sphinx:role:`before it`.
 *
 * ```js
 * A JS code pen!
 * ```
 * And some closing words.
 */
export function codeInDescription() {}

/**
 * An example with destructured args 1
 *
 * @param options
 * @param options.a - The 'a' string.
 * @param options.b - The 'b' string.
 * @destructure options
 */
export function destructureTest({ a, b }: { b: { c: string }; a: string }) {}

/**
 * An example with destructured args 2
 *
 * @param options
 * @destructure options
 */
export function destructureTest2({
  a,
  b,
}: {
  /** The 'b' object. */
  b: { c: string };
  /**  The 'a' string. */
  a: string;
}) {}

/**
 * An example with no destructured args 3
 *
 * @param options - The options.
 * @param options.a - The 'a' string.
 * @param options.b - The 'b' string.
 */
export function destructureTest3({ a, b }: { a: string; b: { c: string } }) {}

/**
 * A test for should_destructure_arg 4
 */
export function destructureTest4(destructureThisPlease: {
  /**  The 'a' string. */
  a: string;
}) {}

/**
 * An example with a function as argument
 *
 * @param a - A number reducer.
 */
export function funcArg(a: (b: number, c: number) => number) {}

export function namedTupleArg(namedTuple: [key: string, value: any]) {}

export let queryType: typeof A;
export let typeOperatorType: keyof A;

type PrivateTypeAlias1 = { a: number; b: string };

// Should expand the private type alias
export let typeIsPrivateTypeAlias1: PrivateTypeAlias1;

/** @private */
export type PrivateTypeAlias2 = { a: number; b: string };

// Should expand the private type alias
export let typeIsPrivateTypeAlias2: PrivateTypeAlias2;

/**
 * Some comment
 * @hidetype
 */
export let hiddenType: number;

export class HasHiddenTypeMember {
  /**
   * Some comment
   * @hidetype
   */
  hasHiddenType: number;
}

export let restType: [...number[]];

export let indexedAccessType: FunctionInterface["length"];

export type ConditionalType<T> = T extends A ? 1 : 2;

export type InferredType<T> = T extends Promise<infer S> ? S : T;

export type keys = "A" | "B" | "C";

export type MappedType1 = { [property in keys]: number };
export type MappedType2 = { -readonly [property in keys]?: number };
export type MappedType3 = { readonly [property in keys]-?: number };

export type TemplateLiteral = `${number}: ${string}`;

export type OptionalType = [number?];

/**
 * @hidetype
 * @omitFromAutoModule
 * @destructure a.b
 * @summaryLink :role:`target`
 */
export type CustomTags = {};
