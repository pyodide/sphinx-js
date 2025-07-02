import {
  ArrayType,
  ConditionalType,
  DeclarationReflection,
  IndexedAccessType,
  InferredType,
  IntersectionType,
  IntrinsicType,
  LiteralType,
  MappedType,
  NamedTupleMember,
  OptionalType,
  PredicateType,
  QueryType,
  ReferenceType,
  ReflectionKind,
  ReflectionType,
  RestType,
  SignatureReflection,
  SomeType,
  TemplateLiteralType,
  TupleType,
  TypeContext,
  TypeOperatorType,
  TypeVisitor,
  UnionType,
  UnknownType,
} from "typedoc";
import {
  Type,
  TypeXRefExternal,
  TypeXRefInternal,
  intrinsicType,
} from "./ir.js";
import { parseFilePath } from "./convertTopLevel.js";
import { ReadonlySymbolToType } from "./redirectPrivateAliases.js";

/**
 * Convert types into a list of strings and XRefs.
 *
 * Most visitor nodes should be similar to the implementation of getTypeString
 * on the same type.
 */
class TypeConverter implements TypeVisitor<Type> {
  private readonly basePath: string;
  // For resolving XRefs.
  private readonly reflToPath: ReadonlyMap<
    DeclarationReflection | SignatureReflection,
    string[]
  >;
  private readonly symbolToType: ReadonlySymbolToType;

  constructor(
    basePath: string,
    reflToPath: ReadonlyMap<
      DeclarationReflection | SignatureReflection,
      string[]
    >,
    symbolToType: ReadonlySymbolToType,
  ) {
    this.basePath = basePath;
    this.reflToPath = reflToPath;
    this.symbolToType = symbolToType;
  }

  /**
   * Helper for inserting type parameters
   */
  addTypeArguments(
    type: { typeArguments?: SomeType[] | undefined },
    l: Type,
  ): Type {
    if (!type.typeArguments || type.typeArguments.length === 0) {
      return l;
    }
    l.push("<");
    for (const arg of type.typeArguments) {
      l.push(...arg.visit(this));
      l.push(", ");
    }
    l.pop();
    l.push(">");
    return l;
  }

  /**
   * Convert the type, maybe add parentheses
   */
  convert(type: SomeType, context: TypeContext): Type {
    const result = type.visit(this);
    if (type.needsParenthesis(context)) {
      result.unshift("(");
      result.push(")");
    }
    return result;
  }

  conditional(type: ConditionalType): Type {
    return [
      ...this.convert(type.checkType, TypeContext.conditionalCheck),
      " extends ",
      ...this.convert(type.extendsType, TypeContext.conditionalExtends),
      " ? ",
      ...this.convert(type.trueType, TypeContext.conditionalTrue),
      " : ",
      ...this.convert(type.falseType, TypeContext.conditionalFalse),
    ];
  }
  indexedAccess(type: IndexedAccessType): Type {
    return [
      ...this.convert(type.objectType, TypeContext.indexedObject),
      "[",
      ...this.convert(type.indexType, TypeContext.indexedIndex),
      "]",
    ];
  }
  inferred(type: InferredType): Type {
    if (type.constraint) {
      return [
        `infer ${type.name} extends `,
        ...this.convert(type.constraint, TypeContext.inferredConstraint),
      ];
    }
    return [`infer ${type.name}`];
  }
  intersection(type: IntersectionType): Type {
    const result: Type = [];
    for (const elt of type.types) {
      result.push(...this.convert(elt, TypeContext.intersectionElement));
      result.push(" & ");
    }
    result.pop();
    return result;
  }
  intrinsic(type: IntrinsicType): Type {
    return [intrinsicType(type.name)];
  }
  literal(type: LiteralType): Type {
    if (type.value === null) {
      return [intrinsicType("null")];
    }
    return [JSON.stringify(type.value)];
  }
  mapped(type: MappedType): Type {
    const read = {
      "+": "readonly ",
      "-": "-readonly ",
      "": "",
    }[type.readonlyModifier ?? ""];

    const opt = {
      "+": "?",
      "-": "-?",
      "": "",
    }[type.optionalModifier ?? ""];

    const parts: Type = [
      "{ ",
      read,
      "[",
      type.parameter,
      " in ",
      ...this.convert(type.parameterType, TypeContext.mappedParameter),
    ];

    if (type.nameType) {
      parts.push(
        " as ",
        ...this.convert(type.nameType, TypeContext.mappedName),
      );
    }

    parts.push(
      "]",
      opt,
      ": ",
      ...this.convert(type.templateType, TypeContext.mappedTemplate),
      " }",
    );
    return parts;
  }
  optional(type: OptionalType): Type {
    return [
      ...this.convert(type.elementType, TypeContext.optionalElement),
      "?",
    ];
  }
  predicate(type: PredicateType): Type {
    // Consider using typedoc's representation for this instead of this custom
    // string.
    return [
      intrinsicType("boolean"),
      " (typeguard for ",
      ...type.targetType!.visit(this),
      ")",
    ];
  }
  query(type: QueryType): Type {
    return [
      "typeof ",
      ...this.convert(type.queryType, TypeContext.queryTypeTarget),
    ];
  }
  /**
   * If it's a reference to a private type alias, replace it with a reflection.
   * Otherwise return undefined.
   */
  convertPrivateReferenceToReflection(type: ReferenceType): Type | undefined {
    if (type.reflection) {
      const refl = type.reflection as DeclarationReflection;

      // If it's private, we don't really want to emit an XRef to it. In the
      // typedocPlugin.ts we tried to calculate Reflections for these, so now
      // we try to look it up. I couldn't get the line+column numbers to match
      // up so in this case we index on file name and reference name.

      // Another place where we incorrectly handle merged declarations
      const src = type.reflection?.sources?.[0];
      if (!src) {
        return undefined;
      }
      const newTarget = this.symbolToType.get(
        `${src.fullFileName}:${refl.name}`,
      );
      if (newTarget) {
        // TODO: this doesn't handle parentheses correctly.
        return newTarget.visit(this);
      }
      return undefined;
    }

    if (!type.symbolId) {
      throw new Error("This should not happen");
    }
    // See if this refers to a private type. In that case we should inline the
    // type reflection rather than referring to the non-exported name. Ideally
    // we should key on position rather than name (the same file can have
    // multiple private types with the same name potentially). But it doesn't
    // seem to be working.
    const newTarget = this.symbolToType.get(
      `${type.symbolId.fileName}:${type.name}`,
    );
    if (newTarget) {
      // TODO: this doesn't handle parentheses correctly.
      return newTarget.visit(this);
    }
    return undefined;
  }
  /**
   * Convert a reference type to either an XRefExternal or an XRefInternal. It
   * works on things that `convertPrivateReferenceToReflection` but it will
   * throw an error if the type `isIntentionallyBroken`.
   *
   * This logic is also used for relatedTypes for classes (extends and
   * implements).
   * TODO: handle type arguments in extends and implements.
   */
  convertReferenceToXRef(type: ReferenceType): Type {
    if (type.isIntentionallyBroken()) {
      throw new Error("Bad type");
    }

    if (type.reflection) {
      const path = this.reflToPath.get(
        type.reflection as DeclarationReflection,
      );
      if (!path) {
        throw new Error(
          `Broken internal xref to ${type.reflection?.toStringHierarchy()}`,
        );
      }
      const xref: TypeXRefInternal = {
        name: type.name,
        path,
        type: "internal",
      };
      return this.addTypeArguments(type, [xref]);
    }

    if (!type.symbolId) {
      throw new Error("This shouldn't happen");
    }

    const path = parseFilePath(type.symbolId.fileName, this.basePath);
    if (path.includes("node_modules/")) {
      // External reference
      const xref: TypeXRefExternal = {
        name: type.name,
        package: type.package!,
        qualifiedName: type.symbolId.qualifiedName || null,
        sourcefilename: type.symbolId.fileName || null,
        type: "external",
      };
      return this.addTypeArguments(type, [xref]);
    } else {
      // TODO: I'm not sure that it's right to generate an internal xref here.
      // We need better test coverage for this code path.
      const xref: TypeXRefInternal = {
        name: type.name,
        path,
        type: "internal",
      };
      return this.addTypeArguments(type, [xref]);
    }
  }

  reference(type: ReferenceType): Type {
    // if we got a reflection use that. It's not all that clear how to deal
    // with type arguments here though...
    const res = this.convertPrivateReferenceToReflection(type);
    if (res) {
      return res;
    }
    if (type.isIntentionallyBroken()) {
      // If it's intentionally broken, don't add an xref. It's probably a type
      // parameter.
      return this.addTypeArguments(type, [type.name]);
    } else {
      return this.convertReferenceToXRef(type);
    }
  }
  reflection(type: ReflectionType): Type {
    if (type.declaration.kindOf(ReflectionKind.TypeLiteral)) {
      return this.convertTypeLiteral(type.declaration);
    }
    if (type.declaration.kindOf(ReflectionKind.Constructor)) {
      const result = this.convertSignature(type.declaration.signatures![0]);
      result.unshift("{new ");
      result.push("}");
      return result;
    }
    if (type.declaration.kindOf(ReflectionKind.FunctionOrMethod)) {
      return this.convertSignature(type.declaration.signatures![0]);
    }
    throw new Error("Not implemented");
  }
  rest(type: RestType): Type {
    return ["...", ...this.convert(type.elementType, TypeContext.restElement)];
  }
  templateLiteral(type: TemplateLiteralType): Type {
    return [
      "`",
      type.head,
      ...type.tail.flatMap(([type, text]) => {
        return [
          "${",
          ...this.convert(type, TypeContext.templateLiteralElement),
          "}",
          text,
        ];
      }),
      "`",
    ];
  }
  tuple(type: TupleType): Type {
    const result: Type = [];
    for (const elt of type.elements) {
      result.push(...this.convert(elt, TypeContext.tupleElement));
      result.push(", ");
    }
    result.pop();
    result.unshift("[");
    result.push("]");
    return result;
  }
  namedTupleMember(type: NamedTupleMember): Type {
    const result: Type = [`${type.name}${type.isOptional ? "?" : ""}: `];
    result.push(...this.convert(type.element, TypeContext.tupleElement));
    return result;
  }
  typeOperator(type: TypeOperatorType): Type {
    return [
      type.operator,
      " ",
      ...this.convert(type.target, TypeContext.typeOperatorTarget),
    ];
  }
  union(type: UnionType): Type {
    const result: Type = [];
    for (const elt of type.types) {
      result.push(...this.convert(elt, TypeContext.unionElement));
      result.push(" | ");
    }
    result.pop();
    return result;
  }
  unknown(type: UnknownType): Type {
    // I'm not sure how we get here: generally nobody explicitly annotates
    // unknown, maybe it's inferred sometimes?
    return [type.name];
  }
  array(t: ArrayType): Type {
    const res = this.convert(t.elementType, TypeContext.arrayElement);
    res.push("[]");
    return res;
  }

  convertSignature(sig: SignatureReflection): Type {
    const result: Type = ["("];
    for (const param of sig.parameters || []) {
      result.push(param.name + ": ");
      result.push(...(param.type?.visit(this) || []));
      result.push(", ");
    }
    if (sig.parameters?.length) {
      result.pop();
    }
    result.push(") => ");
    if (sig.type) {
      result.push(...sig.type.visit(this));
    } else {
      result.push(intrinsicType("void"));
    }
    return result;
  }

  convertTypeLiteral(lit: DeclarationReflection): Type {
    if (lit.signatures) {
      return this.convertSignature(lit.signatures[0]);
    }
    const result: Type = ["{ "];
    // lit.indexSignature for 0.25.x, lit.indexSignatures for 0.26.0 and later.
    const index_sig = lit.indexSignature ?? lit.indexSignatures?.[0];
    if (index_sig) {
      if (index_sig.parameters?.length !== 1) {
        throw new Error("oops");
      }
      const key = index_sig.parameters[0];
      // There's no exact TypeContext for indexedAccess b/c typedoc doesn't
      // render it like this. mappedParameter and mappedTemplate look quite
      // similar:
      // [k in mappedParam]: mappedTemplate
      //  vs
      // [k: keyType]: valueType
      const keyType = this.convert(key.type!, TypeContext.mappedParameter);
      const valueType = this.convert(
        index_sig.type!,
        TypeContext.mappedTemplate,
      );
      result.push("[", key.name, ": ");
      result.push(...keyType);
      result.push("]", ": ");
      result.push(...valueType);
      result.push("; ");
    }
    for (const child of lit.children || []) {
      result.push(child.name);
      if (child.flags.isOptional) {
        result.push("?: ");
      } else {
        result.push(": ");
      }
      result.push(...(child.type?.visit(this) || []));
      result.push("; ");
    }
    result.push("}");
    return result;
  }
}

export function convertType(
  basePath: string,
  reflToPath: ReadonlyMap<
    DeclarationReflection | SignatureReflection,
    string[]
  >,
  symbolToType: ReadonlySymbolToType,
  type: SomeType,
  context: TypeContext = TypeContext.none,
): Type {
  const typeConverter = new TypeConverter(basePath, reflToPath, symbolToType);
  return typeConverter.convert(type, context);
}

export function referenceToXRef(
  basePath: string,
  reflToPath: ReadonlyMap<
    DeclarationReflection | SignatureReflection,
    string[]
  >,
  symbolToType: ReadonlySymbolToType,
  type: ReferenceType,
): Type {
  const converter = new TypeConverter(basePath, reflToPath, symbolToType);
  return converter.convertReferenceToXRef(type);
}
