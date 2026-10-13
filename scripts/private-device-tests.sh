#!/usr/bin/env bash
# Keep the actual test verdict authoritative under one emulator session.
set -euo pipefail
cd source
exec > >(tee private-app-tests.log) 2>&1
adb wait-for-device
./tools/mobile-test/android/prepare-android-test.sh
PROXY="$PWD/out/android.release/node"
"$PROXY" ./test/private-app/runtime-smoke.cjs
"$PROXY" ./test/private-app/h3-smoke.mjs
./tools/mobile-test/addon/run-android-addon.sh "$PWD/crcnative.node"
COUNT=$(grep -cvE '^[[:space:]]*#|^[[:space:]]*$' tools/mobile-test/curated-device-tests.txt)
[ "$COUNT" -ge 200 ] || { echo 'Curated regression list is incomplete'; exit 1; }
grep -vE '^[[:space:]]*#|^[[:space:]]*$' tools/mobile-test/curated-device-tests.txt | xargs ./tools/test.py -j 1 --flaky-tests=skip --timeout=300 --arch android
./tools/test.py -j 1 --flaky-tests=skip --timeout=300 --arch android parallel/test-quic-h3-request-response parallel/test-quic-h3-post-request parallel/test-quic-h3-concurrent-requests parallel/test-quic-h3-trailing-headers parallel/test-quic-h3-handshake-failure
