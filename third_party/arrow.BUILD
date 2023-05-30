# Rules here may need to change if arrow source tree changes drastically
# (e.g. new/renamed dirs).

# LINT.IfChange(arrow_gen_version)
genrule(
    name = "config_h",
    srcs = ["cpp/src/arrow/util/config.h.cmake"],
    outs = ["cpp/src/arrow/util/config.h"],
    cmd = ("sed " +
           "-e 's/@ARROW_VERSION_MAJOR@/6/g' " +
           "-e 's/@ARROW_VERSION_MINOR@/0/g' " +
           "-e 's/@ARROW_VERSION_PATCH@/1/g' " +
           "-e 's/cmakedefine/define/g' " +
           "$< >$@"),
)
# LINT.ThenChange(../WORKSPACE:arrow_archive_version)

cc_library(
    name = "config",
    hdrs = ["cpp/src/arrow/util/config.h"],
    includes = ["."],
    visibility = ["//visibility:private"],
)

# These are originally generated by flatbuffers. We use them instead of
# re-generating from fbs files under "format/" and "cpp/src/arrow/ipc/".
fbs_headers = [
    "cpp/src/generated/feather_generated.h",
    "cpp/src/generated/File_generated.h",
    "cpp/src/generated/Message_generated.h",
    "cpp/src/generated/Schema_generated.h",
    "cpp/src/generated/SparseTensor_generated.h",
    "cpp/src/generated/Tensor_generated.h",
]

cc_library(
    name = "arrow",
    srcs = glob(
        [
            "cpp/src/arrow/*.cc",
            "cpp/src/arrow/c/*.cc",
            "cpp/src/arrow/compute/**/*.cc",
            "cpp/src/arrow/array/**/*.cc",
            "cpp/src/arrow/util/**/*.cc",
            "cpp/src/arrow/util/**/*.h",
            "cpp/src/arrow/vendored/**/*.cpp",
            "cpp/src/arrow/vendored/**/*.hpp",
            "cpp/src/arrow/vendored/**/*.cc",
            "cpp/src/arrow/vendored/**/*.c",
            "cpp/src/arrow/vendored/**/*.h",
            "cpp/src/arrow/io/*.h",
            "cpp/src/arrow/io/*.cc",
            "cpp/src/arrow/tensor/*.cc",
            "cpp/src/arrow/ipc/*.h",
            "cpp/src/arrow/ipc/*.cc",
        ],
        exclude = [
            # Excluding files which we don't depend on, but needs
            # additional dependencies like boost, snappy etc.
            "cpp/src/arrow/util/bpacking_avx2.*",
            "cpp/src/arrow/util/bpacking_avx512.*",
            "cpp/src/arrow/util/bpacking_neon*",
            "cpp/src/arrow/util/bpacking_simd*",
            "cpp/src/arrow/util/compression_brotli*",
            "cpp/src/arrow/util/compression_bz2*",
            "cpp/src/arrow/util/compression_lz4*",
            "cpp/src/arrow/util/compression_z*",
            "cpp/src/arrow/util/compression_snappy*",
            "cpp/src/arrow/**/*test*",
            "cpp/src/arrow/**/*benchmark*.cc",
            "cpp/src/arrow/**/*hdfs*.cc",
            "cpp/src/arrow/**/*hdfs*.h",
            "cpp/src/arrow/ipc/json*.cc",
            "cpp/src/arrow/ipc/generate*.cc",
            "cpp/src/arrow/ipc/stream-to-file.cc",
            "cpp/src/arrow/ipc/file-to-stream.cc",
            "cpp/src/arrow/vendored/xxhash/**",
            "cpp/src/arrow/vendored/datetime/**",
        ],
    ),
    hdrs = glob([
        "cpp/src/arrow/*.h",
        "cpp/src/arrow/array/*.h",
        "cpp/src/arrow/c/*.h",
        "cpp/src/arrow/compute/**/*.h",
        "cpp/src/arrow/tensor/*.h",
        "cpp/src/arrow/util/**/*.h",
    ]) + fbs_headers,
    defines = ["ARROW_STATIC"],
    includes = [
        "cpp/src",
        "cpp/thirdparty/flatbuffers/include",
    ],
    visibility = ["@//:__subpackages__"],
    deps = [
        ":xxhash",
        ":datetime",
        # See arrow.patch.
        "@com_google_absl//absl/numeric:int128",
        ":flatbuffers",
        ":config",
    ],
)

cc_library(
    name = "xxhash",
    srcs = [],
    hdrs = [
        "cpp/src/arrow/vendored/xxhash/xxhash.c",
        "cpp/src/arrow/vendored/xxhash/xxhash.h",
    ],
    copts = ["-Wno-implicit-fallthrough"],
    includes = ["."],
    visibility = ["//visibility:private"],
)

config_setting(
    name = "windows",
    constraint_values = [
        "@platforms//os:windows",
    ],
)

cc_library(
    name = "datetime",
    srcs = [
        "cpp/src/arrow/vendored/datetime/tz.cpp",
    ],
    hdrs = [
        "cpp/src/arrow/vendored/datetime/date.h",
        "cpp/src/arrow/vendored/datetime/ios.h",
        "cpp/src/arrow/vendored/datetime/tz.h",
        "cpp/src/arrow/vendored/datetime/tz_private.h",
        "cpp/src/arrow/vendored/datetime/visibility.h",
    ],
    includes = ["."],
    linkopts = select({
        ":windows": [
            "ole32.lib",  # for CoTaskMemFree
            "shell32.lib",  # for SHGetKnownFolderPath
        ],
        "//conditions:default": [
        ],
    }),
    visibility = ["//visibility:private"],
)

cc_library(
    name = "flatbuffers",
    srcs = [],
    hdrs = [
        "cpp/thirdparty/flatbuffers/include/flatbuffers/base.h",
        "cpp/thirdparty/flatbuffers/include/flatbuffers/flatbuffers.h",
        "cpp/thirdparty/flatbuffers/include/flatbuffers/stl_emulation.h",
    ],
    copts = ["-Wno-implicit-fallthrough"],
    includes = ["."],
    visibility = ["//visibility:private"],
)
