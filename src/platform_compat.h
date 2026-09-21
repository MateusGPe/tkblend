#pragma once

#ifndef USE_TCL_STUBS
#define USE_TCL_STUBS 1
#endif
#ifndef USE_TK_STUBS
#define USE_TK_STUBS 1
#endif
#ifndef USE_TTK_STUBS
#define USE_TTK_STUBS 1
#endif

#include <tcl.h>
#include <tk.h>

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

#if __has_include(<tk-private/generic/ttk/ttkTheme.h>)
  #include <tk-private/generic/ttk/ttkTheme.h>
  #include <tk-private/generic/ttk/ttkDecls.h>
#elif __has_include(<ttk/ttkTheme.h>)
  #include <ttk/ttkTheme.h>
  #include <ttk/ttkDecls.h>
#elif __has_include(<ttkTheme.h>)
  #include <ttkTheme.h>
  #include <ttkDecls.h>
#else
  // Standard TTK Theme subsystem definitions (Tk 8.5, 8.6, 9.0 ABI)
  #define TTK_STATE_ACTIVE        (1<<0)
  #define TTK_STATE_DISABLED      (1<<1)
  #define TTK_STATE_FOCUS         (1<<2)
  #define TTK_STATE_PRESSED       (1<<3)
  #define TTK_STATE_SELECTED      (1<<4)
  #define TTK_STATE_BACKGROUND    (1<<5)
  #define TTK_STATE_ALTERNATE     (1<<6)
  #define TTK_STATE_INVALID       (1<<7)
  #define TTK_STATE_READONLY      (1<<8)
  #define TTK_STATE_HOVER         (1<<9)

  #define TTK_STATE_USER1         (1<<27)
  #define TTK_STATE_USER2         (1<<28)
  #define TTK_STATE_USER3         (1<<29)
  #define TTK_STATE_USER4         (1<<30)
  #define TTK_STATE_USER5         (1<<31)

  typedef unsigned int Ttk_State;

  typedef struct {
      int x;
      int y;
      int width;
      int height;
  } Ttk_Box;

  typedef struct {
      short left;
      short top;
      short right;
      short bottom;
  } Ttk_Padding;

  typedef struct Ttk_Theme_ *Ttk_Theme;
  typedef struct Ttk_ElementClass_ *Ttk_ElementClass;

  typedef struct {
      const char *optionName;
      Tk_OptionType type;
      int offset;
      const char *defaultValue;
  } Ttk_ElementOptionSpec;

  #define TTK_NODE_EXTENDS        (1<<0)
  #define TTK_NODE_NULL           (1<<1)

  enum TTKStyleVersion2 { TK_STYLE_VERSION_2 = 2 };

  typedef struct Ttk_ElementSpec {
      enum TTKStyleVersion2 version;
      size_t elementSize;
      const Ttk_ElementOptionSpec *options;
      void (*geometry)(void *clientData, void *elementRecord, Tk_Window tkwin, int *widthPtr, int *heightPtr, Ttk_Padding *paddingPtr);
      void (*draw)(void *clientData, void *elementRecord, Tk_Window tkwin, Drawable d, Ttk_Box b, Ttk_State state);
  } Ttk_ElementSpec;

  #ifdef __cplusplus
  extern "C" {
  #endif
    Ttk_Theme Ttk_GetTheme(Tcl_Interp *interp, const char *themeName);
    Ttk_Theme Ttk_CreateTheme(Tcl_Interp *interp, const char *themeName, Ttk_Theme parentTheme);
    Ttk_Theme Ttk_GetCurrentTheme(Tcl_Interp *interp);
    Ttk_Theme Ttk_GetDefaultTheme(Tcl_Interp *interp);
    Ttk_ElementClass Ttk_RegisterElementSpec(Ttk_Theme theme, const char *elementName, const Ttk_ElementSpec *spec, void *clientData);
    Ttk_ElementClass Ttk_RegisterElement(Tcl_Interp *interp, Ttk_Theme theme, const char *elementName, const Ttk_ElementSpec *spec, void *clientData);
  #ifdef __cplusplus
  }
  #endif
#endif

#ifndef TTK_LAYOUT_SPEC_VERSION
  #define TTK_LAYOUT_SPEC_VERSION TK_STYLE_VERSION_2
#endif


// Platform Specific Blit Headers
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
  #include <CoreGraphics/CoreGraphics.h>
  #include <tkMacOSX.h>
#endif
