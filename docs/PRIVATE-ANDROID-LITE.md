# Private Android App profile

## Scope and provenance

Only Node 24.22.0 Android lite is built, using the pinned upstream proposal
and the reviewed mobile patch stack. The independent private profile and
`app-lite-v` release tags prevent mixing it with fogtape's public SDKs.
Android API24 and all three current App ABIs are preserved.

## Safe reductions and optimizations

- Keep the existing danmu ICU profile unchanged: all Node TextDecoder web
  encodings, selected English/Chinese/Cantonese/Japanese/Korean locale
  families, normalization, IDNA, time zones and segmentation. Source imports
  are not enough to justify removing data used by future source modules.
- Keep the established lite omissions: Amaro, Inspector, SQLite/Web Storage,
  SEA and native V8 object-print helpers. The App uses the pure UniDB path.
- Omit the iOS-only polywasm JS payload and fallback bootstrap. Android keeps
  native V8 WebAssembly and JIT. Do not apply V8 lite/jitless mode or remove
  compiler tiers; these would change App performance and WASM behavior.
- Disable npm/Corepack installation. They are not needed by an embedded
  runtime; this does not disable loading npm packages bundled by the App.
  They were not previously shipped in the SDK archive, so this is a build
  simplification rather than a claimed libnode size saving.
- Pack dynamic relocations using Android's APS2 format. Official NDK docs
  support it from API23, below this App's API24 minimum. Do not use RELR, which
  needs a higher Android API. Apply packing only to the runtime link, not
  Linux host build tools. Keep build IDs, 16 KB LOAD alignment, RELRO and NOW.
- Strip SDK copies with the established atomic helper and require every
  dynamic symbol to remain unchanged. Do not narrow exports to a guessed
  allow-list: JNI/node::Start and native-addon compatibility matter.

HTTP/3 adds the upstream ngtcp2/nghttp3 implementation. `node:quic` is enabled
by default in this private build, and `--no-experimental-quic` can disable it.
Existing HTTP fetch behavior is preserved. H3 does not add ECH.

## Compatibility gates

The one manual workflow compiles arm/arm64/x86_64 and verifies each ELF's
external dependencies, Node/Node-API entry points, APS2 relocation format,
16 KB page alignment and RELRO/NOW. The API24 emulator runs:

- Existing 39-encoding, locale, normalization/IDNA and timezone checks.
- Native WebAssembly and App compatibility polyfills.
- TLS certificate validation, HTTP, HTTPS, HTTP/2 and fetch/node-fetch.
- Gzip/deflate/Brotli/zstd, crypto, AsyncLocalStorage, Workers and external
  Android shell process launching; CJS and ESM file loading.
- Locked App dependencies: pure UniDB, adapters, OpenCC, pako, Brotli,
  node-fetch and HTTPS proxy agent.
- Real HTTP/3 GET and large POST round trips with certificate validation,
  plus upstream request/concurrency/trailer/handshake regressions.
- A real compiled Node-API addon and the existing curated device suite.

These are meaningful SDK checks, not physical-device or complete App release
validation. The App currently pins Node 26.11 from the public repository;
this task does not silently change its input. Rebuild JNI and perform the
App's device/startup/core checks before replacing that pinned runtime.
