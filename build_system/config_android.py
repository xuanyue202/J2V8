import constants as c
from build_structures import PlatformConfig
from docker_build import DockerBuildSystem, DockerBuildStep
import shared_build_steps as u
import build_utils as b
import cmake_utils as cmu

android_config = PlatformConfig(c.target_android, [c.arch_x86, c.arch_arm])

android_config.set_cross_configs({
    "docker": DockerBuildStep(
        platform=c.target_android,
        host_cwd="$CWD/docker",
        build_cwd="/j2v8"
    )
})

android_config.set_cross_compilers({
    "docker": DockerBuildSystem
})

android_config.set_file_abis({
    c.arch_arm: "armeabi-v7a",
    c.arch_x86: "x86"
})

#-----------------------------------------------------------------------
def build_node_js(config):
    return [
        "cd ./node",

        "export ANDROID_NDK_NAME=android-ndk-r16-beta1",
        "export ANDROID_NDK_HOME=~/$ANDROID_NDK_NAME/",
        "export TOOLCHAIN=/tmp/android-toolchain",

        "export CC_host=gcc",
        "export CXX_host=g++",
        "export AR_host=ar",
        "export LINK_host=g++",

        "export PATH=/tmp/android-toolchain/bin:$PATH",

        "export AR=/tmp/android-toolchain/bin/i686-linux-android-ar",
        "export CC=/tmp/android-toolchain/bin/clang",
        "export CXX=/tmp/android-toolchain/bin/clang++",
        "export LINK=/tmp/android-toolchain/bin/clang++",

        # NOTE: DHAVE_PTHREAD_COND_TIMEDWAIT_MONOTONIC only needed Pre Android platform 21
        "export CFLAGS=\"-fPIC -DHAVE_PTHREAD_COND_TIMEDWAIT_MONOTONIC\"",
        "export CXXFLAGS=\"-fPIC -DHAVE_PTHREAD_COND_TIMEDWAIT_MONOTONIC\"",
        """ \
        export GYP_DEFINES="\
            target_arch=ia32 \
            v8_target_arch=ia32 \
            android_target_arch=ia32 \
            host_os=linux OS=android" \
        """,
        """ \
            ./configure             \
            --dest-cpu=ia32        \
            --dest-os=$PLATFORM     \
            --without-snapshot      \
            --without-inspector     \
            --without-intl          \
            --openssl-no-asm        \
            --enable-static         \
        """,
        # "make clean",
        "make -j4 BUILDTYPE=Release",
    ]

android_config.build_step(c.build_node_js, build_node_js)
# def build_node_js(config):
#     return [
#         """android-gcc-toolchain $ARCH --api 17 --stl libc++ --host gcc-lpthread -C \
#             sh -c \"                \\
#             cd ./node;              \\
#             ./configure             \\
#             --without-intl          \\
#             --without-inspector     \\
#             --dest-cpu=$ARCH        \\
#             --dest-os=$PLATFORM     \\
#             --without-snapshot      \\
#             --enable-static &&      \\
#             CFLAGS=-fPIC CXXFLAGS=-fPIC make -j4\"  \
#             """,
#     ]

# android_config.build_step(c.build_node_js, build_node_js)
#-----------------------------------------------------------------------
def build_j2v8_cmake(config):
    cmake_vars = cmu.setAllVars(config)
    cmake_toolchain = cmu.setToolchain("$BUILD_CWD/docker/android/android.$ARCH.toolchain.cmake")
    # cmake_toolchain = cmu.setToolchain("/temp/docker/android/android-ndk-r16-beta1-canary/build/cmake/android.toolchain.cmake")

    return \
        u.mkdir(u.cmake_out_dir) + \
        ["cd " + u.cmake_out_dir] + \
        u.rm("CMakeCache.txt CMakeFiles/") + [
        """cmake \
            -DCMAKE_BUILD_TYPE=Release \
            %(cmake_vars)s \
            %(cmake_toolchain)s \
            ../../ \
        """
        % locals()
    ]

android_config.build_step(c.build_j2v8_cmake, build_j2v8_cmake)
#-----------------------------------------------------------------------
android_config.build_step(c.build_j2v8_jni, u.build_j2v8_jni)
#-----------------------------------------------------------------------
def build_j2v8_cpp(config):
    return [
        "cd " + u.cmake_out_dir,
        "make clean",
        "VERBOSE=1 make -j4",
    ]

android_config.build_step(c.build_j2v8_cpp, build_j2v8_cpp)
#-----------------------------------------------------------------------
def build_j2v8_java(config):
    return \
        u.clearNativeLibs(config) + \
        u.copyNativeLibs(config) + \
        u.setVersionEnv(config) + \
        u.gradle("clean assembleRelease")

android_config.build_step(c.build_j2v8_java, build_j2v8_java)
#-----------------------------------------------------------------------
def build_j2v8_test(config):
    # if you are running this step without cross-compiling, it is assumed that a proper target Android device
    # or emulator is running that can execute the tests (platform + architecture must be compatible to the the build settings)

    # add the extra step arguments to the command if we got some
    step_args = getattr(config, "args", None)
    step_args = " " + step_args if step_args else ""

    test_cmds = \
        u.setVersionEnv(config) + \
        u.gradle("spoon" + step_args)

    # we are running a build directly on the host shell
    if (not config.cross_agent):
        # just run the tests on the host directly
        return test_cmds

    # we are cross-compiling, run both the emulator and gradle test-runner in parallel
    else:
        b.apply_file_template(
            "./docker/android/supervisord.template.conf",
            "./docker/android/supervisord.conf",
            lambda x: x.replace("$TEST_CMDS", " && ".join(test_cmds))
        )

        emu_arch = "-arm" if config.arch == c.arch_arm else "64-x86"

        b.apply_file_template(
            "./docker/android/start-emulator.template.sh",
            "./docker/android/start-emulator.sh",
            lambda x: x
                .replace("$IMG_ARCH", config.file_abi)
                .replace("$EMU_ARCH", emu_arch)
        )

        return ["/usr/bin/supervisord -c /j2v8/docker/android/supervisord.conf"]

android_config.build_step(c.build_j2v8_test, build_j2v8_test)
#-----------------------------------------------------------------------
