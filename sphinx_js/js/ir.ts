// Define the types for our IR. Must match the cattrs+json serialization
// format from ir.py

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
  sourcefilename: string | null;
  qualifiedName: string | null;
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

export type NoDefault = { _no_default: true };
export const NO_DEFAULT: NoDefault = { _no_default: true };

export type Member = {
  is_abstract: boolean;
  is_optional: boolean;
  is_static: boolean;
  is_private: boolean;
};

export type TypeParam = {
  name: string;
  extends: Type | null;
  description: Description;
};

export type Param = {
  name: string;
  description: Description;
  is_variadic: boolean;
  has_default: boolean;
  default: string | NoDefault;
  type: Type;
};

export type Return = {
  type: Type;
  description: Description;
};

export type Module = {
  filename: string;
  deppath: string;
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
  deppath: string;
  description: Description;
  modifier_tags: string[];
  block_tags: { [key: string]: Description[] };
  line: number | null;
  deprecated: Description | boolean;
  examples: Description[];
  see_alsos: string[];
  properties: Attribute[];
  exported_from: Pathname | null;
  documentation_root: boolean;
};

export type Attribute = TopLevel &
  Member & {
    type: Type;
    readonly: boolean;
    kind: "attribute";
  };

export type IRFunction = TopLevel &
  Member & {
    is_async: boolean;
    params: Param[];
    returns: Return[];
    type_params: TypeParam[];
    kind: "function";
    exceptions: never[];
  };

export type _MembersAndSupers = {
  members: (IRFunction | Attribute)[];
  supers: Type[];
};

export type Interface = TopLevel &
  _MembersAndSupers & {
    type_params: TypeParam[];
    kind: "interface";
  };

export type Class = TopLevel &
  _MembersAndSupers & {
    constructor_: IRFunction | null;
    is_abstract: boolean;
    interfaces: Type[];
    type_params: TypeParam[];
    kind: "class";
  };

export type TypeAlias = TopLevel & {
  kind: "typeAlias";
  type: Type;
  type_params: TypeParam[];
};

export type TopLevelIR = Attribute | IRFunction | Class | Interface | TypeAlias;
