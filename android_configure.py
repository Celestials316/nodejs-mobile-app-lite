import platform
import sys
import os
import shutil

if platform.system() != "Linux" and platform.system() != "Darwin":
    print("android-configure is currently only supported on Linux and Darwin.")
    sys.exit(1)

if len(sys.argv) != 4:
    print("Usage: ./android-configure <path to the Android NDK> <Android SDK version> <target architecture>")
    sys.exit(1)

if not os.path.exists(sys.argv[1]) or not os.listdir(sys.argv[1]):
    print("\033[91mError: \033[0m" + "Invalid path to the Android NDK")
    sys.exit(1)

if int(sys.argv[2]) < 24:
    print("\033[91mError: \033[0m" + "Android SDK version must be at least 24 (Android 7.0)")
    sys.exit(1)

android_ndk_path = sys.argv[1]
android_sdk_version = sys.argv[2]
arch = sys.argv[3]

if arch == "arm":
    DEST_CPU = "arm"
    TOOLCHAIN_PREFIX = "armv7a-linux-androideabi"
elif arch in ("aarch64", "arm64"):
    DEST_CPU = "arm64"
    TOOLCHAIN_PREFIX = "aarch64-linux-android"
    arch = "arm64"
elif arch == "x86":
    DEST_CPU = "ia32"
    TOOLCHAIN_PREFIX = "i686-linux-android"
elif arch == "x86_64":
    DEST_CPU = "x64"
    TOOLCHAIN_PREFIX = "x86_64-linux-android"
    arch = "x64"
else:
    print("\033[91mError: \033[0m" + "Invalid target architecture, must be one of: arm, arm64, aarch64, x86, x86_64")
    sys.exit(1)

print("\033[92mInfo: \033[0m" + "Configuring for " + DEST_CPU + "...")

if platform.system() == "Darwin":
    host_os = "mac"
    toolchain_path = android_ndk_path + "/toolchains/llvm/prebuilt/darwin-x86_64"

elif platform.system() == "Linux":
    host_os = "linux"
    toolchain_path = android_ndk_path + "/toolchains/llvm/prebuilt/linux-x86_64"

os.environ['PATH'] += os.pathsep + toolchain_path + "/bin"
os.environ['CC'] = toolchain_path + "/bin/" + TOOLCHAIN_PREFIX + android_sdk_version + "-" +  "clang"
os.environ['CXX'] = toolchain_path + "/bin/" + TOOLCHAIN_PREFIX + android_sdk_version + "-" + "clang++"
# nodejs-mobile patch: add host CC and CXX
os.environ['CC_host'] = os.popen('command -v clang').read().strip()
os.environ['CXX_host'] = os.popen('command -v clang++').read().strip()

# nodejs-mobile patch: route every compile through sccache, but only when the
# caller opts in (CI sets NODEJS_MOBILE_SCCACHE=1 next to the
# mozilla-actions/sccache-action setup). Opt-in rather than "wrap when
# installed": a local build must not silently change behaviour because a
# developer happens to have sccache on PATH. This lives here and not in CI env
# because this script overwrites CC/CXX with the NDK toolchain paths above —
# an externally exported CC would not survive to the make invocation.
if os.environ.get("NODEJS_MOBILE_SCCACHE"):
    sccache = shutil.which("sccache")
    if not sccache:
        print("\033[91mError: \033[0m" + "NODEJS_MOBILE_SCCACHE is set but sccache is not on PATH")
        sys.exit(1)
    for _var in ("CC", "CXX", "CC_host", "CXX_host"):
        os.environ[_var] = sccache + " " + os.environ[_var]

GYP_DEFINES = "target_arch=" + arch
GYP_DEFINES += " v8_target_arch=" + arch
GYP_DEFINES += " android_target_arch=" + arch
GYP_DEFINES += " host_os=" + host_os + " OS=android"
GYP_DEFINES += " android_ndk_path=" + android_ndk_path
GYP_DEFINES += " android_ndk_sysroot=" + toolchain_path + "/sysroot"
# Private Android-only App profile. Reject accidental full builds.
flavor = os.environ.get("NODEJS_MOBILE_FLAVOR", "lite").strip().lower()
if flavor != "lite":
    sys.exit("This private recipe only builds the App Android lite profile")
print("Build profile: danmu-android-lite-h3")
intl = "full-icu"
GYP_DEFINES += " node_mobile_icu_profile=danmu-lite.json"
extra_flags = (" --experimental-quic --without-npm --without-corepack"
               " --without-amaro --without-inspector --without-sqlite"
               " --disable-single-executable-application --v8-disable-object-print")
# Preserve the public lite memory model and direct V8-addon ABI.
if arch in ("arm64", "x64"):
    extra_flags += " --experimental-enable-pointer-compression"

os.environ['GYP_DEFINES'] = GYP_DEFINES

if os.path.exists("./configure"):
    sys.exit(os.system("./configure --dest-cpu=" + DEST_CPU + " --dest-os=android --openssl-no-asm --with-intl=" + intl + extra_flags + " --cross-compiling --shared") >> 8)
