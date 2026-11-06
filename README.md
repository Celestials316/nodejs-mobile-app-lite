# Private Android Node.js 27 App lite

Private runtime recipe in `Celestials316/nodejs-mobile-app-lite` (account 2)
for the owner's Android `danmu_api` App. The `recipe-v27` branch builds
**Node.js 27.0.0-alpha.0.0.0 lite for Android only**, for arm64-v8a,
armeabi-v7a and x86_64. The existing `recipe` branch remains the Node 24 line.
This branch does not build iOS or full SDKs.

The source is pinned to the official Node 27 alpha tag commit
`fe34c8eae5514797d6dc21a4bdec39c9913d9322`. It bundles upstream OpenSSL
4.1.0 and V8 15.6. The App-specific mobile revision is `27.0.0-0`. This is an
experimental alpha, not a stable Node Current release. The verified tree is
recorded in `expected-tree.txt`.

The lite profile keeps native QUIC/HTTP/3 (enabled by default), the reviewed
danmu ICU data, JIT/native WebAssembly, HTTP/HTTPS/TLS, HTTP/2,
QUIC/HTTP/3 with mandatory ECH, DNS/crypto, zlib/Brotli/zstd,
workers/child processes, async context, filesystem/module loading, VM,
AsyncLocalStorage and Node-API exports. It trims npm/Corepack,
Amaro, Inspector, SQLite/Web Storage, SEA, V8 object-print helpers, FFI and
V8 Temporal. OpenSSL 4 ECH is exposed for mandatory TLS and QUIC client use;
an ECH-configured connection never falls back to plaintext SNI. These choices
match danmu_api and its locked App dependencies rather than a general-purpose
Node distribution.

## Build or release

Open Actions → **Private Android App lite** → **Run workflow** on
`recipe-v27`.

- `build` builds and tests, then retains the SDK as an Actions artifact.
  This is the default manual operation and does not publish a release.
- `build-and-release` runs the same build/test gates, then publishes a
  private prerelease. It must be requested explicitly.
- Leave `release_tag` empty for a unique `app-lite-v27.0.0-0-build.<run>` tag,
  or enter an unused tag beginning `app-lite-v27.0.0-0`.
- Optionally supply additional English release notes. Existing tags and
  published releases are never overwritten.

Push and PR events on `recipe` and `recipe-v27` run quick source/profile
checks. A manual Node 27 build compiles three Android libraries and uses one
API24 emulator session for runtime, ICU/locale, App dependency, HTTP/3 and
native-addon gates. The unadapted upstream curated suite is not used on the
alpha branch.

The package is `nodejs-mobile-android-app-lite-27.0.0-0.zip`, with the
`bin/<abi>/libnode.so` and `include/node/` layout used by the App. It includes
`BUILD-INFO.json`, LICENSE and a separate `SHA256SUMS` file. Temporary ABI
artifacts/logs expire after one day; the tested SDK artifact expires after
seven days. Private release assets remain available with their release.
Download it with authenticated build tooling; never ship a GitHub token
inside the App. Rebuild JNI against this package's headers before switching.

See [private profile and validation](docs/PRIVATE-ANDROID-LITE.md),
[Node 27 alpha notes](docs/UPSTREAM-27.md) and
[release instructions](docs/RELEASING.md). The App still pins Node 26 until
its JNI and startup/runtime checks pass against this SDK.
