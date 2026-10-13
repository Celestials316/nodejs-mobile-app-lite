# Private Android App lite 24.22.0-1 with HTTP/3

This SDK is built exclusively for the owner's Android danmu_api App.
It is a Node.js 24.22.0 LTS proposal snapshot pinned to
`a5d0eb95dd03b90986ad1a7c0cd3f2de1a0f383c`; the final official release may differ.

- Add native QUIC/HTTP/3 and make node:quic available by default. Existing
  fetch and node-fetch behavior is preserved; H3 uses its explicit API.
- Keep the complete ICU API with the reviewed danmu data profile, all web
  encodings including GBK/Big5, Chinese collation and Unicode normalization.
- Preserve JIT/native WebAssembly, HTTP/HTTPS/TLS/HTTP2, crypto, DNS,
  compression, workers, external processes, filesystem/module loading and
  Node-API exports.
- Omit the unused iOS polywasm fallback. Use API23-compatible APS2 relocation
  packing and ABI-preserving SDK stripping; retain the API24 floor, 16 KB
  segment alignment, RELRO/NOW and GNU build IDs.
- Keep the established lite omissions: Amaro, Inspector, SQLite/Web Storage,
  SEA and native V8 object-print helpers. ECH is not included.
- Build only Android arm64-v8a, armeabi-v7a and x86_64. Publish only after
  the API24 App dependency, HTTP/3, TLS, Worker, compression, native-addon
  and curated device regression gates pass. No physical-device validation
  is claimed.

Verify the archive with SHA256SUMS. BUILD-INFO.json records the source tree,
recipe commit, run and per-ABI binary checksums. Rebuild the App JNI bridge
against this SDK's headers before integration. Private assets require an
authenticated build download; do not embed repository credentials in an APK.
