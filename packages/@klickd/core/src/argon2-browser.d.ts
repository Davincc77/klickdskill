// Minimal ambient declaration for the optional argon2-browser fallback.
declare module 'argon2-browser' {
  export enum ArgonType {
    Argon2d = 0,
    Argon2i = 1,
    Argon2id = 2,
  }
  export interface Argon2BrowserHashOptions {
    pass: string;
    salt: Uint8Array;
    type?: ArgonType;
    mem?: number;
    time?: number;
    parallelism?: number;
    hashLen?: number;
  }
  export interface Argon2BrowserHashResult {
    hash: Uint8Array;
    hashHex: string;
    encoded: string;
  }
  export function hash(opts: Argon2BrowserHashOptions): Promise<Argon2BrowserHashResult>;
}
