import {
  Application,
  ArgumentsReader,
  TypeDocReader,
  PackageJsonReader,
  TSConfigReader,
  ProjectReflection,
} from "typedoc";
import { Converter } from "./convertTopLevel.ts";
import { SphinxJsConfig } from "./sphinxJsConfig.ts";
import { fileURLToPath } from "url";
import { redirectPrivateTypes } from "./redirectPrivateAliases.ts";
import { TopLevelIR } from "./ir.ts";

const ExitCodes = {
  Ok: 0,
  OptionError: 1,
  CompileError: 3,
  ValidationError: 4,
  OutputError: 5,
  ExceptionThrown: 6,
  Watching: 7,
};

export class ExitError extends Error {
  code: number;
  constructor(code: number) {
    super();
    this.code = code;
  }
}

async function bootstrapAppTypedoc0_25(args: string[]): Promise<Application> {
  return await Application.bootstrapWithPlugins(
    {
      plugin: [fileURLToPath(import.meta.resolve("./typedocPlugin.ts"))],
    },
    [
      new ArgumentsReader(0, args),
      new TypeDocReader(),
      new PackageJsonReader(),
      new TSConfigReader(),
      new ArgumentsReader(300, args),
    ],
  );
}

async function makeApp(args: string[]): Promise<Application> {
  // Most of this stuff is copied from typedoc/src/lib/cli.ts
  let app = await bootstrapAppTypedoc0_25(args);
  if (app.options.getValue("version")) {
    console.log(app.toString());
    throw new ExitError(ExitCodes.Ok);
  }
  app.extraData = {};
  app.options.getValue("modifierTags").push("@hidetype");
  app.options.getValue("blockTags").push("@destructure");
  return app;
}

async function loadConfig(
  configPath: string | undefined,
): Promise<SphinxJsConfig> {
  if (!configPath) {
    return {};
  }
  const configModule = await import(configPath);
  return configModule.config;
}

async function typedocConvert(app: Application): Promise<ProjectReflection> {
  // Most of this stuff is copied from typedoc/src/lib/cli.ts
  const project = await app.convert();
  if (!project) {
    throw new ExitError(ExitCodes.CompileError);
  }
  const preValidationWarnCount = app.logger.warningCount;
  app.validate(project);
  const hadValidationWarnings =
    app.logger.warningCount !== preValidationWarnCount;
  if (app.logger.hasErrors()) {
    throw new ExitError(ExitCodes.ValidationError);
  }
  if (
    hadValidationWarnings &&
    (app.options.getValue("treatWarningsAsErrors") ||
      app.options.getValue("treatValidationWarningsAsErrors"))
  ) {
    throw new ExitError(ExitCodes.ValidationError);
  }
  return project;
}

export async function run(
  args: string[],
): Promise<[Application, TopLevelIR[]]> {
  let app = await makeApp(args);
  const userConfigPath = app.options.getValue("sphinxJsConfig");
  const config = await loadConfig(userConfigPath);
  app.logger.info(`Loaded user config from ${userConfigPath}`);
  const symbolToType = redirectPrivateTypes(app);
  await config.preConvert?.(app);
  const project = await typedocConvert(app);
  const basePath = app.options.getValue("basePath");
  const converter = new Converter(project, basePath, config, symbolToType);
  converter.computePaths();
  const result = converter.convertAll();
  await config.postConvert?.(app, project, converter.typedocToIRMap);
  return [app, result];
}
