import { DeclarationReference, DeclarationReflection } from "typedoc";

export type TypeXRefIntrinsic = {
  name: string;
  type: "intrinsic";
};

export function intrinsicType(name: string): TypeXRefIntrinsic {
  return {
    name,
    type: "intrinsic",
  };
}

export type TypeXRefInternal = {
  name: string;
  path: string[];
  type: "internal";
};

export type TypeXRefExternal = {
  name: string;
  package: string;
  sourcefilename: string | undefined;
  qualifiedName: string | undefined;
  type: "external";
};

export type TypeXRef = TypeXRefExternal | TypeXRefInternal | TypeXRefIntrinsic;
export type Type = (string | TypeXRef)[];

export type DescriptionName = {
  text: string;
  type: "name";
};

export type DescriptionText = {
  text: string;
  type: "text";
};

export type DescriptionCode = {
  code: string;
  type: "code";
};

export type DescriptionItem =
  | DescriptionName
  | DescriptionText
  | DescriptionCode;
export type Description = DescriptionItem[];

export type Pathname = string[];

export type NoDefault = { _noDefault: true };
export const NO_DEFAULT = {};

export type _Member = {
  is_abstract: boolean;
  is_optional: boolean;
  is_static: boolean;
  is_private: boolean;
};

export function memberProps(a: DeclarationReflection): _Member {
  return {
    is_abstract: a.flags.isAbstract,
    is_optional: a.flags.isOptional,
    is_static: a.flags.isStatic,
    is_private: a.flags.isPrivate,
  };
}

export type TypeParam = {
  name: string;
  extends: Type;
  description: Description;
};

export type ParamBase = {
  name: string;
  description: Description;
  is_variadic: boolean;
  type?: Type;
};

export type ParamWithDefault = ParamBase & {
  has_default: boolean;
  default: string | undefined;
};

export type ParamNoDefault = ParamBase & {
  has_default: false;
  default: NoDefault;
};

export type Param = ParamWithDefault | ParamNoDefault;

export type Return = {
  type: Type;
  description: Description;
};

export type Module = {
  filename: string;
  deppath?: string;
  path: Pathname;
  line: number;
  attributes: TopLevel[];
  functions: IRFunction[];
  classes: Class[];
};

export type TopLevel = {
  name: string;
  path: Pathname;
  filename: string;
  deppath?: string;
  description: Description;
  modifier_tags: string[];
  block_tags: { [key: string]: Description[] };
  line: number | undefined;
  deprecated: Description | boolean;
  examples: Description[];
  see_alsos: string[];
  properties: Attribute[];
  exported_from?: Pathname;
  //   kind: string;
};

export type Attribute = TopLevel &
  _Member & {
    type: Type;
    kind: "attributes";
  };

export type IRFunction = TopLevel &
  _Member & {
    is_async: boolean;
    params: Param[];
    returns: Return[];
    type_params: TypeParam[];
    kind: "functions";
    exceptions: never[];
  };

export type _MembersAndSupers = {
  members: (IRFunction | Attribute)[];
  supers: Pathname[];
};

export type Interface = TopLevel &
  _MembersAndSupers & {
    type_params: TypeParam[];
    kind: "classes";
  };

export type Class = TopLevel &
  _MembersAndSupers & {
    constructor_: IRFunction | undefined;
    is_abstract: boolean;
    interfaces: Pathname[];
    type_params: TypeParam[];
    kind: "classes";
  };

export type TopLevelIR = Attribute | IRFunction | Class | Interface;