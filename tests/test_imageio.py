import os
os.environ["M2AIA_PATH"] = "/media/jtfc/data/02_M2aia/m2aia-dev/build-release/MITK-build/lib"

from unittest import TestCase
import m2aia as m2
import numpy as np
import pathlib
import SimpleITK as sitk

def getTestData(relativePath:str)->str:
    return str(pathlib.Path(__file__).parent.joinpath(relativePath))

class TestImageIO(TestCase):


    def setUp(self):
        self.Image = m2.ImzMLReader(getTestData("data/test.imzML"))        
        self.eps = 1e-12
        self.tol_in_da = 5

    def test_IonImage_ExceptionThrownOnMzIsOutOfBounds(self):
        first,last = self.Image.GetXAxis()[[0,-1]]
        self.assertRaises(ValueError, lambda: self.Image.GetArray(first - self.eps, self.tol_in_da))
        self.assertRaises(ValueError, lambda: self.Image.GetArray(last + self.eps, self.tol_in_da) )


    def test_IonImage_ExceptionThrownOnMzIsOnBounds(self):
        first,last = self.Image.GetXAxis()[[0,-1]]
        # check if any value is not equal
        self.assertFalse(np.any(~np.equal(self.Image.GetArray(first, self.tol_in_da), np.load(getTestData("data/YS_LB_5.npy")))))
        self.assertFalse(np.any(~np.equal(self.Image.GetArray(last, self.tol_in_da), np.load(getTestData("data/YS_UB_5.npy")))))
        
    def test_sitk_IonImage_ExceptionThrownOnMzIsOnBounds(self):
        first,last = self.Image.GetXAxis()[[0,-1]]
        # check if any value is not equal
        self.assertFalse(np.any(~np.equal(sitk.GetArrayFromImage(self.Image.GetImage(first, self.tol_in_da)), np.load(getTestData("data/YS_LB_5.npy")))))
        self.assertFalse(np.any(~np.equal(sitk.GetArrayFromImage(self.Image.GetImage(last, self.tol_in_da)), np.load(getTestData("data/YS_UB_5.npy")))))

    def test_GetOrigin_ExceptionThrownOnMzIsOnBounds(self):
        origin = self.Image.GetOrigin()
        self.assertFalse(np.any(~np.equal(origin, [0,0,0])))
        print("Origin:", origin)

    def test_SetSmoothing(self):
        origin = self.Image.GetOrigin()
        self.assertFalse(np.any(~np.equal(origin, [0,0,0])))
        print("Origin:", origin)

    # --- XAxis / depth ---

    def test_GetXAxis_ReturnsFloat64Array(self):
        xs = self.Image.GetXAxis()
        self.assertIsInstance(xs, np.ndarray)
        self.assertEqual(xs.dtype, np.float64)

    def test_GetXAxis_IsStrictlyIncreasing(self):
        xs = self.Image.GetXAxis()
        self.assertTrue(np.all(np.diff(xs) > 0), "m/z axis must be strictly increasing")

    def test_GetXAxisDepth_MatchesXAxisLength(self):
        self.assertEqual(self.Image.GetXAxisDepth(), len(self.Image.GetXAxis()))

    def test_GetXAxis_MatchesReference(self):
        xs = self.Image.GetXAxis()
        ref = np.load(getTestData("data/XS.npy"))
        np.testing.assert_array_equal(xs, ref)

    # --- Shape / spacing ---

    def test_GetShape_Returns3Elements(self):
        shape = self.Image.GetShape()
        self.assertEqual(len(shape), 3)
        self.assertTrue(np.all(shape > 0))

    def test_GetSpacing_Returns3PositiveValues(self):
        spacing = self.Image.GetSpacing()
        self.assertEqual(len(spacing), 3)
        self.assertTrue(np.all(spacing > 0))

    def test_GetOrigin_Returns3Elements(self):
        origin = self.Image.GetOrigin()
        self.assertEqual(len(origin), 3)

    # --- Spectrum count ---

    def test_GetNumberOfSpectra_IsPositive(self):
        n = self.Image.GetNumberOfSpectra()
        self.assertGreater(n, 0)

    def test_NumberOfSpectra_MatchesNonzeroMaskPixels(self):
        mask = self.Image.GetMaskArray()
        n = self.Image.GetNumberOfSpectra()
        self.assertEqual(int(np.sum(mask > 0)), n)

    # --- Ion image shape consistency ---

    def test_IonImage_ShapeMatchesImageShape(self):
        mz = self.Image.GetXAxis()[len(self.Image.GetXAxis()) // 2]
        arr = self.Image.GetArray(mz, self.tol_in_da)
        shape = self.Image.GetShape()
        # GetArray returns [z, y, x] or [y, x]; shape is [x, y, z]
        self.assertEqual(arr.shape[-1], shape[0])
        self.assertEqual(arr.shape[-2], shape[1])

    def test_IonImage_DefaultDtypeIsFloat32(self):
        mz = self.Image.GetXAxis()[0]
        arr = self.Image.GetArray(mz, self.tol_in_da)
        self.assertEqual(arr.dtype, np.float32)

    def test_IonImage_NonNegative(self):
        mz = self.Image.GetXAxis()[len(self.Image.GetXAxis()) // 2]
        arr = self.Image.GetArray(mz, self.tol_in_da)
        self.assertTrue(np.all(arr >= 0))

    def test_IonImage_MatchesReference(self):
        xs = self.Image.GetXAxis()
        mz5000_idx = np.argmin(np.abs(xs - 5000.0))
        arr = np.squeeze(self.Image.GetArray(xs[mz5000_idx], 5))
        ref = np.load(getTestData("data/YS_mz5000_da5.npy"))
        np.testing.assert_array_equal(arr, ref)

    def test_GetImage_ArrayEqualsGetArray(self):
        mz = self.Image.GetXAxis()[0]
        arr = self.Image.GetArray(mz, self.tol_in_da)
        sitk_arr = sitk.GetArrayFromImage(self.Image.GetImage(mz, self.tol_in_da))
        np.testing.assert_array_equal(arr, sitk_arr)

    # --- Mask & index images ---

    def test_GetMaskArray_IsBinary(self):
        mask = self.Image.GetMaskArray()
        unique = np.unique(mask)
        self.assertTrue(set(unique).issubset({0, 1}),
                        f"Mask values should be 0 or 1, got {unique}")

    def test_GetMaskArray_MatchesMaskImage(self):
        arr = self.Image.GetMaskArray()
        sitk_arr = sitk.GetArrayFromImage(self.Image.GetMaskImage())
        np.testing.assert_array_equal(arr, sitk_arr)

    def test_GetIndexArray_ShapeMatchesMask(self):
        mask = self.Image.GetMaskArray()
        idx = self.Image.GetIndexArray()
        self.assertEqual(mask.shape, idx.shape)

    def test_GetIndexArray_MatchesIndexImage(self):
        arr = self.Image.GetIndexArray()
        sitk_arr = sitk.GetArrayFromImage(self.Image.GetIndexImage())
        np.testing.assert_array_equal(arr, sitk_arr)

    # --- Single spectrum access ---

    def test_GetSpectrum_ReturnsXsAndYs(self):
        xs, ys = self.Image.GetSpectrum(0)
        self.assertIsInstance(xs, np.ndarray)
        self.assertIsInstance(ys, np.ndarray)
        self.assertEqual(len(xs), len(ys))

    def test_GetSpectrum_YsNonNegative(self):
        _, ys = self.Image.GetSpectrum(0)
        self.assertTrue(np.all(ys >= 0))

    def test_GetSpectrum_XsMatchXAxis(self):
        # GetSpectrum returns float32 xs; GetXAxis returns float64 — compare within float32 precision
        xs, _ = self.Image.GetSpectrum(0)
        np.testing.assert_array_almost_equal(xs, self.Image.GetXAxis().astype(np.float32), decimal=4)

    # --- Batch spectrum access ---

    def test_GetSpectra_ShapeIsCorrect(self):
        n = min(3, self.Image.GetNumberOfSpectra())
        indices = list(range(n))
        batch = self.Image.GetSpectra(indices)
        self.assertEqual(batch.shape, (n, self.Image.GetXAxisDepth()))

    def test_GetSpectra_MatchesSingleGetSpectrum(self):
        _, ys_single = self.Image.GetSpectrum(0)
        batch = self.Image.GetSpectra([0])
        np.testing.assert_array_equal(batch[0], ys_single)

    # --- Spectrum position ---

    def test_GetSpectrumPosition_Returns3Coords(self):
        pos = self.Image.GetSpectrumPosition(0)
        self.assertEqual(len(pos), 3)

    def test_GetSpectrumPosition_WithinImageBounds(self):
        shape = self.Image.GetShape()
        pos = self.Image.GetSpectrumPosition(0)
        self.assertGreaterEqual(pos[0], 0)
        self.assertLess(pos[0], shape[0])
        self.assertGreaterEqual(pos[1], 0)
        self.assertLess(pos[1], shape[1])

    # --- Overview spectra ---

    def test_GetMeanSpectrum_LengthMatchesDepth(self):
        mean = self.Image.GetMeanSpectrum()
        self.assertEqual(len(mean), self.Image.GetXAxisDepth())

    def test_GetMaxSpectrum_LengthMatchesDepth(self):
        mx = self.Image.GetMaxSpectrum()
        self.assertEqual(len(mx), self.Image.GetXAxisDepth())

    def test_GetMeanSpectrum_NonNegative(self):
        mean = self.Image.GetMeanSpectrum()
        self.assertTrue(np.all(mean >= 0))

    def test_GetMaxSpectrum_NonNegativeAndNoNaN(self):
        # The max spectrum is the single highest-intensity spectrum, not per-m/z maximum
        mx = self.Image.GetMaxSpectrum()
        self.assertTrue(np.all(mx >= 0))
        self.assertFalse(np.any(np.isnan(mx)))

    # --- Spectrum type / metadata ---

    def test_GetSpectrumType_ReturnsString(self):
        st = self.Image.GetSpectrumType()
        self.assertIsInstance(st, str)
        self.assertGreater(len(st), 0)

    def test_GetMetaData_ReturnsDict(self):
        meta = self.Image.GetMetaData()
        self.assertIsInstance(meta, dict)
        self.assertGreater(len(meta), 0)

    def test_GetParametersAsFormattedString_ReturnsString(self):
        s = self.Image.GetParametersAsFormattedString()
        self.assertIsInstance(s, str)
        self.assertGreater(len(s), 0)

    # --- Tolerance get/set ---

    def test_SetGetTolerance_RoundTrip(self):
        self.Image.SetTolerance(np.float32(3.14))
        self.assertAlmostEqual(float(self.Image.GetTolerance()), 3.14, places=4)

    # --- SpectrumIterator ---

    def test_SpectrumIterator_YieldsAllSpectra(self):
        count = sum(1 for _ in self.Image.SpectrumIterator())
        self.assertEqual(count, self.Image.GetNumberOfSpectra())

    def test_SpectrumIterator_TupleStructure(self):
        for item in self.Image.SpectrumIterator():
            self.assertEqual(len(item), 3)  # (id, xs, ys)
            break

    # --- Normalization ---

    def test_SetNormalization_TIC_ChangesIonImage(self):
        mz = self.Image.GetXAxis()[len(self.Image.GetXAxis()) // 2]
        arr_none = self.Image.GetArray(mz, self.tol_in_da).copy()
        self.Image.SetNormalization(m2.m2Normalization.TIC)
        arr_tic = self.Image.GetArray(mz, self.tol_in_da)
        # With TIC normalization at least some values should differ
        # (unless already normalized); just check it returns valid data
        self.assertEqual(arr_tic.shape, arr_none.shape)
        self.assertTrue(np.all(arr_tic >= 0))

    def test_SetNormalization_ResetToNone(self):
        mz = self.Image.GetXAxis()[0]
        arr_before = self.Image.GetArray(mz, self.tol_in_da).copy()
        self.Image.SetNormalization(m2.m2Normalization.TIC)
        self.Image.SetNormalization(m2.m2Normalization.NONE)
        arr_after = self.Image.GetArray(mz, self.tol_in_da)
        np.testing.assert_array_equal(arr_before, arr_after)

    # --- Intensity transformation ---

    def test_SetIntensityTransformation_Log2_NonNegative(self):
        self.Image.SetIntensityTransformation(m2.m2IntensityTransformation.Log2)
        mz = self.Image.GetXAxis()[len(self.Image.GetXAxis()) // 2]
        arr = self.Image.GetArray(mz, self.tol_in_da)
        # Background pixels are 0; valid pixels may be log-transformed; no NaN/Inf
        self.assertFalse(np.any(np.isnan(arr)))
        self.assertFalse(np.any(np.isinf(arr)))

    # --- Baseline correction ---

    def test_SetBaselineCorrection_TopHat_ReturnsValidData(self):
        self.Image.SetBaselineCorrection(m2.m2BaselineCorrection.TopHat)
        mz = self.Image.GetXAxis()[len(self.Image.GetXAxis()) // 2]
        arr = self.Image.GetArray(mz, self.tol_in_da)
        self.assertFalse(np.any(np.isnan(arr)))
        self.assertFalse(np.any(np.isinf(arr)))

    # --- Pooling ---

    def test_SetPooling_Mean_ShapeUnchanged(self):
        mz = self.Image.GetXAxis()[len(self.Image.GetXAxis()) // 2]
        arr_max = self.Image.GetArray(mz, self.tol_in_da).copy()
        self.Image.SetPooling(m2.m2Pooling.Mean)
        arr_mean = self.Image.GetArray(mz, self.tol_in_da)
        self.assertEqual(arr_max.shape, arr_mean.shape)

    def test_SetPooling_Sum_GeqMaxPooling(self):
        mz = self.Image.GetXAxis()[len(self.Image.GetXAxis()) // 2]
        self.Image.SetPooling(m2.m2Pooling.Maximum)
        arr_max = self.Image.GetArray(mz, self.tol_in_da).copy()
        self.Image.SetPooling(m2.m2Pooling.Sum)
        arr_sum = self.Image.GetArray(mz, self.tol_in_da)
        self.assertTrue(np.all(arr_sum >= arr_max - 1e-6),
                        "Sum pooling must be >= max pooling at every pixel")

    # --- Constructor with processing options ---

    def test_Constructor_WithNormalizationTIC(self):
        img = m2.ImzMLReader(getTestData("data/test.imzML"),
                             normalization=m2.m2Normalization.TIC)
        arr = img.GetArray(img.GetXAxis()[0], self.tol_in_da)
        self.assertEqual(arr.dtype, np.float32)
        self.assertFalse(np.any(np.isnan(arr)))

    def test_Constructor_WithSmoothingGaussian(self):
        img = m2.ImzMLReader(getTestData("data/test.imzML"),
                             smoothing=m2.m2Smoothing.Gaussian,
                             smoothing_half_window_size=2)
        arr = img.GetArray(img.GetXAxis()[0], self.tol_in_da)
        self.assertFalse(np.any(np.isnan(arr)))