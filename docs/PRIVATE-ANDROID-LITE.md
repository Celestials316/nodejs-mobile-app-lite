# Private Android App profile

## Scope and provenance

The repository is `Celestials316/nodejs-mobile-app-lite` (account 2). The
`recipe-v27` branch builds only Node.js 27.0.0-alpha.0.0.0 Android lite, pinned
to the official alpha tag commit
`fe34c8eae5514797d6dc21a4bdec39c9913d9322`. The independent profile and
`app-lite-v` tags prevent mixing it with Node 24 or fogtape's public SDKs.
Android API24 and the three ABIs used by the App are preserved:
arm64-v8a, armeabi-v7a and x86_64. iOS and full builds are rejected.

Node 27 alpha bundles OpenSSL 4.1.0 and V8 15.6. OpenSSL enables the HTTP/TLS
stack and QUIC. This is experimental upstream code, not a stable Node Current
release; integration decisions must treat it as alpha.

## danmu_api reductions

- Keep the reviewed danmu ICU profile: all Node TextDecoder web encodings,
  selected English/Chinese/Cantonese/Japanese/Korean locale families,
  normalization, IDNA, time zones and segmentation. Source imports are not
  enough to justify removing data used by future source modules.
- Omit npm, Corepack, Amaro, Inspector, SQLite/Web Storage, SEA and native V8
  object-print helpers. The App uses its bundled pure-UniDB path.
- Omit the iOS-only polywasm JS payload and fallback bootstrap. Android keeps
  native V8 WebAssembly and JIT. Do not apply V8 lite/jitless mode or remove
  compiler tiers; these would change App performance and WASM behavior.
- Omit FFI and V8 Temporal with `--without-ffi` and
  `--v8-disable-temporal-support`; danmu_api and its locked App dependencies
  do not use them.
- Keep HTTP/HTTPS/TLS, HTTP/2, HTTP/3, fetch/node-fetch, DNS, crypto,
  zlib/Brotli/zstd, workers/child_process, AsyncLocalStorage/async context,
  filesystem/path/url, VM, module loading and Node-API. These are the
  capabilities exercised by danmu_api or its bundled dependencies.
- Pack dynamic relocations using Android's APS2 format, which works from
  API23. Do not use RELR, which raises the Android floor. Apply packing only
  to the runtime link, not Linux host build tools. Keep 16 KB LOAD alignment,
  RELRO and NOW.
- Strip SDK copies with the established atomic helper and require every
  dynamic symbol to remain unchanged. Do not narrow exports to a guessed
  allow-list: JNI/node::Start and native-addon compatibility matter.

QUIC uses the upstream ngtcp2/nghttp3 implementation. `node:quic` is enabled
by default in this profile, and `--no-experimental-quic` can disable it. H3
does not add ECH.

## Compatibility gates

The manual workflow uses Android NDK r29 and compiles arm/arm64/x86_64. It
verifies each ELF's external dependencies, Node/Node-API entry points, APS2
relocation format, 16 KB page alignment and RELRO/NOW. The API24 emulator
runs:

- Node/OpenSSL/ngtcp2 metadata and the App runtime contract.
- ICU encodings, locale, normalization, IDNA and timezone checks.
- Native WebAssembly, TLS/HTTP/HTTPS/HTTP2, fetch/node-fetch, zlib/Brotli/zstd,
  crypto, AsyncLocalStorage, Workers, child processes and CJS/ESM loading.
- Locked App dependencies: pure UniDB, adapters, OpenCC, pako, Brotli,
  node-fetch and HTTPS proxy agent.
- Real HTTP/3 GET and large POST round trips with certificate validation.
- A real compiled Node-API addon.

The upstream Node 24 curated suite is intentionally not run on this alpha
branch: its test/status adaptations were not carried over. These are SDK
checks, not physical-device or complete App release validation. The App
currently pins Node 26. Rebuild JNI and run the App's device/startup/core
checks before replacing that pinned runtime.
