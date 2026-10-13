# Private Android App runtime

This repository belongs to `lilixu3` (account 1) and must remain private.
It builds only Android Node.js 24.22 lite for the user's App. Do not add
Node 26, iOS or full build jobs, and do not push changes to fogtape's public
repository. The private flavor is `danmu-android-lite-h3`.

Edit upstream or fork source in a materialized tree, commit there, then run
`scripts/regenerate-patches.py out`. Never hand-edit patch diffs. Commit the
matching `expected-tree.txt`. Stage explicit paths and preserve attribution.
Keep docs under docs/. Android builds use Linux, NDK r27d and API 24.

Only `.github/workflows/android-lite.yml` is active. Push/PR runs do the
quick checks; manual runs build all three App ABIs, run App/H3/curated and
native-addon gates, package the SDK, and optionally publish a private
prerelease. Publication requires private visibility at preflight and at
upload, uses a separate `app-lite-v` tag prefix, and does not overwrite
published releases. The user authorized this simpler private workflow;
there is no Cut-release/review-PR prerequisite.

Preserve JIT/native WebAssembly, all current danmu ICU data, HTTP/HTTPS/TLS,
HTTP/2, DNS/crypto, compression, workers/child_process, async context,
fs/module loading, Node-API and node::Start. Do not narrow dynamic exports
or reduce these capabilities based only on today's direct imports. Keep
16 KB LOAD alignment, RELRO/NOW and Android API24 compatibility. APS2 is
supported from API23; RELR would raise the minimum version and is forbidden.

Never put private repository credentials in SDKs, APKs, source or logs.
Download private assets in the authenticated build environment, not from
an App with an embedded GitHub token. Keep the existing public App input
until the private SDK and matching JNI build are validated.
