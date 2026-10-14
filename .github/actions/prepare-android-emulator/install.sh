#!/usr/bin/env bash
set -euo pipefail

: "${ANDROID_HOME:?ANDROID_HOME must identify the runner Android SDK}"
: "${RUNNER_TEMP:?RUNNER_TEMP must identify the runner temporary directory}"
ACTION_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
source "$ACTION_DIR/pin.sh"
SDK_MANAGER="$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager"
ORIGINAL="$SDK_MANAGER.nodejs-mobile-original"
EMULATOR="$ANDROID_HOME/emulator/emulator"
ARCHIVE="$RUNNER_TEMP/emulator-linux_x64-${EMULATOR_BUILD_ID}.zip"
URL="https://dl.google.com/android/repository/emulator-linux_x64-${EMULATOR_BUILD_ID}.zip"
WORK=$(mktemp -d "$RUNNER_TEMP/prepare-emulator.XXXXXX")
trap 'rm -rf "$WORK"' EXIT

[ -x "$SDK_MANAGER" ] || { echo "::error::SDK Manager is missing" >&2; exit 1; }

if [ -e "$ORIGINAL" ]; then
  cmp -s "$ACTION_DIR/sdkmanager-wrapper.sh" "$SDK_MANAGER" || {
    echo "::error::SDK Manager was changed after emulator preparation" >&2
    exit 1
  }
fi

valid_archive() {
  [ -f "$1" ] && [ "$(wc -c < "$1" | tr -d '[:space:]')" = "$EMULATOR_SIZE" ] &&
    printf '%s  %s\n' "$EMULATOR_SHA256" "$1" | sha256sum --check --status
}

# A truncated or poisoned cache is never installed. Downloads have bounded
# transport retries plus size/digest validation before extraction.
if ! valid_archive "$ARCHIVE"; then
  for attempt in 1 2 3; do
    echo "Downloading Android Emulator $EMULATOR_VERSION ($EMULATOR_BUILD_ID), attempt $attempt"
    if curl --fail --location --silent --show-error --retry 2 --retry-all-errors \
         --connect-timeout 20 --max-time 180 "$URL" -o "$WORK/emulator.zip" &&
       valid_archive "$WORK/emulator.zip"; then
      mv "$WORK/emulator.zip" "$ARCHIVE"
      break
    fi
    echo "::warning::Emulator archive transfer or size/checksum verification failed"
    if [ "$attempt" -lt 3 ]; then sleep 5; fi
  done
fi
valid_archive "$ARCHIVE" || { echo "::error::No verified emulator archive available" >&2; exit 1; }
unzip -tq "$ARCHIVE" >/dev/null
unzip -q "$ARCHIVE" -d "$WORK"
grep -Fx "Pkg.Revision=$EMULATOR_VERSION" "$WORK/emulator/source.properties"
grep -Fx "Pkg.BuildId=$EMULATOR_BUILD_ID" "$WORK/emulator/source.properties"
VERSION=$("$WORK/emulator/emulator" -version 2>&1) || {
  echo "::error::The verified Android Emulator cannot run: $VERSION" >&2
  exit 1
}
[[ "$VERSION" == *"Android emulator version $EMULATOR_VERSION."* &&
   "$VERSION" == *"build_id $EMULATOR_BUILD_ID"* ]] || {
  echo "::error::The emulator binary does not match its reviewed version/build" >&2
  exit 1
}
printf '%s\n' "$VERSION"
if [ -e "$ANDROID_HOME/emulator" ]; then
  mv "$ANDROID_HOME/emulator" "$WORK/previous-emulator"
fi
mv "$WORK/emulator" "$ANDROID_HOME/emulator"

# Register the pinned emulator as an installed SDK package. The Google
# archive carries only legacy source.properties metadata, and the SDK tools
# never treat such a directory as an installed package: `avdmanager create
# avd` then fails with Error: "emulator" package must be installed! (run
# 38491039799 hit exactly this on the API 24 device gate — nothing else
# registers an emulator there, because the API 24 system image declares no
# emulator dependency while API 30+ images do, which is how the recipe's own
# emulator jobs stayed green). Write the same single-package package.xml
# sdkmanager writes for an installed emulator, with the pin's revision, so
# the SDK sees this exact pinned build at the canonical `emulator/` path.
[ "$EMULATOR_REVISION_MAJOR.$EMULATOR_REVISION_MINOR.$EMULATOR_REVISION_MICRO" = "$EMULATOR_VERSION" ] || {
  echo "::error::pin.sh revision variables disagree with EMULATOR_VERSION" >&2
  exit 1
}
sed -e "s/@MAJOR@/$EMULATOR_REVISION_MAJOR/" \
    -e "s/@MINOR@/$EMULATOR_REVISION_MINOR/" \
    -e "s/@MICRO@/$EMULATOR_REVISION_MICRO/" \
    "$ACTION_DIR/emulator-package.xml.in" > "$ANDROID_HOME/emulator/package.xml"

# The emulator action prepends this exact SDK bin directory to PATH, so a
# separate PATH shim would be shadowed. Keep the original beside its wrapper;
# its APP_HOME still resolves to the same command-line tools installation.
if [ ! -e "$ORIGINAL" ]; then mv "$SDK_MANAGER" "$ORIGINAL"; fi
cp "$ACTION_DIR/sdkmanager-wrapper.sh" "$SDK_MANAGER"
chmod +x "$SDK_MANAGER"
