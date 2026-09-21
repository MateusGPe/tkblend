cmake_minimum_required(VERSION 3.20)
project(tkblend LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(MSVC)
    add_compile_options(/EHsc)
else()
    add_compile_options(-fexceptions)
endif()

# ------------------------------------------------------------------------------
# Python & Nanobind Setup
# ------------------------------------------------------------------------------
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

find_package(nanobind CONFIG QUIET)
if(NOT nanobind_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        nanobind
        GIT_REPOSITORY https://github.com/wjakob/nanobind.git
        GIT_TAG        v2.5.0
        GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(nanobind)
endif()

# ------------------------------------------------------------------------------
# Fetch AsmJit & Blend2D
# ------------------------------------------------------------------------------
include(FetchContent)

set(ASMJIT_STATIC ON CACHE BOOL "Build static AsmJit library" FORCE)
set(ASMJIT_TEST OFF CACHE BOOL "Build AsmJit tests" FORCE)
set(ASMJIT_NO_CUSTOM_ALLOCATOR ON CACHE BOOL "Disable AsmJit custom allocator" FORCE)
set(ASMJIT_NO_INSTALL ON CACHE BOOL "Disable AsmJit install" FORCE)

FetchContent_Declare(
    asmjit
    GIT_REPOSITORY https://github.com/asmjit/asmjit.git
    GIT_TAG        master
    GIT_SHALLOW    TRUE
)
# Populate asmjit without adding target directly, so Blend2D configures it
FetchContent_GetProperties(asmjit)
if(NOT asmjit_POPULATED)
    FetchContent_Populate(asmjit)
endif()

set(ASMJIT_DIR "${asmjit_SOURCE_DIR}" CACHE PATH "AsmJit directory for Blend2D" FORCE)

set(BLEND2D_STATIC ON CACHE BOOL "Build static Blend2D library" FORCE)
set(BLEND2D_TEST OFF CACHE BOOL "Build Blend2D tests" FORCE)
set(BLEND2D_NO_JIT OFF CACHE BOOL "Enable Blend2D JIT compiler" FORCE)
set(BLEND2D_NO_STDCXX OFF CACHE BOOL "Use C++ standard library" FORCE)
set(BLEND2D_NO_INSTALL ON CACHE BOOL "Disable Blend2D install" FORCE)

FetchContent_Declare(
    blend2d
    GIT_REPOSITORY https://github.com/blend2d/blend2d.git
    GIT_TAG        master
    GIT_SHALLOW    TRUE
)

set(_PRE_BLEND2D_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
FetchContent_MakeAvailable(blend2d)
set(CMAKE_CXX_FLAGS "${_PRE_BLEND2D_CXX_FLAGS}")

# ------------------------------------------------------------------------------
# Tcl/Tk Detection
# ------------------------------------------------------------------------------
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(TK_PKG QUIET tk tk8.6 tk86)
    pkg_check_modules(TCL_PKG QUIET tcl tcl8.6 tcl86)
endif()

find_path(TK_INCLUDE_PATH
    NAMES tk.h
    HINTS
        ${TK_PKG_INCLUDE_DIRS}
        ${Python_INCLUDE_DIRS}
        /usr/include/tcl8.6
        /usr/include/tk8.6
        /usr/local/include/tcl8.6
        /usr/local/include/tk8.6
        /usr/include
        /usr/local/include
        /opt/homebrew/include
        /opt/homebrew/opt/tcl-tk/include
        "C:/Program Files/Tcl"
        "C:/Program Files/Tcl/include"
    PATH_SUFFIXES tcl8.6 tk8.6 tcl tk include
)

find_path(TCL_INCLUDE_PATH
    NAMES tcl.h
    HINTS
        ${TCL_PKG_INCLUDE_DIRS}
        ${Python_INCLUDE_DIRS}
        /usr/include/tcl8.6
        /usr/local/include/tcl8.6
        /usr/include
        /usr/local/include
        /opt/homebrew/include
        /opt/homebrew/opt/tcl-tk/include
        "C:/Program Files/Tcl"
        "C:/Program Files/Tcl/include"
    PATH_SUFFIXES tcl8.6 tk8.6 tcl include
)

find_library(TK_LIBRARY
    NAMES tk8.6 tk86 tk
    HINTS
        ${TK_PKG_LIBRARY_DIRS}
        ${Python_LIBRARY_DIRS}
        /usr/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib/aarch64-linux-gnu
        /usr/local/lib
        /opt/homebrew/lib
        /opt/homebrew/opt/tcl-tk/lib
        "C:/Program Files/Tcl/lib"
)

find_library(TCL_LIBRARY
    NAMES tcl8.6 tcl86 tcl
    HINTS
        ${TCL_PKG_LIBRARY_DIRS}
        ${Python_LIBRARY_DIRS}
        /usr/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib/aarch64-linux-gnu
        /usr/local/lib
        /opt/homebrew/lib
        /opt/homebrew/opt/tcl-tk/lib
        "C:/Program Files/Tcl/lib"
)

find_library(TK_STUB_LIBRARY
    NAMES tkstub8.6 tkstub86 tkstub
    HINTS
        ${TK_PKG_LIBRARY_DIRS}
        ${Python_LIBRARY_DIRS}
        /usr/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib/aarch64-linux-gnu
        /usr/local/lib
        /opt/homebrew/lib
        /opt/homebrew/opt/tcl-tk/lib
        "C:/Program Files/Tcl/lib"
)

find_library(TCL_STUB_LIBRARY
    NAMES tclstub8.6 tclstub86 tclstub
    HINTS
        ${TCL_PKG_LIBRARY_DIRS}
        ${Python_LIBRARY_DIRS}
        /usr/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib/aarch64-linux-gnu
        /usr/local/lib
        /opt/homebrew/lib
        /opt/homebrew/opt/tcl-tk/lib
        "C:/Program Files/Tcl/lib"
)

message(STATUS "TK_INCLUDE_PATH: ${TK_INCLUDE_PATH}")
message(STATUS "TCL_INCLUDE_PATH: ${TCL_INCLUDE_PATH}")
message(STATUS "TK_LIBRARY: ${TK_LIBRARY}")
message(STATUS "TCL_LIBRARY: ${TCL_LIBRARY}")
message(STATUS "TK_STUB_LIBRARY: ${TK_STUB_LIBRARY}")
message(STATUS "TCL_STUB_LIBRARY: ${TCL_STUB_LIBRARY}")

# ------------------------------------------------------------------------------
# Sanitizers & Coverage Options
# ------------------------------------------------------------------------------
option(ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(ENABLE_COVERAGE "Enable code coverage instrumentation" OFF)

# ------------------------------------------------------------------------------
# Platform-specific dependencies (X11, GDI, Cocoa)
# ------------------------------------------------------------------------------
set(PLATFORM_SOURCES)
set(PLATFORM_LIBS)

if(APPLE)
    find_library(COCOA_LIBRARY Cocoa REQUIRED)
    find_library(COREGRAPHICS_LIBRARY CoreGraphics REQUIRED)
    list(APPEND PLATFORM_SOURCES src/blit/blit_macos.mm)
    list(APPEND PLATFORM_LIBS ${COCOA_LIBRARY} ${COREGRAPHICS_LIBRARY})
elseif(WIN32)
    list(APPEND PLATFORM_SOURCES src/blit/blit_win32.cpp)
    list(APPEND PLATFORM_LIBS gdi32 user32)
else()
    find_package(X11 REQUIRED)
    list(APPEND PLATFORM_SOURCES src/blit/blit_x11.cpp)
    list(APPEND PLATFORM_LIBS ${X11_LIBRARIES})
endif()

# ------------------------------------------------------------------------------
# Module Target
# ------------------------------------------------------------------------------
set(TKBLEND_SOURCES
    src/tkblend.cpp
    src/theme/theme_engine.cpp
    src/theme/element_button.cpp
    src/theme/element_entry.cpp
    src/theme/element_arrows.cpp
    src/theme/element_tab.cpp
    src/theme/element_checkradio.cpp
    src/theme/element_progressbar.cpp
    src/theme/element_scrollbar.cpp
    src/theme/element_scale.cpp
    ${PLATFORM_SOURCES}
)

nanobind_add_module(
    _tkblend
    NB_STATIC
    ${TKBLEND_SOURCES}
)

target_include_directories(_tkblend PRIVATE
    src
    src/blit
    src/theme
    ${blend2d_SOURCE_DIR}
    ${blend2d_SOURCE_DIR}/blend2d
    ${TK_INCLUDE_PATH}
    ${TK_INCLUDE_PATH}/tk-private/generic
    ${TK_INCLUDE_PATH}/tk-private/generic/ttk
    ${TK_INCLUDE_PATH}/tk-private/unix
    ${TCL_INCLUDE_PATH}
)

if(X11_INCLUDE_DIR)
    target_include_directories(_tkblend PRIVATE ${X11_INCLUDE_DIR})
endif()

target_link_libraries(_tkblend PRIVATE
    blend2d::blend2d
    ${PLATFORM_LIBS}
    ${CMAKE_DL_LIBS}
)

if(TK_STUB_LIBRARY)
    target_link_libraries(_tkblend PRIVATE ${TK_STUB_LIBRARY})
endif()
if(TCL_STUB_LIBRARY)
    target_link_libraries(_tkblend PRIVATE ${TCL_STUB_LIBRARY})
endif()
if(TK_LIBRARY)
    target_link_libraries(_tkblend PRIVATE ${TK_LIBRARY})
endif()
if(TCL_LIBRARY)
    target_link_libraries(_tkblend PRIVATE ${TCL_LIBRARY})
endif()


if(MSVC)
    target_compile_options(_tkblend PRIVATE /O2 /W4 /permissive- /EHsc)
    if(ENABLE_SANITIZERS)
        target_compile_options(_tkblend PRIVATE /fsanitize=address /Zi)
    endif()
else()
    if(ENABLE_COVERAGE)
        target_compile_options(_tkblend PRIVATE -O0 -g -fexceptions --coverage -fprofile-arcs -ftest-coverage -Wall -Wextra -Wno-unused-parameter)
        target_link_options(_tkblend PRIVATE --coverage)
    elseif(ENABLE_SANITIZERS)
        target_compile_options(_tkblend PRIVATE -O1 -g -fexceptions -fsanitize=address,undefined -fno-omit-frame-pointer -Wall -Wextra -Wno-unused-parameter)
        target_link_options(_tkblend PRIVATE -fsanitize=address,undefined)
    else()
        target_compile_options(_tkblend PRIVATE -O3 -fexceptions -Wall -Wextra -Wno-unused-parameter)
    endif()
endif()

# Install target for packaging
install(TARGETS _tkblend LIBRARY DESTINATION tkblend)

