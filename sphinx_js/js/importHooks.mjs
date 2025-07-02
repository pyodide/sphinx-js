async function tryResolve(specifier, context, nextResolve) {
  try {
    return await nextResolve(specifier, context);
  } catch (e) {
    if (e.code !== "ERR_MODULE_NOT_FOUND") {
      // Unusual error let it propagate
      throw e;
    }
  }
}

// An import hook to pick up packages in the node_modules that typedoc is
// installed into
export async function resolve(specifier, context, nextResolve) {
  // Take an `import` or `require` specifier and resolve it to a URL.
  const origURL = context.parentURL;
  const fallbackURL = `file:${process.env["TYPEDOC_NODE_MODULES"]}/`;
  for (const parentURL of [origURL, fallbackURL]) {
    context.parentURL = parentURL;
    const res = await tryResolve(specifier, context, nextResolve);
    context.parentURL = origURL;
    if (res) {
      return res;
    }
  }
  // If we get here, this will throw an error.
  return nextResolve(specifier, context);
}
