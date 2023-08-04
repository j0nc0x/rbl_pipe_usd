cmake_minimum_required(VERSION 2.8)

include(RezBuild)

file(GLOB_RECURSE py_files "lib/python/*.py")
rez_install_files(
    ${py_files}
    DESTINATION rbl_pipe_usd
)

file(GLOB_RECURSE bin_files "bin/*")
rez_install_files(
    ${bin_files}
    DESTINATION rbl_pipe_usd
    EXECUTABLE
)
