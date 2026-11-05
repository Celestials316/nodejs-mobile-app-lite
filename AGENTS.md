# Private Android App runtime

This repository is `Celestials316/nodejs-mobile-app-lite` (account 2).
The `recipe-v27` branch builds only Android Node.js 27.0.0-alpha lite for the
user's App. Do not add Node 26, iOS or full build jobs to this branch, do not
modify the `recipe` Node 24 line without an explicit request, and never push
changes to fogtape's repository (account 4) or any account-1 repository.
The private flavor is `danmu-android-lite-h3`.

Edit upstream or fork source in a materialized tree, commit there, then run
`scripts/regenerate-patches.py out`. Never hand-edit patch diffs. Commit the
matching `expected-tree.txt`. Stage explicit paths and preserve attribution.
Keep docs under docs/. Android builds use Linux, NDK r29 (`29.0.14206865`)
and API 24.

Only `.github/workflows/android-lite.yml` is active. Push/PR runs do the
quick checks; manual runs build all three App ABIs, run App/runtime, ICU,
HTTP/3 and native-addon gates, package the SDK, and optionally publish a
private prerelease. `build` is the default; publishing requires an explicit
`build-and-release` dispatch on the branch named in `private-profile.json`.
Publication checks repository identity, uses an `app-lite-v` tag prefix, and
does not overwrite published releases.

Preserve JIT/native WebAssembly, all current danmu ICU data, HTTP/HTTPS/TLS,
HTTP/2, DNS/crypto, compression, workers/child_process, async context,
fs/module loading, VM, Node-API and node::Start. Do not narrow dynamic
exports or reduce these capabilities based only on today's direct imports.
Keep 16 KB LOAD alignment, RELRO/NOW and Android API24 compatibility. APS2 is
supported from API23; RELR would raise the minimum version and is forbidden.

Node 27 is an upstream alpha. Keep OpenSSL 4.1.0 and upstream V8 metadata
visible in test output, and do not describe this SDK as stable or production
ready. The reviewed trims are npm/Corepack, Amaro, Inspector, SQLite/Web
Storage, SEA, V8 object-print helpers, FFI and V8 Temporal. Do not transfer
upstream test status adaptations from the Node 24 branch without reviewing
them against Node 27.

Never put private repository credentials in SDKs, APKs, source or logs.
Use only the account-2 credential for this repository. Download assets in the
authenticated build environment, not from an App with an embedded token.
Keep the App's existing Node 26 input until this SDK and the matching JNI
build pass its device/startup/core checks.
