# ZPE IMC WASM Package

This package provides an async browser/edge wrapper around the Rust WASM text codec.

## Build

```bash
cd code/wasm
npm run build
```

## Wrapper API

```js
import { initTokenizer, encode, decode } from "./src/index.js";

const tokenizer = await initTokenizer();
const ids = tokenizer.encode("hello");
const text = tokenizer.decode(ids);

const ids2 = await encode("edge-ready");
const text2 = await decode(ids2);
```

The wrapper initializes asynchronously and then exposes stable synchronous `encode` and `decode` methods.

## Local Contract Test

```bash
cd code/wasm
npm run test
```

## npm Publish Flow

```bash
cd code/wasm
npm run build
npm pack --dry-run --json
npm publish --access public
```
