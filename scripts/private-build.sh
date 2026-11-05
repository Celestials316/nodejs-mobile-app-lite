#!/usr/bin/env bash
set -euo pipefail
NDK=${1:?NDK path required}
ARCH=${2:?arm, arm64 or x86_64 required}
case "$ARCH" in arm|arm64|x86_64) ;; *) exit 2 ;; esac
API=$(python3 -c 'import json; print(json.load(open("private-profile.json"))["android_api"])')
cd source
NODEJS_MOBILE_FLAVOR=lite ./tools/android_build.sh "$NDK" "$API" "$ARCH"
case "$ARCH" in arm) ABI=armeabi-v7a ;; arm64) ABI=arm64-v8a ;; *) ABI=x86_64 ;; esac
TOOLS="$NDK/toolchains/llvm/prebuilt/linux-x86_64/bin"
LIB="out_android/$ABI/libnode.so"
"$TOOLS/llvm-readelf" -d "$LIB" > "$RUNNER_TEMP/dynamic-$ABI.txt"
"$TOOLS/llvm-readelf" -lW "$LIB" > "$RUNNER_TEMP/segments-$ABI.txt"
"$TOOLS/llvm-nm" -D --format=posix "$LIB" > "$RUNNER_TEMP/symbols-$ABI.txt"
grep -q '_ZN4node5StartEiPPc ' "$RUNNER_TEMP/symbols-$ABI.txt"
grep -q '^napi_create_function ' "$RUNNER_TEMP/symbols-$ABI.txt"
grep -Eq 'ANDROID_REL|ANDROID_RELA' "$RUNNER_TEMP/dynamic-$ABI.txt"
python3 ../scripts/private-package.py validate-elf "$LIB" --readelf "$TOOLS/llvm-readelf"
mkdir -p ../payload/bin/"$ABI"
cp "$LIB" ../payload/bin/"$ABI"/libnode.so
mkdir -p ../payload/include
cp -R out_android/libnode/include/node ../payload/include/node
cp LICENSE ../payload/LICENSE
