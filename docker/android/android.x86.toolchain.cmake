set(CMAKE_SYSTEM_NAME Android)
set(CMAKE_SYSTEM_VERSION 17) # API level

set(CMAKE_ANDROID_ARCH x86)
set(CMAKE_ANDROID_ARCH_ABI x86)

set(CMAKE_ANDROID_STL_TYPE c++_static)
# set(CMAKE_ANDROID_STL_TYPE c++_shared)

set(ANDROID_STL_PREFIX llvm-libc++)

set(CMAKE_ANDROID_STANDALONE_TOOLCHAIN /tmp/android-toolchain)

set(ANDROID_NDK /temp/docker/android/android-ndk-r16-beta1-canary)

set(CMAKE_CXX_STANDARD_INCLUDE_DIRECTORIES
"/tmp/android-toolchain/lib64/clang/5.0/include"
"${ANDROID_NDK}/sources/cxx-stl/${ANDROID_STL_PREFIX}/include"
"${ANDROID_NDK}/sources/android/support/include"
"${ANDROID_NDK}/sources/cxx-stl/${ANDROID_STL_PREFIX}abi/include")
