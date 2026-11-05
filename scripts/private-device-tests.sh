#!/usr/bin/env bash
# Keep the actual test verdict authoritative under one emulator session.
# Node 27 is an alpha port. Upstream Node24 test status adaptations are not
# carried into this branch, so gate the App contract and the runtime features
# danmu_api actually uses instead of running an unadapted curated suite.
set -euo pipefail
cd source
exec > >(tee private-app-tests.log) 2>&1
adb wait-for-device
./tools/mobile-test/android/prepare-android-test.sh
PROXY="$PWD/out/android.release/node"
"$PROXY" ./test/private-app/runtime-smoke.cjs
"$PROXY" ./test/private-app/h3-smoke.mjs
./tools/mobile-test/addon/run-android-addon.sh "$PWD/crcnative.node"
