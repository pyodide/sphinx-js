import { writeFile } from "fs/promises";
import { ExitError, run } from "./cli.ts";

async function main() {
  const start = Date.now();
  const args = process.argv.slice(2);
  let app, result;
  try {
    [app, result] = await run(args);
  } catch (e) {
    if (e instanceof ExitError) {
      return e.code;
    }
    throw e;
  }
  const space = app.options.getValue("pretty") ? "\t" : "";
  const res = JSON.stringify([result, app.extraData], null, space);
  const json = app.options.getValue("json");
  await writeFile(json, res);
  app.logger.info(`JSON written to ${json}`);
  app.logger.verbose(`JSON rendering took ${Date.now() - start}ms`);
  return 0;
}

process.exit(await main());
