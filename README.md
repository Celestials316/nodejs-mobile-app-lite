# Private Android Node.js 24.22 App lite

Private runtime recipe for the owner's Android `danmu_api` App. This
repository builds **Node.js 24.22 lite for Android only**, for arm64-v8a,
armeabi-v7a and x86_64. It does not build Node 26, iOS or full SDKs.

The source is pinned to the Node 24.22 LTS proposal commit
`a5d0eb95dd03b90986ad1a7c0cd3f2de1a0f383c`. The App-specific mobile revision
is `24.22.0-1`. This is an upstream proposal snapshot, not an official Node tag.
The verified tree is recorded in `expected-tree.txt`.

The private profile adds native QUIC/HTTP/3 and makes `node:quic` available
by default. It keeps the reviewed danmu ICU profile, JIT/native WebAssembly,
HTTP/HTTPS/TLS, HTTP/2, DNS/crypto, workers, external-process launching,
compression, filesystem/module loading and Node-API exports. Existing
fetch/node-fetch requests remain on their existing transports; HTTP/3
requires an explicit request path. ECH is not provided by this runtime.

## Build or release

Open Actions → **Private Android 24.22 lite** → **Run workflow** on `recipe`.

- `build`: build and test, then retain the SDK as a private Actions artifact.
- `build-and-release`: the same build/test gates, then publish a private
  GitHub prerelease. This is the default manual operation.
- Leave `release_tag` empty for a unique `app-lite-v24.22.0-1-build.<run>` tag,
  or enter an unused tag beginning `app-lite-v24.22.0-1`.
- Optionally supply additional English release notes. Existing tags and
  published releases are never overwritten.

Push and PR events run quick source/profile checks. There are no scheduled
full/iOS suites, public-repository compiler caches, BrowserStack credentials
or multi-line release controllers. A manual build compiles three Android
libraries and uses one API24 emulator session for the App dependency,
HTTP/3, native-addon and curated regression gates.

The package is `nodejs-mobile-android-app-lite-24.22.0-1.zip`, with the same
`bin/<abi>/libnode.so` and `include/node/` layout used by the App. It includes
`BUILD-INFO.json`, LICENSE and a separate `SHA256SUMS` file.
Download it with authenticated build tooling; never ship a GitHub token
inside the App. Rebuild JNI against this package's headers before switching.

See [private profile and validation](docs/PRIVATE-ANDROID-LITE.md) and
[release instructions](docs/RELEASING.md). Existing public release inputs
are unchanged until consumer integration is explicitly requested.
