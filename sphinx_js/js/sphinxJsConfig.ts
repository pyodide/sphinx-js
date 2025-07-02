import {
  Application,
  DeclarationReflection,
  ParameterReflection,
  ProjectReflection,
} from "typedoc";
import { TopLevel } from "./ir.ts";

export type SphinxJsConfig = {
  shouldDestructureArg?: (param: ParameterReflection) => boolean;
  preConvert?: (app: Application) => Promise<void>;
  postConvert?: (
    app: Application,
    project: ProjectReflection,
    typedocToIRMap: ReadonlyMap<DeclarationReflection, TopLevel>,
  ) => Promise<void>;
};
