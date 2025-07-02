/** Declare some extra stuff we monkeypatch on to typedoc */
declare module "typedoc" {
  export interface TypeDocOptionMap {
    sphinxJsConfig: string;
  }
  export interface Application {
    extraData: {
      [key: string]: any;
    };
  }
}
