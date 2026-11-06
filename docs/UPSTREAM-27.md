# Node.js 27 alpha upstream notes

## Pin

- Tag: `v27.0.0-alpha.0.0.0`
- Commit: `fe34c8eae5514797d6dc21a4bdec39c9913d9322`
- Node: `27.0.0-alpha.0.0.0`
- V8: `15.6.75.13`
- OpenSSL: `4.1.0`
- Upstream release date: `2026-10-29`

The official Node.js release schedule places Node 27 Current in April 2027;
this alpha is experimental and may change ABI, diagnostics, test status or
dependencies before a stable release. The recipe therefore pins the exact tag
commit and does not follow a moving branch.

## Branch policy

`recipe` remains Node 24. `recipe-v27` is the isolated alpha port. It keeps
the Android-only lite flavor and does not enable iOS, full SDKs, npm,
Corepack or the Node 24 curated test suite. Shared fixes should be reviewed
separately for each line rather than merged blindly.

## Port notes

The Node 27 move required rebasing the mobile patch stack onto the alpha tag.
The test status patch and upstream workflow/document removal patches from
Node 24 were retired: they conflicted with Node 27 and do not contribute to
the App runtime. The test harness patch is retained because the emulator App
uses it. The QUIC default remains behind `OPENSSL_NO_QUIC`; FFI and Temporal
are disabled because danmu_api does not use them.

Node 27's V8 needs a Clang 19.1+ host toolchain for C++20 features that the
runner's default Clang 18 does not implement. CI installs Clang 20 and the
configure wrapper now honors explicit `CC_host`/`CXX_host` values. The arm
target also needs the host toolset linked with `-latomic`; V8 15.6
default-constructs an alias template (`SimdShuffle::ShuffleArray`) in a form
rejected by older compilers, so the patch spells out the existing 128-bit
size; and the 32-bit host standard library lacks the C++17 cache-line constant
used by one V8 layout assertion, so that non-functional assertion is
feature-gated. None of these changes alter libnode behavior or data layout.

The runtime gate checks that `process.versions.mobile` retains the upstream
prerelease metadata before the mobile rebuild suffix. OpenSSL 4.1 and QUIC/
HTTP/3 behavior are validated on the API24 emulator. A successful SDK build
is not a claim that Node 27 is ready for the App: rebuild the JNI bridge and
run the App's startup/core tests before replacing Node 26.
