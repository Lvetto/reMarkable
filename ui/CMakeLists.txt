cmake_minimum_required(VERSION 3.10) # Specify the minimum version of CMake
set(CMAKE_CXX_STANDARD 11)  # or a later standard like 14, 17, 20
set(CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}")

project(MyProject) # Name of your project

# Find the SDL2 library
find_package(SDL2 REQUIRED)
find_package(PkgConfig REQUIRED)

include_directories(${SDL2_INCLUDE_DIRS})

find_package(SDL2_TTF REQUIRED)

PKG_SEARCH_MODULE(SDL2IMAGE REQUIRED SDL2_image>=2.0.0)

# Find and configure the json library
add_subdirectory(json)

# Add executable target with source files
add_executable(exec main.cpp graphics-lib/graphics-functions.cpp graphics-lib/button.cpp)

# Link the SDL2 library
target_link_libraries(exec ${SDL2_LIBRARIES})
target_link_libraries(exec ${SDL2TTF_LIBRARY})
target_link_libraries(exec ${SDL2IMAGE_LIBRARIES})
target_link_libraries(exec nlohmann_json::nlohmann_json)

add_custom_target(run
    COMMAND exec
    DEPENDS exec
    WORKING_DIRECTORY ${CMAKE_PROJECT_DIR}
)
