#pragma once

#ifndef USE_TCL_STUBS
#define USE_TCL_STUBS 1
#endif
#ifndef USE_TK_STUBS
#define USE_TK_STUBS 1
#endif

#include <tcl.h>
#include <tk.h>
#include <climits>
#include <cstdint>

// Tcl 8.6 vs Tcl 9.0 compatibility definitions
#ifndef TCL_SIZE_MAX
  #if defined(TCL_MAJOR_VERSION) && (TCL_MAJOR_VERSION < 9)
    typedef int Tcl_Size;
    #define TCL_SIZE_MAX INT_MAX
    #define TCL_SIZE_MODIFIER ""
  #endif
#endif

#ifdef __cplusplus
#define TKBLEND_EXTERN_C extern "C"
#else
#define TKBLEND_EXTERN_C
#endif

#if defined(_WIN32) || defined(__CYGWIN__)
  #ifdef TKBLEND_BUILD_DLL
    #define TKBLEND_API TKBLEND_EXTERN_C TCL_STORAGE_CLASS __declspec(dllexport)
  #else
    #define TKBLEND_API TKBLEND_EXTERN_C TCL_STORAGE_CLASS
  #endif
#else
  #define TKBLEND_API TKBLEND_EXTERN_C TCL_STORAGE_CLASS __attribute__((visibility("default")))
#endif

// Platform Specific Windowing Headers
#if defined(__linux__) || defined(__unix__)
  #if !defined(__APPLE__)
    #include <X11/Xlib.h>
    #include <X11/Xutil.h>
  #endif
#elif defined(_WIN32)
  #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
  #endif
  #include <windows.h>
  #include <tkPlatDecls.h>
#elif defined(__APPLE__)
  #undef panic
  #include <CoreGraphics/CoreGraphics.h>
  typedef struct TkRegion_ *TkRegion;
  #include <tkMacOSX.h>
#endif

namespace tkblend {

inline bool EnsureTkStubs(Tcl_Interp* interp) {
#if defined(USE_TCL_STUBS) && defined(USE_TK_STUBS)
    if (!interp) return false;
    if (!Tcl_InitStubs(interp, "8.6", 0)) {
        return false;
    }
    if (!Tk_InitStubs(interp, "8.6", 0)) {
        return false;
    }
#endif
    return true;
}

} // namespace tkblend
