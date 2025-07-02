import assert from "node:assert";
import { test, suite, before } from "node:test";
import { run } from "../sphinx_js/js/cli";
import { TopLevelIR, Type } from "../sphinx_js/js/ir";
import { Application } from "typedoc";

function joinType(t: Type): string {
  return t.map((x) => (typeof x === "string" ? x : x.name)).join("");
}

function resolveFile(path: string): string {
  return import.meta.dirname + "/" + path;
}

suite("types.ts", async () => {
  let app: Application;
  let results: TopLevelIR[];
  let map: Map<string, TopLevelIR>;
  before(async () => {
    [app, results] = await run([
      "--sphinxJsConfig",
      resolveFile("sphinxJsConfig.ts"),
      "--entryPointStrategy",
      "expand",
      "--tsconfig",
      resolveFile("test_typedoc_analysis/source/tsconfig.json"),
      "--basePath",
      resolveFile("test_typedoc_analysis/source"),
      resolveFile("test_typedoc_analysis/source/types.ts"),
    ]);
    map = new Map(results.map((res) => [res.name, res]));
  });
  function getObject(name: string): TopLevelIR {
    const obj = map.get(name);
    assert(obj);
    return obj;
  }
  suite("basic", async () => {
    for (const [obj_name, type_name] of [
      ["bool", "boolean"],
      ["num", "number"],
      ["str", "string"],
      ["array", "number[]"],
      ["genericArray", "number[]"],
      ["tuple", "[string, number]"],
      ["color", "Color"],
      ["unk", "unknown"],
      ["whatever", "any"],
      ["voidy", "void"],
      ["undef", "undefined"],
      ["nully", "null"],
      ["nev", "never"],
      ["obj", "object"],
      ["sym", "symbol"],
    ]) {
      await test(obj_name, () => {
        const obj = getObject(obj_name);
        assert.strictEqual(obj.kind, "attribute");
        assert.strictEqual(joinType(obj.type), type_name);
      });
    }
  });
  await test("named_interface", () => {
    const obj = getObject("interfacer");
    assert.strictEqual(obj.kind, "function");
    assert.deepStrictEqual(obj.params[0].type, [
      {
        name: "Interface",
        path: ["./", "types.", "Interface"],
        type: "internal",
      },
    ]);
  });
  await test("interface_readonly_member", () => {
    const obj = getObject("Interface");
    assert.strictEqual(obj.kind, "interface");
    const readOnlyNum = obj.members[0];
    assert.strictEqual(readOnlyNum.kind, "attribute");
    assert.strictEqual(readOnlyNum.name, "readOnlyNum");
    assert.deepStrictEqual(readOnlyNum.type, [
      { name: "number", type: "intrinsic" },
    ]);
  });
  await test("array", () => {
    const obj = getObject("overload");
    assert.strictEqual(obj.kind, "function");
    assert.deepStrictEqual(obj.params[0].type, [
      { name: "string", type: "intrinsic" },
      "[]",
    ]);
  });
  await test("literal_types", () => {
    const obj = getObject("certainNumbers");
    assert.strictEqual(obj.kind, "attribute");
    assert.deepStrictEqual(obj.type, [
      {
        name: "CertainNumbers",
        path: ["./", "types.", "CertainNumbers"],
        type: "internal",
      },
    ]);
  });
  await test("private_type_alias_1", () => {
    const obj = getObject("typeIsPrivateTypeAlias1");
    assert.strictEqual(obj.kind, "attribute");
    assert.deepStrictEqual(joinType(obj.type), "{ a: number; b: string; }");
  });
  await test("private_type_alias_2", () => {
    const obj = getObject("typeIsPrivateTypeAlias2");
    assert.strictEqual(obj.kind, "attribute");
    assert.deepStrictEqual(joinType(obj.type), "{ a: number; b: string; }");
  });
});
