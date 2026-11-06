# Private Android App lite 27.0.0-0 with HTTP/3

This SDK is built exclusively for the owner's Android danmu_api App from
Node.js 27.0.0-alpha.0.0.0, pinned to
`fe34c8eae5514797d6dc21a4bdec39c9913d9322`. It is an experimental alpha
snapshot, not a stable production runtime.

- Use upstream OpenSSL 4.1.0 and V8 15.6; expose Node, OpenSSL, ngtcp2,
  nghttp3 and mobile versions in the runtime gate.
- Add native QUIC/HTTP/3 and make node:quic available by default. Existing
  fetch and node-fetch behavior is preserved; H3 uses its explicit API.
- Keep the complete ICU API with the reviewed danmu data profile, all web
  encodings including GBK/Big5, Chinese collation and Unicode normalization.
- Preserve JIT/native WebAssembly, HTTP/HTTPS/TLS/HTTP2, crypto, DNS,
  compression, workers, external processes, filesystem/module loading, VM
  and Node-API exports.
- Omit npm/Corepack, the iOS polywasm fallback, Amaro, Inspector,
  SQLite/Web Storage, SEA, V8 object-print helpers, FFI and V8 Temporal.
  ECH is not included.
- Build with Clang 20 host tools from LLVM's official apt repository (Node 27
  requires Clang 19.1+) and the pinned NDK r29 cross compiler.
- Use API23-compatible APS2 relocation packing and ABI-preserving SDK
  stripping; retain the API24 floor, 16 KB segment alignment, RELRO/NOW and
  GNU build IDs.
- Build only Android arm64-v8a, armeabi-v7a and x86_64. Publish only after
  the API24 App dependency, HTTP/3, TLS, Worker, compression and native-addon
  gates pass. The unadapted Node 24 curated suite and physical-device
  validation are not claimed.

Verify the archive with SHA256SUMS. BUILD-INFO.json records the source tree,
recipe commit, run and per-ABI binary checksums. Rebuild the App JNI bridge
against this SDK's headers before integration. Do not embed repository
credentials in an APK.
