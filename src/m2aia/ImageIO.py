from enum import Enum
from typing import List, Dict
from ctypes import create_string_buffer, c_void_p, c_uint32, c_char_p, c_double, c_float, c_ushort, POINTER  # noqa: F401 (used in type annotations)
import pathlib
import numpy as np
import SimpleITK as sitk

from .Library import get_library


class m2Normalization(str, Enum):
    NONE     = "None"
    TIC      = "TIC"
    Sum      = "Sum"
    Mean     = "Mean"
    Max      = "Max"
    RMS      = "RMS"
    Internal = "Internal"
    External = "External"

class m2Smoothing(str, Enum):
    NONE          = "None"
    SavitzkyGolay = "SavitzkyGolay"
    Gaussian      = "Gaussian"

class m2Pooling(str, Enum):
    NONE    = "None"
    Mean    = "Mean"
    Median  = "Median"
    Maximum = "Maximum"
    Sum     = "Sum"

class m2BaselineCorrection(str, Enum):
    NONE   = "None"
    TopHat = "TopHat"
    Median = "Median"

class m2IntensityTransformation(str, Enum):
    NONE       = "None"
    Log2       = "Log2"
    Log10      = "Log10"
    SquareRoot = "SquareRoot"


class m2SpectrumFormat(str, Enum):
    """Bitmask enum describing the storage format of spectra in an imzML file.
    Maps to m2::SpectrumFormat in m2CoreCommon.h.
    """
    NONE              = "None"
    Profile           = "Profile"
    Centroid          = "Centroid"
    Continuous        = "Continuous"
    Processed         = "Processed"
    ContinuousProfile = "ContinuousProfile"
    ProcessedProfile  = "ProcessedProfile"
    ContinuousCentroid = "ContinuousCentroid"
    ProcessedCentroid  = "ProcessedCentroid"

    @classmethod
    def from_type_id(cls, type_id: int) -> "m2SpectrumFormat":
        _map = {0:cls.NONE, 1:cls.Profile, 2:cls.Centroid, 4:cls.Continuous,
                8:cls.Processed, 21:cls.ContinuousProfile, 41:cls.ProcessedProfile,
                70:cls.ContinuousCentroid, 138:cls.ProcessedCentroid}
        return _map.get(type_id, cls.NONE)


class m2ImageNormalization(str, Enum):
    """Spatial (image-level) normalization strategies.
    Maps to m2::ImageNormalizationStrategyType in m2SignalCommon.h.
    """
    NONE          = "None"
    MinMax        = "MinMax"
    zScore        = "zScore"
    ParetoScaling = "ParetoScaling"
    RangeScaling  = "RangeScaling"
    VastScaling   = "VastScaling"


class m2ImageSmoothing(str, Enum):
    """Spatial (image-level) smoothing strategies.
    Maps to m2::ImageSmoothingStrategyType in m2SignalCommon.h.
    """
    NONE    = "None"
    Median  = "Median"
    Gaussian = "Gaussian"

# Backward-compatible aliases (keep old names working)
m2NormalizationNone     = m2Normalization.NONE
m2NormalizationTIC      = m2Normalization.TIC
m2NormalizationSum      = m2Normalization.Sum
m2NormalizationMean     = m2Normalization.Mean
m2NormalizationMax      = m2Normalization.Max
m2NormalizationRMS      = m2Normalization.RMS
m2NormalizationInternal = m2Normalization.Internal
m2NormalizationExternal = m2Normalization.External

m2SmoothingSavitzkyGolay = m2Smoothing.SavitzkyGolay
m2SmoothingGaussian      = m2Smoothing.Gaussian

m2PoolingMean    = m2Pooling.Mean
m2PoolingMedian  = m2Pooling.Median
m2PoolingMaximum = m2Pooling.Maximum
m2PoolingSum     = m2Pooling.Sum
m2PoolingNone    = m2Pooling.NONE

m2BaselineCorrectionTopHat = m2BaselineCorrection.TopHat
m2BaselineCorrectionMedian = m2BaselineCorrection.Median

m2IntensityTransformationLog2       = m2IntensityTransformation.Log2
m2IntensityTransformationLog10      = m2IntensityTransformation.Log10
m2IntensityTransformationSquareRoot = m2IntensityTransformation.SquareRoot



class ImzMLReader(object):
    ''' Wrapper class for M2aia's imzML reader https://github.com/m2aia/m2aia.
    
    Complete processing examples with focus on deep learning can be found on https://github.com/m2aia/pym2aia-examples 
    
    Example usage::

        import m2aia as m2

        I = m2.ImzMLReader("path/to/imzMl/file.imzML")
        I.SetNormalization(m2.m2NormalizationTIC)
        I.SetIntensityTransformation(m2.m2IntensityTransformationSquareRoot)
        ys_2 = I.GetMeanSpectrum()
        i_2 = I.GetArray(imz, 75)

    '''
    def __init__(self, imzML_path, baseline_correction: m2BaselineCorrection = "None",
                 baseline_correction_half_window_size: int = 50,
                 normalization: m2Normalization = "None",
                 smoothing: m2Smoothing = "None",
                 smoothing_half_window_size: int = 2,
                 intensity_transformation: m2IntensityTransformation = "None",
                 pooling: m2Pooling = m2PoolingMaximum):

        self.lib = get_library()

        self.x_axis = None

        self.imzML_path = imzML_path
        self.handle = None
        self.spectrum_type_id = None


        self.baseline_correction = baseline_correction
        self.baseline_correction_hws = baseline_correction_half_window_size
        self.smoothing = smoothing
        self.smoothing_hws = smoothing_half_window_size
        self.normalization = normalization
        self.intensity_transformation = intensity_transformation
        self.pooling = pooling
        self.image_normalization = m2ImageNormalization.NONE
        self.image_smoothing = m2ImageSmoothing.NONE


        # Read and initialize the image by creating a handle
        self.Load()


    def __del__(self):
        if self.handle is not None:
            self.lib.DestroyImageHandle(self.handle)
            self.handle = None

    def Load(self):
        
        if self.handle is not None:
            self.lib.DestroyImageHandle(self.handle)

        cPath = create_string_buffer(self.imzML_path.encode())
        self.handle = self.lib.CreateImageHandle(cPath)

        self.SetBaselineCorrection(self.baseline_correction, self.baseline_correction_hws)
        self.SetSmoothing(self.smoothing, self.smoothing_hws)
        self.SetNormalization(self.normalization)
        self.SetIntensityTransformation(self.intensity_transformation)
        self.SetPooling(self.pooling)
        self.SetImageNormalization(self.image_normalization)
        self.SetImageSmoothing(self.image_smoothing)

        self.lib.Update(self.handle)

        self.depth = self.lib.GetXAxisDepth(self.handle)

        # mean overview spectrum
        self.mean_spectrum = np.zeros(self.depth, dtype=np.float64)
        self.lib.GetMeanSpectrum(self.handle, self.mean_spectrum.ctypes.data_as(
            POINTER(c_double)))

        # max overview spectrum
        self.max_spectrum = np.zeros(self.depth, dtype=np.float64)
        self.lib.GetMaxSpectrum(self.handle, self.max_spectrum.ctypes.data_as(
            POINTER(c_double)))

        self.number_of_spectra = self.lib.GetNumberOfSpectra(self.handle)
        self.shape = self.GetShape()

        self.spectrum_type_id = self.lib.GetSpectrumType(self.handle)
        
        # XAxis
        self.x_axis = np.zeros(self.depth, dtype=np.float64)
        self.lib.GetXAxis(self.handle, self.x_axis.ctypes.data_as(
            POINTER(c_double)))

        

    def path(self) -> pathlib.Path:
        '''Absolute path to the referenced imzML'''
        return pathlib.Path(self.imzML_path)

    def dir(self) -> pathlib.Path:
        '''Absolute path to directory containing the referenced imzML '''
        return self.path().parent

    def name(self) -> str:
        '''Name (including file ending) of the given imzML'''
        return self.path().name


    def CheckHandle(self):
        ''' Check if the handle was initialized properly.
        '''
        if self.handle is None:
            raise ReferenceError(
                "Please initialize image handle by providing a valid file name")

    def GetParametersAsFormattedString(self):
        '''Transform signal processing parameters into a fomatted string representation.'''
        s = str()
        s += f"(baseline-correction {self.baseline_correction})\n"
        s += f"(baseline-correction-hw {self.baseline_correction_hws})\n"
        s += f"(smoothing {self.smoothing})\n"
        s += f"(smoothing-hw {self.smoothing_hws})\n"
        s += f"(normalization {self.normalization})\n"
        s += f"(pooling {self.pooling})\n"
        s += f"(transform {self.intensity_transformation})\n"
        s += f"(image-normalization {self.image_normalization})\n"
        s += f"(image-smoothing {self.image_smoothing})\n"
        return s

    def SetSmoothing(self, strategy: m2Smoothing, half_window_size=2):
        '''Set the spectrum smoothing strategy.

        :param strategy: Set the smoothing strategy using one of the m2Smoothing literals.
        :param half_window_size: 2*half_window_size + 1 spectrum points used for smoothing.
        '''
        
        self.smoothing = strategy
        self.smoothing_hws = half_window_size
        arg = create_string_buffer(strategy.encode())
        self.lib.SetSmoothing(self.handle, arg, half_window_size)


    def SetIntensityTransformation(self, strategy: m2IntensityTransformation):
        '''
        Set the intensity transformation strategy.

        :param strategy: m2IntensityTransformation
            Set the intensity transformation strategy using one of the m2IntensityTransformation literals.
        '''
        self.intensity_transformation = strategy
        arg = create_string_buffer(strategy.encode())
        self.lib.SetIntensityTransformation(self.handle, arg)


    def SetBaselineCorrection(self, strategy: m2BaselineCorrection, half_window_size=50):
        '''Set the baseline correction strategy.

        :param strategy: Set the basline correction strategy using one of the m2BaselineCorrection literals.
        :param half_window_size: 2*half_window_size + 1 spectrum points are used for BaselineCorrection.
        '''
        self.baseline_correction = strategy
        self.baseline_correction_hws = half_window_size
        arg = create_string_buffer(strategy.encode())
        self.lib.SetBaselineCorrection(self.handle, arg, half_window_size)

    def SetNormalization(self, strategy: m2Normalization):
        '''
        Set the normalization strategy.

        :param strategy: m2Normalization
            Set the normalization strategy using one of the m2Normalization literals.
        '''
        self.normalization = strategy
        arg = create_string_buffer(strategy.encode())
        self.lib.SetNormalization(self.handle, arg)

    def SetPooling(self, strategy: m2Pooling):
        '''
        Set the pooling strategy.

        :param strategy: m2Pooling
            Set the pooling strategy using one of the m2Pooling literals.
        '''
        self.pooling = strategy
        arg = create_string_buffer(strategy.encode())
        self.lib.SetPooling(self.handle, arg)

    def SetImageNormalization(self, strategy: m2ImageNormalization):
        '''Set the spatial (image-level) normalization strategy applied after ion image generation.

        :param strategy: m2ImageNormalization
            One of: None, MinMax, zScore, ParetoScaling, RangeScaling, VastScaling.
        '''
        self.image_normalization = strategy
        arg = create_string_buffer(strategy.encode())
        self.lib.SetImageNormalization(self.handle, arg)

    def SetImageSmoothing(self, strategy: m2ImageSmoothing):
        '''Set the spatial (image-level) smoothing strategy applied after ion image generation.

        :param strategy: m2ImageSmoothing
            One of: None, Median, Gaussian.
        '''
        self.image_smoothing = strategy
        arg = create_string_buffer(strategy.encode())
        self.lib.SetImageSmoothing(self.handle, arg)

    def SetTolerance(self, tol: np.float32):
        '''
        Set the tolerance value.

        :param tol: np.float32
            The tolerance value to be set.
        '''
        self.lib.SetTolerance(self.handle, tol)

    def GetTolerance(self) -> np.float32:
        '''
        Get the current tolerance value.

        :return: np.float32
            The current tolerance value.
        '''
        return self.lib.GetTolerance(self.handle)


    def GetYDataType(self):
        '''Return the intensity data type defined in the imzML file.

        :return: np.float32 or np.float64; if not defined return None
        '''
        self.CheckHandle()
        size_in_bytes = self.lib.GetYDataTypeSizeInBytes(self.handle)
        if size_in_bytes == 4:
            return np.float32
        elif size_in_bytes == 8:
            return np.float64
        else:
            return None

    def GetShape(self) -> np.array:
        '''Get the shape of the image.

        :return: numpy array of size [3] for the x,y,z image dimensions (in number of pixels).
        '''
        self.CheckHandle()
        shape = np.zeros((3), dtype=np.int32)
        self.lib.GetSize(self.handle, shape.ctypes.data_as(
            POINTER(c_uint32)))
        return shape

    def GetSpacing(self) -> np.array:
        '''Get the pixel spacing of the image

        :return: numpy array of size [3] and dtype=np.float64 for the pixel size in x,y,z dimension (in millimeter).
        '''
        self.CheckHandle()
        spacing = np.zeros((3), dtype=np.float64)
        self.lib.GetSpacing(self.handle, spacing.ctypes.data_as(
            POINTER(c_double)))
        return spacing

    def GetSpectrumPosition(self, id) -> np.array:
        '''Get the image index position for a given spectrum id.

        :param id: the id of a spectrum (may be different to the ids given in the imzML).

        :return: Position in index coordinates as numpy array of size [3] and dtype=np.int32.
        '''

        self.CheckHandle()
        pos = np.zeros((3), dtype=np.int32)
        self.lib.GetSpectrumPosition(self.handle, id, pos.ctypes.data_as(
            POINTER(c_uint32)))
        return pos

    def GetMetaData(self) -> Dict[str,str]:
        '''Returns a dictionary of all meta data information retrieved by m2aia.

        :return: List of strings of meta data.
        '''
        self.CheckHandle()
        separator = '\t'
        data = self.lib.GetMetaDataDictionary(self.handle)
        lines = [f.strip() for f in data.decode("utf-8").split('\n') if len(f.strip()) > 0]
        return { line.split(separator)[0]:line.split(separator)[1]  if len(line.split(separator)) > 0  else "true" for line in lines}

    def GetOrigin(self) -> np.array:
        '''Get the image origin.

        :return: The origin in world coordinates of the image as numpy array of size [3] and dtype=np.float64.
        '''
        self.CheckHandle()
        origin = np.zeros((3), dtype=np.float64)
        self.lib.GetOrigin(self.handle, origin.ctypes.data_as(
            POINTER(c_double)))
        return origin

    def GetMaskArray(self) -> np.ndarray:
        ''' Get the mask image data as numpy array.
        The binary mask indicates valid spectra (pixel value >= 1) and background (pixel value == 0).

        :return: Numpy array of size [x,y,z] with dtype=np.ushort.
        '''
        self.CheckHandle()
        slice = np.zeros(self.GetShape()[::-1], dtype=np.ushort)
        self.lib.GetMaskArray(
            self.handle, slice.ctypes.data_as(POINTER(c_ushort)))
        return slice

    def GetMaskImage(self) -> sitk.Image:
        ''' Get the mask image data as parameterized SimpleITK.Image.
        The pixel values indicate valid spectra (pixel value >= 1) and background (pixel value == 0).

        :return: sitk.Image of size [x,y,z] with dtype=np.ushort.
        '''
        self.CheckHandle()
        slice = self.GetMaskArray()
        spacing = self.GetSpacing()
        origin = self.GetOrigin()
        I = sitk.GetImageFromArray(slice)
        I.SetSpacing(spacing)
        I.SetOrigin(origin)
        return I

    def GetIndexArray(self) -> np.ndarray:
        ''' Get the index image data as numpy array.
        The pixel values are the spectrum IDs starting with 0. Use the mask array to identify valid spectrum IDs.

        Access valid spectrum IDs:: 
        
            indexImage = I.GetIndexArray()
            maskImage = I.GetMaskArray()
            validIndices = indexImage[maskImage > 0]

        :return: Numpy array of size [x,y,z] with dtype=np.uint32.
        '''
        self.CheckHandle()
        slice = np.zeros(self.GetShape()[::-1], dtype=np.uint32)
        self.lib.GetIndexArray(
            self.handle, slice.ctypes.data_as(POINTER(c_uint32)))
        return slice

    def GetIndexImage(self):
        ''' Get the index image data as parameterized SimpleITK.Image.
            This method calls :func:`~m2aia.ImageIO.GetIndexArray`

        :return: sitk.Image of size [x,y,z] with dtype=np.uint32.
        '''
        self.CheckHandle()
        slice = self.GetIndexArray()
        spacing = self.GetSpacing()
        origin = self.GetOrigin()
        I = sitk.GetImageFromArray(slice)
        I.SetSpacing(spacing)
        I.SetOrigin(origin)
        return I
    
    def GetNormalizationArray(self, type) -> np.ndarray:
        ''' Get a normalization image data as numpy array.

        :return: Numpy array of size [x,y,z] with dtype=np.float64.
        '''
        self.CheckHandle()
        arg = create_string_buffer(type.encode())
        
        image = np.zeros(self.GetShape()[::-1], dtype=np.float64)
        self.lib.GetNormalizationArray(
            self.handle, arg, image.ctypes.data_as(POINTER(c_double)))
        return image

    def GetNormalizationImage(self, type) -> sitk.Image:
        ''' Get a normalization image data as parameterized SimpleITK.Image.
        
        :return: sitk.Image of size [x,y,z] with dtype=np.float64.
        '''
        self.CheckHandle()
        slice = self.GetNormalizationArray(type)
        spacing = self.GetSpacing()
        origin = self.GetOrigin()
        I = sitk.GetImageFromArray(slice)
        I.SetSpacing(spacing)
        I.SetOrigin(origin)
        return I

    def GetArray(self, center, tol, dtype=np.float32, squeeze: bool = False) -> np.ndarray:
        ''' Get the (ion) image data as numpy array.
        The pixel values are the pooled intensities (ie. pooling strategies like 
        the 'Mean', 'Median', 'Maximum', or 'Sum') in the interval [center-tol, center+tol] of the spectra.

        :return: Numpy array of size [x,y,z] with dtype=dtype.

        :param center: value on the x axis.
        :param tol: tolerance for query points on the x axis around the center.
        :param dtype: array element type [np.float32, np.float64].
        :param squeeze: Remove all dimensions if any is smaller or equals 1.

        :raises:
            TypeError: Image pixel type is not one of [np.float32, np.float64]
        '''
        self.CheckHandle()
        xs = self.GetXAxis()

        if center < np.min(xs) or center > np.max(xs):
            raise ValueError("Center is out of x-axis range!", center, tol, dtype, squeeze)

        slice = np.zeros(self.GetShape()[::-1], dtype=dtype)
        if dtype == np.float32:
            self.lib.GetImageArrayFloat32(
                self.handle, center, tol, slice.ctypes.data_as(POINTER(c_float)))
        elif dtype == np.float64:
            self.lib.GetImageArrayFloat64(
                self.handle, center, tol, slice.ctypes.data_as(POINTER(c_double)))
        else:
            raise TypeError(
                "Image pixel type is not one of [np.float32, np.float64].")

        if squeeze:
            return np.squeeze(slice)
        return slice

    def GetImage(self, center, tol, dtype=np.float32) -> sitk.Image:
        ''' Get the (ion) image data as parameterized SimpleITK.Image.
        
        :meth:`m2aia.ImzMLReader.GetArray`

        :return: sitk.Image of size [x,y,z] with dtype=dtype.

        :param center: value on the x axis.
        :param tol: tolerance for query points on the x axis around the center.
        :param dtype: array element type [np.float32, np.float64].
        :param squeeze: Remove all dimensions if any is smaller or equals 1.

        :raises:
            TypeError: Image pixel type is not one of [np.float32, np.float64]
        '''
        array = self.GetArray(center, tol, dtype)
        spacing = self.GetSpacing()
        origin = self.GetOrigin()
        I = sitk.GetImageFromArray(array)
        I.SetSpacing(spacing)
        I.SetOrigin(origin)
        return I

    def GetMeanSpectrum(self) -> np.array:
        ''' Get the overview spectrum (mean over all spectra).

        :return: np.array with mean intensity values of all spectra.
        '''
        self.CheckHandle()
        return self.mean_spectrum

    def GetMaxSpectrum(self) -> np.array:
        ''' Get the overview spectrum (max over all spectra).

        :return: np.array with maximum intensity values of all spectra.
        '''
        self.CheckHandle()
        return self.max_spectrum

    def GetXAxis(self) -> np.array:
        ''' Get the x axis values (i.e. m/z values on the x axis).

        :return: np.array
        '''
        self.CheckHandle()
        return self.x_axis

    def GetXAxisDepth(self) -> int:
        ''' Get the size of the x axis. For processed imzML files, 
        this value is the number of bins used to represent the x-axis.

        :return: Number of x values.
        '''
        self.CheckHandle()
        return self.depth

    def GetSpectrumDepth(self, id) -> int:
        ''' Get the size of the x axis for a specific spectrum of the image. 
        This method is helpful for processed (centroid) imzML files. For continuous
        (centroid/profile) imzML files use GetXAxisDepth(self).

        :param id: Id of a spectrum in the image.

        :return: Number of x values.
        '''
        self.CheckHandle()
        depth = self.lib.GetSpectrumDepth(self.handle, id)
        if depth <= 0:
            raise RuntimeError("Spectrum depth can not be 0!")
        return depth

    def GetSpectrumType(self) -> str:
        '''Get the imzML type, i.e. continuous/processed profile/centroid.
        
        :return: The type of the imzML as string.
        '''
        self.CheckHandle()
        return m2SpectrumFormat.from_type_id(self.spectrum_type_id)

    def GetSizeInBytesOfYAxisType(self) -> int:
        '''Get number of bytes used to store the intensity values.
        
        :return: The number of bytes.
        '''
        self.CheckHandle()
        return self.lib.GetSizeInBytesOfYAxisType(self.handle)

    def GetSpectrum(self, index) -> List[np.array]:
        ''' Query the x-axis (xs) and y-axis (ys) values for a given spectrum id.

        :param index: Id of a spectrum in the image.
        
        :return: A list of two np.array elements [xs,ys]. xs = x-values; ys = y-values.

        :raises: IndexError: if index is not in the range of valid spectra indices [0,self.number_of_spectra-1].
        '''
        self.CheckHandle()
        if index < 0 or index >= self.number_of_spectra:
            raise IndexError(
                "Index " + str(index) + " out of range of valid spectrum indices [0," + str(self.number_of_spectra - 1) + "] ")

        depth = self.GetSpectrumDepth(index)
        xs = np.zeros(depth, dtype=np.float32)
        ys = np.zeros(depth, dtype=np.float32)

        self.lib.GetSpectrum(self.handle, index, xs.ctypes.data_as(
            POINTER(c_float)), ys.ctypes.data_as(
            POINTER(c_float)))

        return [xs, ys]

    def GetIntensities(self, index, ys = None) -> np.array:
        ''' Query the y-axis (ys) values for a given spectrum id.

        :param index: Id of a spectrum in the image.
        :param ys: By passing a np.array (dtype=np.float32) from external, this np.array can 
            be reused and do not require an extra memory allocation. Otherwise
            a new array is created.
        
        :return: A list of two np.array elements [xs,ys]. xs = x-values; ys = y-values.

        :raises: 
            IndexError: if index is not in the range of valid spectra indices [0,self.number_of_spectra-1].
            TypeError: if the ImzML file format is not continuous profile/centroid!

        '''
        self.CheckHandle()
        if index < 0 or index >= self.number_of_spectra:
            raise IndexError(
                "Index " + str(index) + " out of range of valid spectrum indices [0," + str(self.number_of_spectra - 1) + "] ")

        if not 'Continuous' in self.GetSpectrumType():
            raise TypeError(
                f"The ImzML format has to be in Continuous format! Current format ist {self.GetSpectrumType()}!\nUse GetSpectrum(...) instead.")

        if ys is None:
            ys = np.zeros(self.depth, dtype=np.float32)
        
        if ys.shape[0] != self.depth:
            ys = np.resize(ys, (self.depth))
        
        self.lib.GetIntensities(
            self.handle, index, ys.ctypes.data_as(POINTER(c_float)))
        return ys

    def GetSpectra(self, indices: List[int]) -> np.ndarray:
        ''' Query a set of intensities by a list of indices.
        Only continuous imzML files.

        :param indices: List of Ids of spectra in the image.

        :return: a np.ndarray of shape [len(indices), self.depth].
        
        :raises: 
            IndexError: if index is not in the range of valid spectra indices [0,self.number_of_spectra-1].
            TypeError: if the ImzML file format is not continuous profile/centroid!
        '''
        self.CheckHandle()
        for index in indices:
            if index < 0 or index >= self.number_of_spectra:
                raise IndexError(
                    "Index " + str(index) + " out of range of valid spectrum indices [0," + str(self.number_of_spectra - 1) + "] ")

        if not 'Continuous' in self.GetSpectrumType():
            raise TypeError(
                f"The ImzML format has to be in Continuous format! Current format ist {self.GetSpectrumType()}!\nUse GetSpectrum(...) instead.")

        batch_size = len(indices)
        ys_batch = np.zeros([batch_size, self.depth], dtype=np.float32)
        idx = np.array(indices, dtype=np.uint32)

        self.lib.GetSpectra(self.handle, idx.ctypes.data_as(
            POINTER(c_uint32)), batch_size, ys_batch.ctypes.data_as(
            POINTER(c_float)))

        return ys_batch

    def GetNumberOfSpectra(self) -> int:
        '''Get the number of valid spectra in the image.
        This can be used to iterate over all spectra in the image using
        a for loop:: 
        
            for i in range(GetNumberOfSpectra()):
                xs, ys = reader.GetSpectrum(i)
                
        :return: Number of valid spectra.
        '''
        self.CheckHandle()
        return self.number_of_spectra

    def SpectrumIterator(self):
        '''Create a spectrum iterator/generator, yielding all valid spectra.
        This can be used to iterate over all spectra in the image using
        a for loop:: 
        
            for i,xs,ys in reader.SpectrumIterator():
                ...
                
        :return: a triplet with (i=spectrum-id, xs=x-values, ys=y-values)
        '''
        self.CheckHandle()
        for i in range(self.number_of_spectra):
            xs, ys = self.GetSpectrum(i)
            yield i, xs, ys

    def SpectrumRandomBatchIterator(self, batch_size):
        '''Create a spectrum batch iterator/generator, yielding a batch of ys-values of spectra in a random order with repetitions.
        
        Example:: 
        
            for ys_batch in reader.SpectrumRandomBatchIterator(batch_size = N):
                ...
                
        :return: a np.array as batch of intensities with shape [batch_size, self.depth]
        '''
        self.CheckHandle()
        while (True):
            ids = np.random.randint(
                0, self.number_of_spectra, batch_size)
            data = np.array([self.GetSpectrum(int(i))[1] for i in ids])
            yield data
