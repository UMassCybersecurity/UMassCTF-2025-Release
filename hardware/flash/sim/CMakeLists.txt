cmake_minimum_required(VERSION 3.25)

project(led-blink)

file(GLOB CSources ./src/*.c)
add_executable(ctfavrsim ${CSources})
target_include_directories(ctfavrsim PUBLIC include)

# add simavr
target_include_directories(ctfavrsim PUBLIC lib/simavr/include/simavr)
find_library(SIMAVR_DIR simavr lib/simavr/lib)
target_link_libraries(ctfavrsim ${SIMAVR_DIR})
configure_file(${SIMAVR_DIR} ${CMAKE_CURRENT_BINARY_DIR}/libsimavr.so.1 COPYONLY)