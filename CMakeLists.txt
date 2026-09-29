if(CMAKE_HOST_SYSTEM_NAME STREQUAL "Darwin" OR CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "Minimum macOS version" FORCE)
endif()

cmake_minimum_required(VERSION 3.20)
project(tkblend LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

if(APPLE)
    enable_language(OBJCXX)
    set(CMAKE_OBJCXX_STANDARD 20)
    set(CMAKE_OBJCXX_STANDARD_REQUIRED ON)
    set(CMAKE_OBJCXX_EXTENSIONS OFF)
endif()

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
# FreeType Detection & Fallback (for Color Emojis)
# ------------------------------------------------------------------------------
find_package(Freetype QUIET)
if(NOT Freetype_FOUND AND NOT FREETYPE_FOUND)
    include(FetchContent)
    FetchContent_Declare(
        freetype
        GIT_REPOSITORY https://gitlab.freedesktop.org/freetype/freetype.git
        GIT_TAG        VER-2-13-2
        GIT_SHALLOW    TRUE
    )
    set(FT_DISABLE_ZLIB TRUE CACHE BOOL "Disable ZLIB" FORCE)
    set(FT_DISABLE_BZIP2 TRUE CACHE BOOL "Disable BZIP2" FORCE)
    set(FT_DISABLE_PNG TRUE CACHE BOOL "Disable PNG" FORCE)
    set(FT_DISABLE_HARFBUZZ TRUE CACHE BOOL "Disable HARFBUZZ" FORCE)
    set(FT_DISABLE_BROTLI TRUE CACHE BOOL "Disable BROTLI" FORCE)
    set(SKIP_INSTALL_ALL TRUE CACHE BOOL "Disable FreeType install" FORCE)
    set(SKIP_INSTALL_LIBRARIES TRUE CACHE BOOL "Disable FreeType install" FORCE)
    set(SKIP_INSTALL_HEADERS TRUE CACHE BOOL "Disable FreeType install" FORCE)

    if(DEFINED CMAKE_POLICY_VERSION_MINIMUM)
        set(_TKBLEND_PREVIOUS_POLICY_VERSION_MINIMUM "${CMAKE_POLICY_VERSION_MINIMUM}")
        set(_TKBLEND_HAS_PREVIOUS_POLICY_VERSION_MINIMUM TRUE)
    endif()
    set(CMAKE_POLICY_VERSION_MINIMUM 3.5)
    FetchContent_MakeAvailable(freetype)
    if(_TKBLEND_HAS_PREVIOUS_POLICY_VERSION_MINIMUM)
        set(CMAKE_POLICY_VERSION_MINIMUM "${_TKBLEND_PREVIOUS_POLICY_VERSION_MINIMUM}")
    else()
        unset(CMAKE_POLICY_VERSION_MINIMUM)
    endif()
    unset(_TKBLEND_PREVIOUS_POLICY_VERSION_MINIMUM)
    unset(_TKBLEND_HAS_PREVIOUS_POLICY_VERSION_MINIMUM)
endif()

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
        /opt/homebrew/opt/tcl-tk/include
        /usr/local/opt/tcl-tk/include
        /opt/homebrew/include
        /usr/local/include
        /usr/include/tcl8.6
        /usr/include/tk8.6
        /usr/local/include/tcl8.6
        /usr/local/include/tk8.6
        /usr/include
        "C:/Program Files/Tcl"
        "C:/Program Files/Tcl/include"
        "C:/msys64/ucrt64/include"
        "C:/msys64/mingw64/include"
        "C:/msys64/clang64/include"
    PATH_SUFFIXES tcl8.6 tk8.6 tcl tk include
)

find_path(TCL_INCLUDE_PATH
    NAMES tcl.h
    HINTS
        ${TCL_PKG_INCLUDE_DIRS}
        ${Python_INCLUDE_DIRS}
        /opt/homebrew/opt/tcl-tk/include
        /usr/local/opt/tcl-tk/include
        /opt/homebrew/include
        /usr/local/include
        /usr/include/tcl8.6
        /usr/local/include/tcl8.6
        /usr/include
        "C:/Program Files/Tcl"
        "C:/Program Files/Tcl/include"
        "C:/msys64/ucrt64/include"
        "C:/msys64/mingw64/include"
        "C:/msys64/clang64/include"
    PATH_SUFFIXES tcl8.6 tk8.6 tcl include
)

find_library(TK_LIBRARY
    NAMES tk86t tk8.6 tk86 tk
    HINTS
        ${TK_PKG_LIBRARY_DIRS}
        ${Python_LIBRARY_DIRS}
        /opt/homebrew/opt/tcl-tk/lib
        /usr/local/opt/tcl-tk/lib
        /opt/homebrew/lib
        /usr/local/lib
        /usr/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib/aarch64-linux-gnu
        "C:/Program Files/Tcl/lib"
        "C:/msys64/ucrt64/lib"
        "C:/msys64/mingw64/lib"
        "C:/msys64/clang64/lib"
)

find_library(TCL_LIBRARY
    NAMES tcl86t tcl8.6 tcl86 tcl
    HINTS
        ${TCL_PKG_LIBRARY_DIRS}
        ${Python_LIBRARY_DIRS}
        /opt/homebrew/opt/tcl-tk/lib
        /usr/local/opt/tcl-tk/lib
        /opt/homebrew/lib
        /usr/local/lib
        /usr/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib/aarch64-linux-gnu
        "C:/Program Files/Tcl/lib"
        "C:/msys64/ucrt64/lib"
        "C:/msys64/mingw64/lib"
        "C:/msys64/clang64/lib"
)

find_library(TK_STUB_LIBRARY
    NAMES tkstub8.6 tkstub86 tkstub
    HINTS
        ${TK_PKG_LIBRARY_DIRS}
        ${Python_LIBRARY_DIRS}
        /opt/homebrew/opt/tcl-tk/lib
        /usr/local/opt/tcl-tk/lib
        /opt/homebrew/lib
        /usr/local/lib
        /usr/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib/aarch64-linux-gnu
        "C:/Program Files/Tcl/lib"
        "C:/msys64/ucrt64/lib"
        "C:/msys64/mingw64/lib"
        "C:/msys64/clang64/lib"
)

find_library(TCL_STUB_LIBRARY
    NAMES tclstub8.6 tclstub86 tclstub
    HINTS
        ${TCL_PKG_LIBRARY_DIRS}
        ${Python_LIBRARY_DIRS}
        /opt/homebrew/opt/tcl-tk/lib
        /usr/local/opt/tcl-tk/lib
        /opt/homebrew/lib
        /usr/local/lib
        /usr/lib
        /usr/lib/x86_64-linux-gnu
        /usr/lib/aarch64-linux-gnu
        "C:/Program Files/Tcl/lib"
        "C:/msys64/ucrt64/lib"
        "C:/msys64/mingw64/lib"
        "C:/msys64/clang64/lib"
)

message(STATUS "TK_INCLUDE_PATH: ${TK_INCLUDE_PATH}")
message(STATUS "TCL_INCLUDE_PATH: ${TCL_INCLUDE_PATH}")
message(STATUS "TK_LIBRARY: ${TK_LIBRARY}")
message(STATUS "TCL_LIBRARY: ${TCL_LIBRARY}")
message(STATUS "TK_STUB_LIBRARY: ${TK_STUB_LIBRARY}")
message(STATUS "TCL_STUB_LIBRARY: ${TCL_STUB_LIBRARY}")

if(WIN32)
    if(NOT TK_INCLUDE_PATH OR NOT TCL_INCLUDE_PATH
        OR NOT EXISTS "${TK_INCLUDE_PATH}/tkPlatDecls.h")
        message(FATAL_ERROR
            "Windows builds require Tcl/Tk 8.6 development headers. "
            "Install the tk=8.6.13 conda-forge package and set "
            "CMAKE_PREFIX_PATH to its Library directory."
        )
    endif()
    if(NOT TK_LIBRARY OR NOT TCL_LIBRARY
        OR NOT TK_STUB_LIBRARY OR NOT TCL_STUB_LIBRARY)
        message(FATAL_ERROR
            "Windows builds require Tcl/Tk 8.6 import and stub libraries. "
            "Install the tk=8.6.13 conda-forge package and set "
            "CMAKE_PREFIX_PATH to its Library directory."
        )
    endif()
endif()

# ------------------------------------------------------------------------------
# Sanitizers & Coverage Options
# ------------------------------------------------------------------------------
option(ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
option(ENABLE_NANOBIND_LEAK_CHECK "Enable nanobind debug leak tracking and abort on leak" OFF)
option(ENABLE_COVERAGE "Enable code coverage instrumentation" OFF)

# ------------------------------------------------------------------------------
# Platform-specific dependencies (X11, GDI, Cocoa, CoreText, DirectWrite, Fontconfig)
# ------------------------------------------------------------------------------
set(PLATFORM_SOURCES)
set(PLATFORM_LIBS)
set(PLATFORM_INCLUDES)

if(APPLE)
    find_library(COCOA_LIBRARY Cocoa REQUIRED)
    find_library(COREGRAPHICS_LIBRARY CoreGraphics REQUIRED)
    find_library(CORETEXT_LIBRARY CoreText REQUIRED)
    find_library(COREFOUNDATION_LIBRARY CoreFoundation REQUIRED)
    list(APPEND PLATFORM_SOURCES src/blit/blit_macos.mm src/font/font_resolver_macos.mm)
    list(APPEND PLATFORM_LIBS ${COCOA_LIBRARY} ${COREGRAPHICS_LIBRARY} ${CORETEXT_LIBRARY} ${COREFOUNDATION_LIBRARY})
    set_source_files_properties(src/window_shape.cpp PROPERTIES COMPILE_FLAGS "-x objective-c++ -fobjc-arc")
    set_source_files_properties(src/blit/blit_macos.mm src/font/font_resolver_macos.mm PROPERTIES COMPILE_FLAGS "-fobjc-arc")
elseif(WIN32)
    list(APPEND PLATFORM_SOURCES src/blit/blit_win32.cpp src/font/font_resolver_win32.cpp)
    list(APPEND PLATFORM_LIBS gdi32 user32 dwrite)
else()
    find_package(X11 REQUIRED)
    list(APPEND PLATFORM_SOURCES src/blit/blit_x11.cpp src/font/font_resolver_linux.cpp)
    list(APPEND PLATFORM_LIBS ${X11_LIBRARIES})
    if(X11_Xext_LIB)
        list(APPEND PLATFORM_LIBS ${X11_Xext_LIB})
    endif()

    find_package(PkgConfig QUIET)
    if(PkgConfig_FOUND)
        pkg_check_modules(FONTCONFIG QUIET fontconfig)
        if(FONTCONFIG_FOUND)
            list(APPEND PLATFORM_LIBS ${FONTCONFIG_LIBRARIES})
            list(APPEND PLATFORM_INCLUDES ${FONTCONFIG_INCLUDE_DIRS})
            add_compile_definitions(TKBLEND_HAS_FONTCONFIG=1)
        endif()
    endif()
endif()

find_package(ZLIB QUIET)
if(NOT ZLIB_FOUND)
    include(FetchContent)
    set(ZLIB_BUILD_EXAMPLES OFF CACHE BOOL "Disable Zlib examples" FORCE)
    set(SKIP_INSTALL_ALL TRUE CACHE BOOL "Disable Zlib install" FORCE)
    set(SKIP_INSTALL_LIBRARIES TRUE CACHE BOOL "Disable Zlib install" FORCE)
    set(SKIP_INSTALL_HEADERS TRUE CACHE BOOL "Disable Zlib install" FORCE)
    set(SKIP_INSTALL_FILES TRUE CACHE BOOL "Disable Zlib install" FORCE)
    FetchContent_Declare(
        zlib
        GIT_REPOSITORY https://github.com/madler/zlib.git
        GIT_TAG        v1.3.1
        GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(zlib)
    add_library(ZLIB::ZLIB ALIAS zlibstatic)
endif()

# ------------------------------------------------------------------------------
# Module Target
# ------------------------------------------------------------------------------
set(TKBLEND_SOURCES
    src/color.cpp
    src/animation.cpp
    src/gradient.cpp
    src/path.cpp
    src/font_manager.cpp
    src/font/embedded_fonts.cpp
    src/shadow_engine.cpp
    src/emoji_engine.cpp
    src/draw_batch.cpp
    src/style_engine.cpp
    src/surface.cpp
    src/window_shape.cpp
    src/bindings.cpp
    src/blit/blit_common.cpp
    ${PLATFORM_SOURCES}
)

nanobind_add_module(
    _tkblend
    NB_STATIC
    ${TKBLEND_SOURCES}
)

set(TKBLEND_TCLTK_INCLUDE_DIRS
    ${TK_INCLUDE_PATH}
    ${TCL_INCLUDE_PATH}
)
if(NOT WIN32)
    list(APPEND TKBLEND_TCLTK_INCLUDE_DIRS
        ${TK_INCLUDE_PATH}/tk-private/generic
        ${TK_INCLUDE_PATH}/tk-private/unix
    )
endif()

target_include_directories(_tkblend PRIVATE
    src
    src/blit
    src/font
    ${PLATFORM_INCLUDES}
    ${blend2d_SOURCE_DIR}
    ${blend2d_SOURCE_DIR}/blend2d
    ${TKBLEND_TCLTK_INCLUDE_DIRS}
)

if(FREETYPE_INCLUDE_DIRS)
    target_include_directories(_tkblend PRIVATE ${FREETYPE_INCLUDE_DIRS})
endif()

if(X11_INCLUDE_DIR)
    target_include_directories(_tkblend PRIVATE ${X11_INCLUDE_DIR})
endif()

target_link_libraries(_tkblend PRIVATE
    blend2d::blend2d
    ZLIB::ZLIB
    ${PLATFORM_LIBS}
    ${CMAKE_DL_LIBS}
)

if(TARGET Freetype::Freetype)
    target_link_libraries(_tkblend PRIVATE Freetype::Freetype)
elseif(TARGET freetype)
    target_link_libraries(_tkblend PRIVATE freetype)
elseif(FREETYPE_LIBRARIES)
    target_link_libraries(_tkblend PRIVATE ${FREETYPE_LIBRARIES})
endif()

if(UNIX AND NOT APPLE)
    if(NOT TK_STUB_LIBRARY OR NOT TCL_STUB_LIBRARY)
        message(FATAL_ERROR "Tcl/Tk stub libraries are required on Linux")
    endif()
    target_compile_definitions(_tkblend PRIVATE USE_TCL_STUBS USE_TK_STUBS)
    target_link_libraries(_tkblend PRIVATE ${TK_STUB_LIBRARY} ${TCL_STUB_LIBRARY})
elseif(WIN32)
    target_compile_definitions(_tkblend PRIVATE USE_TCL_STUBS USE_TK_STUBS)
    target_link_libraries(_tkblend PRIVATE
        ${TK_STUB_LIBRARY}
        ${TCL_STUB_LIBRARY}
        ${TK_LIBRARY}
        ${TCL_LIBRARY}
    )
else()
    if(NOT TK_STUB_LIBRARY OR NOT TCL_STUB_LIBRARY)
        message(FATAL_ERROR
            "Tcl/Tk stub libraries (libtclstub8.6.a, libtkstub8.6.a) are required on macOS. "
            "Install them via 'brew install tcl-tk' and set CMAKE_PREFIX_PATH."
        )
    endif()
    target_compile_definitions(_tkblend PRIVATE USE_TCL_STUBS USE_TK_STUBS)
    target_link_libraries(_tkblend PRIVATE ${TK_STUB_LIBRARY} ${TCL_STUB_LIBRARY})
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

if(ENABLE_NANOBIND_LEAK_CHECK)
    target_compile_definitions(_tkblend PRIVATE NB_DEBUG=1 NB_ABORT_ON_LEAK=1)
endif()

if(MINGW)
    target_link_options(_tkblend PRIVATE -static-libgcc -static-libstdc++)
endif()

# Install target for packaging
install(TARGETS _tkblend LIBRARY DESTINATION tkblend RUNTIME DESTINATION tkblend ARCHIVE DESTINATION tkblend)

