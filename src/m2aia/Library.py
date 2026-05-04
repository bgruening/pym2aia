import ctypes
import ctypes.util
from ctypes import c_void_p, c_uint32, c_char_p, c_double, c_float, c_ushort, POINTER
import pathlib
import platform
import os

_lib = None


def _configure_signatures(lib):
    """Declare argtypes and restype for every C function in libM2aiaCore. Called once."""
    H = c_void_p  # opaque image handle

    lib.CreateImageHandle.argtypes              = [c_char_p];                                  lib.CreateImageHandle.restype              = H
    lib.DestroyImageHandle.argtypes             = [H];                                         lib.DestroyImageHandle.restype             = None
    lib.GetSize.argtypes                        = [H, POINTER(c_uint32)];                      lib.GetSize.restype                        = None
    lib.GetSpacing.argtypes                     = [H, POINTER(c_double)];                      lib.GetSpacing.restype                     = None
    lib.GetOrigin.argtypes                      = [H, POINTER(c_double)];                      lib.GetOrigin.restype                      = None
    lib.GetXAxis.argtypes                       = [H, POINTER(c_double)];                      lib.GetXAxis.restype                       = None
    lib.GetXAxisDepth.argtypes                  = [H];                                         lib.GetXAxisDepth.restype                  = c_uint32
    lib.GetImageArrayFloat64.argtypes           = [H, c_double, c_double, POINTER(c_double)];  lib.GetImageArrayFloat64.restype           = None
    lib.GetImageArrayFloat32.argtypes           = [H, c_double, c_double, POINTER(c_float)];   lib.GetImageArrayFloat32.restype           = None
    lib.GetMaskArray.argtypes                   = [H, POINTER(c_ushort)];                      lib.GetMaskArray.restype                   = None
    lib.GetIndexArray.argtypes                  = [H, POINTER(c_uint32)];                      lib.GetIndexArray.restype                  = None
    lib.GetNormalizationArray.argtypes          = [H, c_char_p, POINTER(c_float)];            lib.GetNormalizationArray.restype          = None
    lib.GetSpectrumType.argtypes                = [H];                                         lib.GetSpectrumType.restype                = c_uint32
    lib.GetSpectrumDepth.argtypes               = [H, c_uint32];                               lib.GetSpectrumDepth.restype               = c_uint32
    lib.GetSizeInBytesOfYAxisType.argtypes      = [H];                                         lib.GetSizeInBytesOfYAxisType.restype      = c_uint32
    lib.GetMeanSpectrum.argtypes                = [H, POINTER(c_double)];                      lib.GetMeanSpectrum.restype                = None
    lib.GetMaxSpectrum.argtypes                 = [H, POINTER(c_double)];                      lib.GetMaxSpectrum.restype                 = None
    lib.GetSpectrumPosition.argtypes            = [H, c_uint32, POINTER(c_uint32)];            lib.GetSpectrumPosition.restype            = None
    lib.GetYDataTypeSizeInBytes.argtypes        = [H];                                         lib.GetYDataTypeSizeInBytes.restype        = c_uint32
    lib.GetNumberOfSpectra.argtypes             = [H];                                         lib.GetNumberOfSpectra.restype             = c_uint32
    lib.GetMetaDataDictionary.argtypes          = [H];                                         lib.GetMetaDataDictionary.restype          = c_char_p
    lib.DestroyCharBuffer.argtypes              = [H];                                         lib.DestroyCharBuffer.restype              = None
    lib.GetSpectrum.argtypes                    = [H, c_uint32, POINTER(c_float), POINTER(c_float)]; lib.GetSpectrum.restype                = None
    lib.GetSpectra.argtypes                     = [H, POINTER(c_uint32), c_uint32, POINTER(c_float)]; lib.GetSpectra.restype                = None
    lib.GetIntensities.argtypes                 = [H, c_uint32, POINTER(c_float)];             lib.GetIntensities.restype                  = None
    lib.SetSmoothing.argtypes                   = [H, c_char_p, c_uint32];                     lib.SetSmoothing.restype                   = None
    lib.SetBaselineCorrection.argtypes          = [H, c_char_p, c_uint32];                     lib.SetBaselineCorrection.restype          = None
    lib.SetNormalization.argtypes               = [H, c_char_p];                               lib.SetNormalization.restype               = None
    lib.SetIntensityTransformation.argtypes     = [H, c_char_p];                               lib.SetIntensityTransformation.restype     = None
    lib.SetPooling.argtypes                     = [H, c_char_p];                               lib.SetPooling.restype                     = None
    lib.SetTolerance.argtypes                   = [H, c_float];                                lib.SetTolerance.restype                   = None
    lib.GetTolerance.argtypes                   = [H];                                         lib.GetTolerance.restype                   = c_float
    lib.SetImageNormalization.argtypes          = [H, c_char_p];                               lib.SetImageNormalization.restype          = None
    lib.SetImageSmoothing.argtypes              = [H, c_char_p];                               lib.SetImageSmoothing.restype              = None
    lib.Update.argtypes                         = [H];                                         lib.Update.restype                         = None

def load_m2aia_library():
    search_path = pathlib.Path(os.environ["M2AIA_PATH"])

    if "Windows" in platform.platform():
        os.add_dll_directory(search_path)
        return ctypes.cdll.LoadLibrary("M2aiaCore.dll")

    if "Darwin" in platform.platform():
        raise ImportError("macOS/Darwin based systems are currently not tested.")

    # For development installs pointing at a raw M2aia build, prepend the search path
    # so the linker finds all bundled .so files. For PyPI wheels, auditwheel has already
    # rewritten the RPATH so this is a no-op.
    search_str = str(search_path.resolve())
    existing = os.environ.get("LD_LIBRARY_PATH", "")
    if search_str not in existing.split(":"):
        os.environ["LD_LIBRARY_PATH"] = search_str + (":" + existing if existing else "")

    return ctypes.CDLL(str((search_path / "libM2aiaCore.so").resolve()), mode=ctypes.RTLD_GLOBAL)
    
    


def get_library():
    global _lib
    if _lib is not None:
        return _lib
    try:
        _lib = load_m2aia_library()
        _configure_signatures(_lib)
        return _lib
    except SystemExit:
        pass
    except ImportError as e:
        print(e)
        raise ImportError(
"""Could not find the required M2aia libraries.
pyM2aia requires a valid M2aia installation/build. 
Go to https://m2aia.github.io/m2aia and download the latest version of M2aia. 
Then, follow the setup procedure for pyM2aia on https://github.com/m2aia/pym2aia.
"""
                        ,name="m2aia")
