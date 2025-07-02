/**
 * Typedoc plugin which adds --sphinxJsConfig option
 */

// TODO: we don't seem to resolve imports correctly in this file, but it works
// to do a dynamic import. Figure out why.

export async function load(app: any): Promise<void> {
  // @ts-ignore
  const typedoc = await import("typedoc");
  app.options.addDeclaration({
    name: "sphinxJsConfig",
    help: "[typedoc-plugin-sphinx-js]: the sphinx-js config",
    type: typedoc.ParameterType.String,
  });
}
