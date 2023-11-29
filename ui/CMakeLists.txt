cmake_minimum_required(VERSION 3.10) # Specify the minimum version of CMake
set(CMAKE_CXX_STANDARD 11)  # or a later standard like 14, 17, 20

project(MyProject) # Name of your project

# Find the SDL2 library
find_package(SDL2 REQUIRED)
find_package(PkgConfig REQUIRED)
pkg_search_module(SDL2TTF REQUIRED SDL2_ttf)

include(FetchContent)

# Find and configure the json library
add_subdirectory(json)

# Add executable target with source files
add_executable(exec main.cpp graphics-lib/graphics-functions.cpp graphics-lib/button.cpp)

# Link the SDL2 library
target_link_libraries(exec SDL2::SDL2)
target_link_libraries(exec SDL_ttf)
target_link_libraries(exec nlohmann_json::nlohmann_json)
