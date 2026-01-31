cmake_minimum_required(VERSION 3.16)
project(voxel_sandbox LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

# GLFW
FetchContent_Declare(
  glfw
  GIT_REPOSITORY https://github.com/glfw/glfw.git
  GIT_TAG latest
)
FetchContent_MakeAvailable(glfw)

# GLAD
FetchContent_Declare(
  glad
  GIT_REPOSITORY https://github.com/Dav1dde/glad.git
  GIT_TAG master
)
FetchContent_MakeAvailable(glad)

find_package(OpenGL REQUIRED)
find_package(Threads REQUIRED)

add_executable(voxel_sandbox
  src/main.cpp
  src/Renderer.cpp
  src/World.cpp
  src/Chunk.cpp
  src/MeshBuilder.cpp
  src/Camera.cpp
  src/Raycast.cpp
  src/Entity.cpp
  src/EntityManager.cpp
  src/Mob.cpp
)

target_include_directories(voxel_sandbox PRIVATE
  ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_link_libraries(voxel_sandbox PRIVATE
  glfw
  glad
  OpenGL::GL
  Threads::Threads
)

# Copy shaders to build dir for runtime
add_custom_command(TARGET voxel_sandbox POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory
  ${CMAKE_SOURCE_DIR}/shaders $<TARGET_FILE_DIR:voxel_sandbox>/shaders
)
