import {
  Comment,
  CommentDisplayPart,
  DeclarationReflection,
  ParameterReflection,
  ProjectReflection,
  ReferenceType,
  ReflectionKind,
  ReflectionVisitor,
  SignatureReflection,
  SomeType,
  TypeContext,
  TypeParameterReflection,
} from "typedoc";
import { referenceToXRef, convertType } from "./convertType.ts";
import {
  NO_DEFAULT,
  Attribute,
  Class,
  Description,
  DescriptionItem,
  Interface,
  IRFunction,
  Member,
  Param,
  Pathname,
  Return,
  TopLevelIR,
  TopLevel,
  Type,
  TypeParam,
} from "./ir.ts";
import { sep, relative } from "path";
import { SphinxJsConfig } from "./sphinxJsConfig.ts";
import { ReadonlySymbolToType } from "./redirectPrivateAliases.ts";

export function parseFilePath(path: string, base_dir: string): string[] {
  // First we want to know if path is under base_dir.
  // Get directions from base_dir to the path
  const rel = relative(base_dir, path);
  let pathSegments: string[];
  if (!rel.startsWith("..")) {
    // We don't have to go up so path is under base_dir
    pathSegments = rel.split(sep);
  } else {
    // It's not under base_dir... maybe it's in a global node_modules or
    // something? This makes it look the same as if it were under a local
    // node_modules.
    pathSegments = path.split(sep);
    pathSegments.reverse();
    const idx = pathSegments.indexOf("node_modules");
    if (idx !== -1) {
      pathSegments = pathSegments.slice(0, idx + 1);
    }
    pathSegments.reverse();
  }
  // Remove the file suffix from the last entry if it exists. If there is no .,
  // then this will leave it alone.
  let lastEntry = pathSegments.pop();
  if (lastEntry !== undefined) {
    pathSegments.push(lastEntry.slice(0, lastEntry.lastIndexOf(".")));
  }
  // Add a . to the start and a / after every entry so that if we join the
  // entries it looks like the correct relative path.
  // Hopefully it was actually a relative path of some sort...
  pathSegments.unshift(".");
  for (let i = 0; i < pathSegments.length - 1; i++) {
    pathSegments[i] += "/";
  }
  return pathSegments;
}

/**
 * We currently replace {a : () => void} with {a() => void}. "a" is a reflection
 * with a TypeLiteral type kind, and the type has name "__type". We don't want
 * this to appear in the docs so we have to check for it and remove it.
 */
function isAnonymousTypeLiteral(
  refl: DeclarationReflection | SignatureReflection,
): boolean {
  return refl.kindOf(ReflectionKind.TypeLiteral) && refl.name === "__type";
}

/**
 * A ReflectionVisitor that computes the path for each reflection for us.
 *
 * We want to compute the paths for both DeclarationReflections and
 * SignatureReflections.
 */
class PathComputer implements ReflectionVisitor {
  readonly basePath: string;
  // The maps we're trying to fill in.
  readonly pathMap: Map<DeclarationReflection | SignatureReflection, Pathname>;
  readonly filePathMap: Map<
    DeclarationReflection | SignatureReflection,
    Pathname
  >;
  // Record which reflections are documentation roots. Used in sphinx for
  // automodule and autosummary directives.
  readonly documentationRoots: Set<DeclarationReflection | SignatureReflection>;

  // State for the visitor
  parentKind: ReflectionKind | undefined;
  parentSegments: string[];
  filePath: string[];
  constructor(
    basePath: string,
    pathMap: Map<DeclarationReflection | SignatureReflection, Pathname>,
    filePathMap: Map<DeclarationReflection | SignatureReflection, Pathname>,
    documentationRoots: Set<DeclarationReflection | SignatureReflection>,
  ) {
    this.pathMap = pathMap;
    this.filePathMap = filePathMap;
    this.basePath = basePath;
    this.documentationRoots = documentationRoots;
    this.parentKind = undefined;
    this.parentSegments = [];
    this.filePath = [];
  }

  /**
   * If the name of the reflection is supposed to be a symbol, it should look
   * something like [Symbol.iterator] but typedoc just shows it as [iterator].
   * Downstream lexers to color the docs split on dots, but we don't want that
   * because here the dot is part of the name. Instead, we add a dot lookalike.
   */
  static fixSymbolName(refl: DeclarationReflection | SignatureReflection) {
    const SYMBOL_PREFIX = "[Symbol\u2024";
    if (refl.name.startsWith("[") && !refl.name.startsWith(SYMBOL_PREFIX)) {
      // Probably a symbol (are there other reasons the name would start with "["?)
      // \u2024 looks like a period but is not a period.
      // This isn't ideal, but otherwise the coloring is weird.
      refl.name = SYMBOL_PREFIX + refl.name.slice(1);
    }
  }

  /**
   * The main logic for this visitor. static for easier readability.
   */
  static computePath(
    refl: DeclarationReflection | SignatureReflection,
    parentKind: ReflectionKind,
    parentSegments: string[],
    filePath: string[],
  ): Pathname {
    // If no parentSegments, this is a "root", use the file path as the
    // parentSegments.
    // We have to copy the segments because we're going to mutate it.
    const segments = Array.from(
      parentSegments.length > 0 ? parentSegments : filePath,
    );
    // Skip some redundant names
    const suppressReflName =
      refl.kindOf(
        // Module names are redundant with the file path
        ReflectionKind.Module |
          // Signature names are redundant with the callable. TODO: do we want to
          // handle callables with multiple signatures?
          ReflectionKind.ConstructorSignature |
          ReflectionKind.CallSignature,
      ) || isAnonymousTypeLiteral(refl);
    if (suppressReflName) {
      return segments;
    }
    if (segments.length > 0) {
      // Add delimiter. For most things use a . e.g., parent.name but for
      // nonstatic class members we write Class#member
      const delimiter =
        parentKind === ReflectionKind.Class && !refl.flags.isStatic ? "#" : ".";
      segments[segments.length - 1] += delimiter;
    }
    // Add the name of the current reflection to the list
    segments.push(refl.name);
    return segments;
  }

  setPath(refl: DeclarationReflection | SignatureReflection): Pathname {
    PathComputer.fixSymbolName(refl);
    const segments = PathComputer.computePath(
      refl,
      this.parentKind!,
      this.parentSegments,
      this.filePath,
    );
    if (isAnonymousTypeLiteral(refl)) {
      // Rename the anonymous type literal to share its name with the attribute
      // it is the type of.
      refl.name = this.parentSegments.at(-1)!;
    }
    this.pathMap.set(refl, segments);
    this.filePathMap.set(refl, this.filePath);
    return segments;
  }

  // The visitor methods

  project(project: ProjectReflection) {
    // Compute the set of documentation roots.
    // This consists of all children of the Project and all children of Modules.
    for (const child of project.children || []) {
      this.documentationRoots.add(child);
    }
    for (const module of project.getChildrenByKind(ReflectionKind.Module)) {
      for (const child of module.children || []) {
        this.documentationRoots.add(child);
      }
    }
    // Visit children
    project.children?.forEach((x) => x.visit(this));
  }

  declaration(refl: DeclarationReflection) {
    if (refl.sources) {
      this.filePath = parseFilePath(refl.sources![0].fileName, this.basePath);
    }
    const segments = this.setPath(refl);
    // Update state for children
    const origParentSegs = this.parentSegments;
    const origParentKind = this.parentKind;
    this.parentSegments = segments;
    this.parentKind = refl.kind;
    // Visit children
    refl.children?.forEach((child) => child.visit(this));
    refl.signatures?.forEach((child) => child.visit(this));
    if (
      refl.kind === ReflectionKind.Property &&
      refl.type?.type == "reflection"
    ) {
      // If the property has a function type, we replace it with a function
      // described by the declaration. Just in case that happens we compute the
      // path for the declaration here.
      refl.type.declaration.visit(this);
    }
    // Restore state
    this.parentSegments = origParentSegs;
    this.parentKind = origParentKind;
  }

  signature(refl: SignatureReflection) {
    this.setPath(refl);
  }
}

// Some utilities for manipulating comments

/**
 * Convert CommentDisplayParts from typedoc IR to sphinx-js comment IR.
 * @param content List of CommentDisplayPart
 * @returns
 */
function renderCommentContent(content: CommentDisplayPart[]): Description {
  return content.map((x): DescriptionItem => {
    if (x.kind === "code") {
      return { type: "code", code: x.text };
    }
    if (x.kind === "text") {
      return { type: "text", text: x.text };
    }
    throw new Error("Not implemented");
  });
}

function renderCommentSummary(c: Comment | undefined): Description {
  if (!c) {
    return [];
  }
  return renderCommentContent(c.summary);
}

/**
 * Compute a map from blockTagName to list of comment descriptions.
 */
function getCommentBlockTags(c: Comment | undefined): {
  [key: string]: Description[];
} {
  if (!c) {
    return {};
  }
  const result: { [key: string]: Description[] } = {};
  for (const tag of c.blockTags) {
    const tagType = tag.tag.slice(1);
    if (!(tagType in result)) {
      result[tagType] = [];
    }
    const content: Description = [];
    if (tag.name) {
      // If the tag has a name field, add it as a DescriptionName
      content.push({
        type: "name",
        text: tag.name,
      });
    }
    content.push(...renderCommentContent(tag.content));
    result[tagType].push(content);
  }
  return result;
}

/**
 * The type returned by most methods on the converter.
 *
 * A pair, an optional TopLevel and an optional list of additional reflections
 * to convert.
 */
type ConvertResult = [
  TopLevelIR | undefined,
  DeclarationReflection[] | undefined,
];

/**
 * We generate some "synthetic parameters" when destructuring parameters. It
 * would be possible to convert directly to our IR but it causes some code
 * duplication. Instead, we keep track of the subset of fields that `paramToIR`
 * actually needs here.
 */
type ParamReflSubset = Pick<
  ParameterReflection,
  "comment" | "defaultValue" | "flags" | "name" | "type"
>;

/**
 * Main class for creating IR from the ProjectReflection.
 *
 * The main toIr logic is a sort of visitor for ReflectionKinds. We don't use
 * ReflectionVisitor because the division it uses for visitor methods is too
 * coarse.
 *
 * We visit in a breadth-first order, not for any super compelling reason.
 */
export class Converter {
  readonly project: ProjectReflection;
  readonly basePath: string;
  readonly config: SphinxJsConfig;
  readonly symbolToType: ReadonlySymbolToType;

  readonly pathMap: Map<DeclarationReflection | SignatureReflection, Pathname>;
  readonly filePathMap: Map<
    DeclarationReflection | SignatureReflection,
    Pathname
  >;
  readonly documentationRoots: Set<DeclarationReflection | SignatureReflection>;
  readonly typedocToIRMap: Map<DeclarationReflection, TopLevel>;

  constructor(
    project: ProjectReflection,
    basePath: string,
    config: SphinxJsConfig,
    symbolToType: ReadonlySymbolToType,
  ) {
    this.project = project;
    this.basePath = basePath;
    this.config = config;
    this.symbolToType = symbolToType;

    this.pathMap = new Map();
    this.filePathMap = new Map();
    this.documentationRoots = new Set();
    this.typedocToIRMap = new Map();
  }

  convertType(type: SomeType, context: TypeContext = TypeContext.none): Type {
    return convertType(
      this.basePath,
      this.pathMap,
      this.symbolToType,
      type,
      context,
    );
  }

  referenceToXRef(type: ReferenceType): Type {
    return referenceToXRef(
      this.basePath,
      this.pathMap,
      this.symbolToType,
      type,
    );
  }

  computePaths() {
    this.project.visit(
      new PathComputer(
        this.basePath,
        this.pathMap,
        this.filePathMap,
        this.documentationRoots,
      ),
    );
  }

  /**
   * Convert all Reflections.
   */
  convertAll(): TopLevelIR[] {
    const todo = Array.from(this.project.children!);
    const result: TopLevelIR[] = [];
    while (todo.length) {
      const node = todo.pop()!;
      const [converted, rest] = this.toIr(node);
      if (converted) {
        this.typedocToIRMap.set(node, converted);
        result.push(converted);
      }
      todo.push(...(rest || []));
    }
    return result;
  }

  /**
   * Convert the reflection and return a pair, the conversion result and a list
   * of descendent Reflections to convert. These descendents are either children
   * or signatures.
   *
   * @param object The reflection to convert
   * @returns A pair, a possible result IR object, and a list of descendent
   * Reflections that still need converting.
   */
  toIr(object: DeclarationReflection | SignatureReflection): ConvertResult {
    // ReflectionKinds that we give no conversion.
    if (
      object.kindOf(
        ReflectionKind.Module |
          ReflectionKind.Namespace |
          // TODO: document enums
          ReflectionKind.Enum |
          ReflectionKind.EnumMember |
          // A ReferenceReflection is when we reexport something.
          // TODO: should we handle this somehow?
          ReflectionKind.Reference,
      )
    ) {
      // TODO: The children of these have no rendered parent in the docs. If
      // "object" is marked as a documentation_root, maybe the children should
      // be too?
      return [undefined, (object as DeclarationReflection).children];
    }
    const kind = ReflectionKind[object.kind];
    const convertFunc = `convert${kind}` as keyof this;
    if (!this[convertFunc]) {
      throw new Error(`No known converter for kind ${kind}`);
    }
    // @ts-ignore
    const result: ConvertResult = this[convertFunc](object);
    if (this.documentationRoots.has(object) && result[0]) {
      result[0].documentation_root = true;
    }
    return result;
  }

  // Reflection visitor methods

  convertFunction(func: DeclarationReflection): ConvertResult {
    return [this.functionToIR(func), func.children];
  }
  convertMethod(func: DeclarationReflection): ConvertResult {
    return [this.functionToIR(func), func.children];
  }
  convertConstructor(func: DeclarationReflection): ConvertResult {
    return [this.functionToIR(func), func.children];
  }
  convertVariable(v: DeclarationReflection): ConvertResult {
    if (!v.type) {
      throw new Error(`Type of ${v.name} is undefined`);
    }
    let type: Type;
    if (v.comment?.modifierTags.has("@hidetype")) {
      type = [];
    } else {
      type = this.convertType(v.type);
    }
    const result: Attribute = {
      ...this.memberProps(v),
      ...this.topLevelProperties(v),
      readonly: false,
      kind: "attribute",
      type,
    };
    return [result, v.children];
  }

  /**
   * Return the unambiguous pathnames of implemented interfaces or extended
   * classes.
   */
  relatedTypes(
    cls: DeclarationReflection,
    kind: "extendedTypes" | "implementedTypes",
  ): Type[] {
    const origTypes = cls[kind] || [];
    const result: Type[] = [];
    for (const t of origTypes) {
      if (t.type !== "reference") {
        continue;
      }
      result.push(this.referenceToXRef(t));
    }
    return result;
  }

  convertClass(cls: DeclarationReflection): ConvertResult {
    const [constructor_, members] = this.constructorAndMembers(cls);
    const result: Class = {
      constructor_,
      members,
      supers: this.relatedTypes(cls, "extendedTypes"),
      is_abstract: cls.flags.isAbstract,
      interfaces: this.relatedTypes(cls, "implementedTypes"),
      type_params: this.typeParamsToIR(cls.typeParameters),
      ...this.topLevelProperties(cls),
      kind: "class",
    };
    return [result, cls.children];
  }

  convertInterface(cls: DeclarationReflection): ConvertResult {
    const [_, members] = this.constructorAndMembers(cls);
    const result: Interface = {
      members,
      supers: this.relatedTypes(cls, "extendedTypes"),
      type_params: this.typeParamsToIR(cls.typeParameters),
      ...this.topLevelProperties(cls),
      kind: "interface",
    };
    return [result, cls.children];
  }

  convertProperty(prop: DeclarationReflection): ConvertResult {
    if (
      prop.type?.type === "reflection" &&
      prop.type.declaration.kindOf(ReflectionKind.TypeLiteral) &&
      prop.type.declaration.signatures?.length
    ) {
      // Render {f: () => void} like {f(): void}
      // TODO: unclear if this is the right behavior. Maybe there should be a
      // way to pick?
      return [this.functionToIR(prop.type.declaration), []];
    }
    let type: Type;
    if (prop.comment?.modifierTags.has("@hidetype")) {
      // We should probably also be able to hide the type of a thing with a
      // function type literal type...
      type = [];
    } else {
      type = this.convertType(prop.type!);
    }
    const result: Attribute = {
      type,
      ...this.memberProps(prop),
      ...this.topLevelProperties(prop),
      description: renderCommentSummary(prop.comment),
      readonly: prop.flags.isReadonly,
      kind: "attribute",
    };
    return [result, prop.children];
  }

  /**
   * An Accessor is a thing with a getter or a setter. It should look exactly
   * like a Property in the rendered docs since the distinction is an
   * implementation detail.
   *
   * Specifically:
   * 1. an Accessor with a getter but no setter should be rendered as a readonly
   *    Property.
   * 2. an Accessor with a getter and a setter should be rendered as a
   *    read/write Property
   * 3. Not really sure what to do with an Accessor with a setter and no getter.
   *    That's kind of weird.
   */
  convertAccessor(prop: DeclarationReflection): ConvertResult {
    let type: SomeType;
    let sig: SignatureReflection;
    if (prop.getSignature) {
      // There's no signature to speak of for a getter: only a return type.
      sig = prop.getSignature;
      type = sig.type!;
    } else {
      if (!prop.setSignature) {
        throw new Error("???");
      }
      // ES6 says setters have exactly 1 param.
      sig = prop.setSignature;
      type = sig.parameters![0].type!;
    }
    // If there's no setter say it's readonly
    const readonly = !prop.setSignature;
    const result: Attribute = {
      type: this.convertType(type),
      readonly,
      ...this.memberProps(prop),
      ...this.topLevelProperties(prop),
      kind: "attribute",
    };
    result.description = renderCommentSummary(sig.comment);
    return [result, prop.children];
  }

  convertClassChild(child: DeclarationReflection): IRFunction | Attribute {
    if (
      !child.kindOf(
        ReflectionKind.Accessor |
          ReflectionKind.Constructor |
          ReflectionKind.Method |
          ReflectionKind.Property,
      )
    ) {
      throw new TypeError(
        "Expected an Accessor, Constructor, Method, or Property",
      );
    }
    // Should we assert that the "descendants" component is empty?
    return this.toIr(child)[0] as IRFunction | Attribute;
  }

  /**
   * Return the IR for the constructor and other members of a class or
   * interface.
   *
   * In TS, a constructor may have multiple (overloaded) type signatures but
   * only one implementation. (Same with functions.) So there's at most 1
   * constructor to return. Return None for the constructor if it is inherited
   * or implied rather than explicitly present in the class.
   *
   * @param refl Class or Interface
   * @returns A tuple of (constructor Function, list of other members)
   */
  constructorAndMembers(
    refl: DeclarationReflection,
  ): [IRFunction | null, (IRFunction | Attribute)[]] {
    let constructor: IRFunction | null = null;
    const members: (IRFunction | Attribute)[] = [];
    for (const child of refl.children || []) {
      if (child.inheritedFrom) {
        continue;
      }
      if (child.kindOf(ReflectionKind.Constructor)) {
        // This really, really should happen exactly once per class.
        constructor = this.functionToIR(child);
        constructor.returns = [];
        continue;
      }
      members.push(this.convertClassChild(child));
    }
    return [constructor, members];
  }

  /**
   * Compute common properties for all class members.
   */
  memberProps(refl: DeclarationReflection): Member {
    return {
      is_abstract: refl.flags.isAbstract,
      is_optional: refl.flags.isOptional,
      is_static: refl.flags.isStatic,
      is_private: refl.flags.isPrivate,
    };
  }

  /**
   * Compute common properties for all TopLevels.
   */
  topLevelProperties(
    refl: DeclarationReflection | SignatureReflection,
  ): TopLevel {
    const path = this.pathMap.get(refl);
    const filePath = this.filePathMap.get(refl)!;
    if (!path) {
      throw new Error(`Missing path for ${refl.name}`);
    }
    const block_tags = getCommentBlockTags(refl.comment);
    let deprecated: Description | boolean =
      block_tags["deprecated"]?.[0] || false;
    if (deprecated && deprecated.length === 0) {
      deprecated = true;
    }
    return {
      name: refl.name,
      path,
      deppath: filePath.join(""),
      filename: "",
      description: renderCommentSummary(refl.comment),
      modifier_tags: Array.from(refl.comment?.modifierTags || []),
      block_tags,
      deprecated,
      examples: block_tags["example"] || [],
      properties: [],
      see_alsos: [],
      exported_from: filePath,
      line: refl.sources?.[0].line || null,
      documentation_root: false,
    };
  }

  /**
   * We want to document a destructured argument as if it were several separate
   * arguments. This finds complex inline object types in the arguments list of
   * a function and "destructures" them into separately documented arguments.
   *
   * E.g., a function
   *
   *       /**
   *       * @param options
   *       * @destructure options
   *       *./
   *       function f({x , y } : {
   *           /** The x value *./
   *           x : number,
   *           /** The y value *./
   *           y : string
   *       }){ ... }
   *
   * should be documented like:
   *
   *       options.x (number) The x value
   *       options.y (number) The y value
   */
  _destructureParam(param: ParameterReflection): ParamReflSubset[] {
    const type = param.type;
    if (type?.type !== "reflection") {
      throw new Error("Unexpected");
    }
    const decl = type.declaration;
    const children = decl.children!;
    // Sort destructured parameter by order in the type declaration in the
    // source file. Before we sort they are in alphabetical order by name. Maybe
    // we should have a way to pick the desired behavior? There are three
    // reasonable orders:
    //
    // 1. alphabetical by name
    // 2. In order of the @options.b annotations
    // 3. In order of their declarations in the type
    //
    // This does order 3
    children.sort(
      ({ sources: a }, { sources: b }) =>
        a![0].line - b![0].line || a![0].character - b![0].character,
    );
    const result: ParamReflSubset[] = [];
    for (const child of children) {
      result.push({
        name: param.name + "." + child.name,
        type: child.type,
        comment: child.comment,
        defaultValue: undefined,
        flags: child.flags,
      });
    }
    return result;
  }

  _destructureParams(sig: SignatureReflection): ParamReflSubset[] {
    const result = [];
    // Destructure a parameter if it's type is a reflection and it is requested
    // with @destructure or _shouldDestructureArg.
    const destructureTargets = sig.comment
      ?.getTags("@destructure")
      .flatMap((tag) => tag.content[0].text.split(" "));
    const shouldDestructure = (p: ParameterReflection) => {
      if (p.type?.type !== "reflection") {
        return false;
      }
      if (destructureTargets?.includes(p.name)) {
        return true;
      }
      const shouldDestructure = this.config.shouldDestructureArg;
      return shouldDestructure && shouldDestructure(p);
    };
    for (const p of sig.parameters || []) {
      if (shouldDestructure(p)) {
        result.push(...this._destructureParam(p));
      } else {
        result.push(p);
      }
    }
    return result;
  }

  /**
   * Convert a signature parameter
   */
  paramToIR(param: ParamReflSubset): Param {
    let type: Type = [];
    if (param.type) {
      type = this.convertType(param.type);
    }
    let description = renderCommentSummary(param.comment);
    if (description.length === 0 && param.type?.type === "reflection") {
      // If the parameter type is given as the typeof something else, use the
      // description from the target?
      // TODO: isn't this a weird thing to do here? I think we should remove it?
      description = renderCommentSummary(
        param.type.declaration?.signatures?.[0].comment,
      );
    }
    return {
      name: param.name,
      has_default: !!param.defaultValue,
      default: param.defaultValue || NO_DEFAULT,
      is_variadic: param.flags.isRest,
      description,
      type,
    };
  }
  /**
   * Convert callables: Function, Method, and Constructor.
   * @param func
   * @returns
   */
  functionToIR(func: DeclarationReflection): IRFunction {
    // There's really nothing in the function itself; all the interesting bits
    // are in the 'signatures' property. We support only the first signature at
    // the moment, because to do otherwise would create multiple identical
    // pathnames to the same function, which would cause the suffix tree to
    // raise an exception while being built. An eventual solution might be to
    // store the signatures in a one-to- many attr of Functions.
    const first_sig = func.signatures![0]; // Should always have at least one

    // Make sure name matches, can be different in case this comes from
    // isAnonymousTypeLiteral returning true.
    first_sig.name = func.name;
    const params = this._destructureParams(first_sig);
    let returns: Return[] = [];
    let is_async = false;
    // We want to suppress the return type for constructors (it's technically
    // correct that it returns a class instance but it looks weird).
    // Also hide explicit void return type.
    const voidReturnType =
      func.kindOf(ReflectionKind.Constructor) ||
      !first_sig.type ||
      (first_sig.type.type === "intrinsic" && first_sig.type.name === "void");
    let type_params = this.typeParamsToIR(first_sig.typeParameters);
    if (func.kindOf(ReflectionKind.Constructor)) {
      // I think this is wrong
      // TODO: remove it
      type_params = this.typeParamsToIR(
        (func.parent as DeclarationReflection).typeParameters,
      );
    }
    const topLevel = this.topLevelProperties(first_sig);
    if (!voidReturnType && first_sig.type) {
      // Compute return comment and return annotation.
      const returnType = this.convertType(first_sig.type);
      const description = topLevel.block_tags.returns?.[0] || [];
      returns = [{ type: returnType, description }];
      // Put async in front of the function if it returns a Promise.
      // Question: Is there any important difference between an actual async
      // function and a non-async one that returns a Promise?
      is_async =
        first_sig.type.type === "reference" &&
        first_sig.type.name === "Promise";
    }
    return {
      ...topLevel,
      ...this.memberProps(func),
      is_async,
      params: params?.map(this.paramToIR.bind(this)) || [],
      type_params,
      returns,
      exceptions: [],
      kind: "function",
    };
  }
  typeParamsToIR(
    typeParams: TypeParameterReflection[] | undefined,
  ): TypeParam[] {
    return typeParams?.map((typeParam) => this.typeParamToIR(typeParam)) || [];
  }

  typeParamToIR(typeParam: TypeParameterReflection): TypeParam {
    const extends_ = typeParam.type
      ? this.convertType(typeParam.type, TypeContext.referenceTypeArgument)
      : null;
    return {
      name: typeParam.name,
      extends: extends_,
      description: renderCommentSummary(typeParam.comment),
    };
  }

  convertTypeAlias(ty: DeclarationReflection): ConvertResult {
    const ir: TopLevelIR = {
      ...this.topLevelProperties(ty),
      kind: "typeAlias",
      type: this.convertType(ty.type!),
      type_params: this.typeParamsToIR(ty.typeParameters),
    };
    return [ir, ty.children];
  }
}
