import initWasm, {
  decode_words as wasmDecodeWords,
  encode_text as wasmEncodeText,
  module_version as wasmModuleVersion,
} from "../pkg/zpe_wasm_codec.js";

let initPromise;

async function resolveInitArg() {
  if (typeof process !== "undefined" && process.versions?.node) {
    const { readFile } = await import("node:fs/promises");
    const wasmUrl = new URL("../pkg/zpe_wasm_codec_bg.wasm", import.meta.url);
    return readFile(wasmUrl);
  }
  return undefined;
}

async function ensureInit() {
  if (!initPromise) {
    initPromise = (async () => {
      const initArg = await resolveInitArg();
      if (initArg === undefined) {
        await initWasm();
      } else {
        await initWasm({ module_or_path: initArg });
      }
    })();
  }
  await initPromise;
}

function normalizeIds(ids) {
  if (!Array.isArray(ids) && !(ids instanceof Uint32Array)) {
    throw new TypeError("ids must be an array or Uint32Array");
  }

  const out = new Uint32Array(ids.length);
  for (let i = 0; i < ids.length; i += 1) {
    const value = Number(ids[i]);
    if (!Number.isInteger(value) || value < 0 || value > 0xFFFFF) {
      throw new RangeError(`ids[${i}] must be an integer in [0, 1048575]`);
    }
    out[i] = value;
  }
  return out;
}

function buildTokenizer() {
  return {
    version: wasmModuleVersion(),
    encode(text) {
      if (typeof text !== "string") {
        throw new TypeError("text must be a string");
      }
      return Array.from(wasmEncodeText(text));
    },
    decode(ids) {
      const normalized = normalizeIds(ids);
      return wasmDecodeWords(normalized);
    },
  };
}

export async function initTokenizer() {
  await ensureInit();
  return buildTokenizer();
}

export async function encode(text) {
  const tokenizer = await initTokenizer();
  return tokenizer.encode(text);
}

export async function decode(ids) {
  const tokenizer = await initTokenizer();
  return tokenizer.decode(ids);
}
