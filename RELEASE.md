# Version 1.21.0

## Major Features and Improvements

*   N/A

## Bug Fixes and Other Changes

*   Added support for Python 3.12 and Python 3.13, and dropped support for Python 3.9.
*   Depends on `tensorflow>=2.21,<2.22`.
*   Depends on `protobuf>=6.0.0,<7.0.0`.
*   Removed `numpy<2` restriction and required `pandas>=2.0` to support NumPy 2.x.
*   Bumped the minimum bazel version required to build `tfx_bsl` to 7.7.0.
*   Resolved macOS CI hang/crash by upgrading to NumPy 2.0 and Pandas 2.x.
*   Refactored `example_coder_test.py` to use lazy evaluation for `RecordBatch` objects.
*   Added `-undefined dynamic_lookup` to macOS linkopts to resolve linker errors.

## Breaking Changes

*   N/A

## Deprecations

*   N/A
