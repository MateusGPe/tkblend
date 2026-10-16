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

#if !defined(_WIN32) && !defined(__APPLE__)
#include <X11/Xlib.h>
#endif
#include <tcl.h>
#include <tk.h>
#include <limits.h>
#include <cstddef>

#if defined(_WIN32)
  #ifndef WIN32_LEAN_AND_MEAN
    #define WIN32_LEAN_AND_MEAN
  #endif
  #ifndef NOMINMAX
    #define NOMINMAX
  #endif
  #include <windows.h>
  #include <tkPlatDecls.h>
  #ifdef DrawText
    #undef DrawText
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

/* -------------------------------------------------------------------------
 * Tcl/Tk 8.6 <-> 9.0+ Compatibility Layer (TIP #412, TIP #590, TIP #625)
 * ------------------------------------------------------------------------- */

/* Tcl_Size abstraction */
#ifndef TCL_SIZE_MAX
    typedef int Tcl_Size;
    #define TCL_SIZE_MAX INT_MAX
    #define TCL_SIZE_MODIFIER ""
#else
    #ifndef TCL_SIZE_MODIFIER
        #if defined(_WIN64) || defined(__x86_64__) || defined(__ppc64__) || defined(__aarch64__)
            #define TCL_SIZE_MODIFIER "l"
        #else
            #define TCL_SIZE_MODIFIER ""
        #endif
    #endif
#endif

#ifndef TCL_INDEX_NONE
    #define TCL_INDEX_NONE ((Tcl_Size)-1)
#endif

/* Const and ClientData qualifiers */
#if (TCL_MAJOR_VERSION >= 9)
    #define TKBLEND_CONST86 const
    #define TKBLEND_CLIENTDATA void *
#else
    #define TKBLEND_CONST86
    #define TKBLEND_CLIENTDATA ClientData
#endif

/* Safe string length retrieval shim */
static inline char *TkBlend_GetStringFromObj(Tcl_Obj *objPtr, Tcl_Size *sizePtr) {
#if (TCL_MAJOR_VERSION >= 9)
    return Tcl_GetStringFromObj(objPtr, sizePtr);
#else
    int legacyLen = 0;
    char *result;
    if (sizePtr == NULL) {
        return Tcl_GetStringFromObj(objPtr, NULL);
    }
    result = Tcl_GetStringFromObj(objPtr, &legacyLen);
    *sizePtr = (Tcl_Size)legacyLen;
    return result;
#endif
}

/* Safe byte array length retrieval shim */
static inline unsigned char *TkBlend_GetByteArrayFromObj(Tcl_Obj *objPtr, Tcl_Size *sizePtr) {
#if (TCL_MAJOR_VERSION >= 9)
    return Tcl_GetByteArrayFromObj(objPtr, sizePtr);
#else
    int legacyLen = 0;
    unsigned char *result;
    if (sizePtr == NULL) {
        return Tcl_GetByteArrayFromObj(objPtr, NULL);
    }
    result = Tcl_GetByteArrayFromObj(objPtr, &legacyLen);
    *sizePtr = (Tcl_Size)legacyLen;
    return result;
#endif
}

/* Safe list length query shim */
static inline int TkBlend_ListObjLength(Tcl_Interp *interp, Tcl_Obj *listPtr, Tcl_Size *sizePtr) {
#if (TCL_MAJOR_VERSION >= 9)
    return Tcl_ListObjLength(interp, listPtr, sizePtr);
#else
    int legacyLen = 0;
    int code;
    if (sizePtr == NULL) {
        return Tcl_ListObjLength(interp, listPtr, NULL);
    }
    code = Tcl_ListObjLength(interp, listPtr, &legacyLen);
    if (code == TCL_OK) {
        *sizePtr = (Tcl_Size)legacyLen;
    }
    return code;
#endif
}

/* Const-correct Tk_SetClassProcs wrapper */
static inline void TkBlend_SetClassProcs(Tk_Window tkwin,
                                        const Tk_ClassProcs *procsPtr,
                                        ClientData instanceData) {
#if (TK_MAJOR_VERSION >= 9)
    Tk_SetClassProcs(tkwin, procsPtr, (ClientData)instanceData);
#else
    Tk_SetClassProcs(tkwin, (Tk_ClassProcs *)procsPtr, instanceData);
#endif
}

/* Cross-version Tcl evaluation shim: Tcl_EvalEx exists in slot 291 across both Tcl 8.6 and 9.0+ */
static inline int TkBlend_Eval(Tcl_Interp *interp, const char *script) {
    if (!interp || !script) return TCL_ERROR;
    return Tcl_EvalEx(interp, script, -1, 0);
}

#define TKBLEND_TCL_STUB_MAGIC_86 ((int)0xFCA3BACF)
#define TKBLEND_TCL_STUB_MAGIC_90 ((int)0xFCA3BAD3)

struct TkStubInfoShim {
    int magic;
    const struct TkStubs *tkStubsPtr;
    const struct TkPlatStubs *tkPlatStubsPtr;
    const struct TkIntStubs *tkIntStubsPtr;
};

/* Unified stubs initialization: supports Tcl/Tk 8.6 through 9.0+ */
static inline int TkBlend_InitStubs(Tcl_Interp *interp) {
    if (interp == NULL) {
        return TCL_ERROR;
    }

#ifdef USE_TCL_STUBS
    // 1. Try standard Tcl_InitStubs from tclstub
    if (Tcl_InitStubs(interp, "8.6-", 0) == NULL && Tcl_InitStubs(interp, "8.6", 0) == NULL) {
        // Fallback: If host is Tcl 9.0+ and tclstub86 rejected 0xFCA3BAD3 magic:
        // Offset 0x18 in Tcl_Interp is stubTable across both Tcl 8.6 and Tcl 9.0 (TIP #590)
        struct InterpHeader {
            void *result;
            void *freeProc;
            int errorLine;
            const struct TclStubs *stubTable;
        };
        const struct TclStubs *stubs = reinterpret_cast<const InterpHeader*>(interp)->stubTable;
        if (!stubs || (stubs->magic != TKBLEND_TCL_STUB_MAGIC_86 && stubs->magic != TKBLEND_TCL_STUB_MAGIC_90)) {
            return TCL_ERROR;
        }
        tclStubsPtr = (decltype(tclStubsPtr))stubs;
        void *pkgData = nullptr;
        const char *actualVersion = tclStubsPtr->tcl_PkgRequireEx(interp, "Tcl", "8.6-", 0, &pkgData);
        if (!actualVersion) {
            actualVersion = tclStubsPtr->tcl_PkgRequireEx(interp, "Tcl", "8.6", 0, &pkgData);
            if (!actualVersion) {
                return TCL_ERROR;
            }
        }
        if (stubs->magic == TKBLEND_TCL_STUB_MAGIC_90 && pkgData) {
            tclStubsPtr = (decltype(tclStubsPtr))pkgData;
        }
    }
#endif

#ifdef USE_TK_STUBS
    // 2. Initialize Tk stubs
    if (Tk_InitStubs(interp, "8.6-", 0) == NULL && Tk_InitStubs(interp, "8.6", 0) == NULL) {
        if (!tclStubsPtr) {
            return TCL_ERROR;
        }
        void *pkgData = nullptr;
        const char *actualVersion = tclStubsPtr->tcl_PkgRequireEx(interp, "Tk", "8.6-", 0, &pkgData);
        if (!actualVersion) {
            actualVersion = tclStubsPtr->tcl_PkgRequireEx(interp, "Tk", "8.6", 0, &pkgData);
            if (!actualVersion) {
                return TCL_ERROR;
            }
        }
        if (!pkgData) {
            return TCL_ERROR;
        }
        const auto *tkInfo = reinterpret_cast<const TkStubInfoShim*>(pkgData);
        tkStubsPtr = (decltype(tkStubsPtr))tkInfo->tkStubsPtr;
#if defined(_WIN32) || defined(__CYGWIN__)
        tkPlatStubsPtr = (decltype(tkPlatStubsPtr))tkInfo->tkPlatStubsPtr;
#endif
    }
#endif

    return TCL_OK;
}

/* Cross-version Tk requested dimension queries (compatible with Tk 8.6 and Tk 9.0/9.1+) */
struct Tk8_FakeWinLayout {
    Display *display;
    char *dummy1;
    int screenNum;
    Visual *visual;
    int depth;
    Window window;
    char *dummy2;
    char *dummy3;
    Tk_Window parentPtr;
    char *dummy4;
    char *dummy5;
    char *pathName;
    Tk_Uid nameUid;
    Tk_Uid classUid;
    XWindowChanges changes;
    unsigned int dummy6;
    XSetWindowAttributes atts;
    unsigned long dummy7;
    unsigned int flags;
    char *dummy8;
#ifdef TK_USE_INPUT_METHODS
    XIC dummy9;
#endif
    void **dummy10;
    int dummy11;
    int dummy12;
    char *dummy13;
    char *dummy14;
    void *dummy15;
    int reqWidth, reqHeight;
};

struct Tk9_FakeWinLayout {
    Display *display;
    char *dummy1;
    int screenNum;
    Visual *visual;
    int depth;
    Window window;
    char *dummy2;
    char *dummy3;
    Tk_Window parentPtr;
    char *dummy4;
    char *dummy5;
    char *pathName;
    Tk_Uid nameUid;
    Tk_Uid classUid;
    XWindowChanges changes;
    unsigned int dummy6;
    XSetWindowAttributes atts;
    unsigned long dummy7;
    unsigned int flags;
    char *dummy8;
#ifdef TK_USE_INPUT_METHODS
    XIC dummy9;
#endif
    void **dummy10;
    ptrdiff_t dummy11;
    ptrdiff_t dummy12;
    char *dummy13;
    char *dummy14;
    void *dummy15;
    int reqWidth, reqHeight;
};

#if defined(TK_MAJOR_VERSION) && (TK_MAJOR_VERSION < 9)
static_assert(offsetof(Tk8_FakeWinLayout, reqWidth) == offsetof(Tk_FakeWin, reqWidth),
              "Tk8_FakeWinLayout::reqWidth offset mismatch with Tk_FakeWin");
static_assert(offsetof(Tk8_FakeWinLayout, reqHeight) == offsetof(Tk_FakeWin, reqHeight),
              "Tk8_FakeWinLayout::reqHeight offset mismatch with Tk_FakeWin");
#elif defined(TK_MAJOR_VERSION) && (TK_MAJOR_VERSION >= 9)
static_assert(offsetof(Tk9_FakeWinLayout, reqWidth) == offsetof(Tk_FakeWin, reqWidth),
              "Tk9_FakeWinLayout::reqWidth offset mismatch with Tk_FakeWin");
static_assert(offsetof(Tk9_FakeWinLayout, reqHeight) == offsetof(Tk_FakeWin, reqHeight),
              "Tk9_FakeWinLayout::reqHeight offset mismatch with Tk_FakeWin");
#endif

static inline bool TkBlend_IsTk9() {
    if (tkStubsPtr && tkStubsPtr->magic == TKBLEND_TCL_STUB_MAGIC_90) return true;
    if (tclStubsPtr && tclStubsPtr->magic == TKBLEND_TCL_STUB_MAGIC_90) return true;
#if defined(TK_MAJOR_VERSION) && (TK_MAJOR_VERSION >= 9)
    if (!tkStubsPtr && !tclStubsPtr) return true;
#endif
    return false;
}

static inline int TkBlend_ReqWidth(Tk_Window tkwin) {
    if (!tkwin) return 0;
    if (TkBlend_IsTk9()) {
        return reinterpret_cast<const Tk9_FakeWinLayout*>(tkwin)->reqWidth;
    }
    return reinterpret_cast<const Tk8_FakeWinLayout*>(tkwin)->reqWidth;
}

static inline int TkBlend_ReqHeight(Tk_Window tkwin) {
    if (!tkwin) return 0;
    if (TkBlend_IsTk9()) {
        return reinterpret_cast<const Tk9_FakeWinLayout*>(tkwin)->reqHeight;
    }
    return reinterpret_cast<const Tk8_FakeWinLayout*>(tkwin)->reqHeight;
}


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
  #ifndef NOMINMAX
    #define NOMINMAX
  #endif
  #include <windows.h>
  #include <tkPlatDecls.h>
  #ifdef DrawText
    #undef DrawText
  #endif
#elif defined(__APPLE__)
  #undef panic
  #include <CoreGraphics/CoreGraphics.h>
  typedef struct TkRegion_ *TkRegion;
  #include <tkMacOSX.h>
#endif
