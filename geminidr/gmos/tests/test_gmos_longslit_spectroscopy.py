#!/usr/bin/python
"""
Tests related to GMOS Long-slit Spectroscopy data reduction.
"""
import glob
import numpy as np
import os

import astrodata
import astrofaker
import geminidr

# noinspection PyPackageRequirements
import pytest

# noinspection PyUnresolvedReferences
import gemini_instruments

from geminidr.gmos import primitives_gmos_spect, primitives_gmos_longslit
from gempy.adlibrary import dataselect
from gempy.utils import logutils
from recipe_system.reduction.coreReduce import Reduce
from recipe_system.utils.reduce_utils import normalize_ucals
from scipy import ndimage

dataset_folder_list = ['GMOS/GN-2017A-FT-19',
                       'GMOS/GS-2016B-Q-54-32']


@pytest.fixture(scope='class')
def calibrations():

    my_calibrations = []

    yield my_calibrations

    _ = [os.remove(f) for f in glob.glob(os.path.join(os.getcwd(), '*.fits'))]


@pytest.mark.gmosls
@pytest.mark.parametrize('dataset_folder', dataset_folder_list, scope='class')
class TestGmosReduceLongslit:
    """
    Collection of tests that will run on every `dataset_folder`. Both
    `dataset_folder` and `calibrations` parameter should be present on every
    test. Even when the test does not use it.
    """
    @staticmethod
    def test_can_run_reduce_bias(dataset_folder, calibrations, path_to_inputs,
                                 path_to_outputs):
        """
        Make sure that the reduce_BIAS works for spectroscopic data.
        """
        logutils.config(file_name='reduce_GMOS_LS_bias.log')

        dataset = sorted(
            glob.glob(os.path.join(path_to_inputs, dataset_folder, '*.fits')))

        list_of_bias = dataselect.select_data(dataset, ['BIAS'], [])
        reduce_bias = Reduce()
        assert len(reduce_bias.files) == 0

        reduce_bias.files.extend(list_of_bias)
        assert len(reduce_bias.files) == len(list_of_bias)

        reduce_bias.runr()

        new_files = [os.path.join(path_to_outputs, dataset_folder, f)
                     for f in reduce_bias.output_filenames]

        for old, new in zip(reduce_bias.output_filenames, new_files):
            os.renames(old, new)
            calibrations.append('processed_bias:{}'.format(new))

    @staticmethod
    def test_can_run_reduce_flat(dataset_folder, calibrations, path_to_inputs,
                                 path_to_outputs):
        """
        Make sure that the reduce_FLAT_LS_SPECT works for spectroscopic data.
        """
        logutils.config(file_name='reduce_GMOS_LS_flat.log')

        dataset = sorted(
            glob.glob(os.path.join(path_to_inputs, dataset_folder, '*.fits')))

        list_of_flat = dataselect.select_data(dataset, ['FLAT'], [])

        reduce_flat = Reduce()
        assert len(reduce_flat.files) == 0

        reduce_flat.files.extend(list_of_flat)
        assert len(reduce_flat.files) == len(list_of_flat)

        reduce_flat.ucals = normalize_ucals(reduce_flat.files, calibrations)

        reduce_flat.runr()

        if not os.path.exists(os.path.join(path_to_outputs, dataset_folder)):
            os.makedirs(os.path.join(path_to_outputs, dataset_folder))

        new_files = [os.path.join(path_to_outputs, dataset_folder, f)
                     for f in reduce_flat.output_filenames]

        for old, new in zip(reduce_flat.output_filenames, new_files):
            os.renames(old, new)
            calibrations.append('processed_flat:{}'.format(new))

    @staticmethod
    def test_can_run_reduce_arc(dataset_folder, calibrations, path_to_inputs,
                                path_to_outputs):
        """
        Make sure that the reduce_FLAT_LS_SPECT can run for spectroscopic
        data.
        """
        logutils.config(file_name='reduce_GMOS_LS_arc.log')

        dataset = sorted(
            glob.glob(os.path.join(path_to_inputs, dataset_folder, '*.fits')))

        list_of_arcs = dataselect.select_data(dataset, ['ARC'], [])

        for f in list_of_arcs:
            ad = astrodata.open(f)
            _ = ad.gain_setting()

        for c in calibrations:
            f = c.split(':')[-1]
            ad = astrodata.open(f)
            _ = ad.gain_setting()

        adinputs = [astrodata.open(f) for f in list_of_arcs]

        cal_files = normalize_ucals(list_of_arcs, calibrations)
        processed_bias = [cal_files[k] for k in cal_files.keys() if 'processed_bias' in k]

        p = primitives_gmos_spect.GMOSSpect(adinputs)

        p.viewer = geminidr.dormantViewer(p, None)

        p.prepare()
        p.addDQ(static_bpm=None)
        p.addVAR(read_noise=True)
        p.overscanCorrect()
        p.biasCorrect(bias=processed_bias)
        p.ADUToElectrons()
        p.addVAR(poisson_noise=True)
        p.mosaicDetectors()
        p.makeIRAFCompatible()
        p.determineWavelengthSolution()
        p.determineDistortion()
        p.storeProcessedArc()
        p.writeOutputs()

        new_files = [os.path.join(path_to_outputs, dataset_folder, f)
                     for f in glob.glob('*.fits')]

        for old, new in zip(glob.glob('*.fits'), new_files):
            os.renames(old, new)
            if 'arc' in new:
                calibrations.append('processed_arc:{}'.format(new))

    # noinspection PyUnusedLocal
    @staticmethod
    @pytest.mark.skip(reason="Work in progress")
    def test_can_run_reduce_science(dataset_folder, calibrations):
        """
        Make sure that the recipes_ARC_LS_SPECT works for spectroscopic data.
        """
        assert True
        # ToDo WIP - Define first how flats are processed
        # raw_subdir = 'GMOS/GN-2017A-FT-19'
        #
        # logutils.config(file_name='reduce_GMOS_LS_arc.log')
        #
        # assert len(calibrations) == 2
        #
        # all_files = sorted(glob.glob(os.path.join(path_to_inputs, raw_subdir, '*.fits')))
        # assert len(all_files) > 1
        #
        # list_of_science = dataselect.select_data(all_files, [], ['CAL'])
        #
        # reduce_science = Reduce()
        # assert len(reduce_science.files) == 0
        #
        # reduce_science.files.extend(list_of_science)
        # assert len(reduce_science.files) == len(list_of_science)
        #
        # reduce_science.ucals = normalize_ucals(reduce_science.files, calibrations)
        #
        # reduce_science.runr()


class TestGmosReduceFakeData:
    """
    The tests defined by this class reflect the expected behavior on science
    spectral data.
    """
    @staticmethod
    def create_1d_spectrum(width, n_lines, max_weight):
        """
        Generates a 1D NDArray noiseless spectrum.

        Parameters
        ----------
        width : int
            Number of array elements.
        n_lines : int
            Number of artificial lines.
        max_weight : float
            Maximum weight (or flux, or intensity) of the lines.

        Returns
        -------
        sky_1d_spectrum : numpy.ndarray

        """
        lines = np.random.randint(low=0, high=width, size=n_lines)
        weights = max_weight * np.random.random(size=n_lines)

        spectrum = np.zeros(width)
        spectrum[lines] = weights

        return spectrum

    def test_can_extract_1d_spectra_from_2d_spectral_image(self):

        logutils.config(file_name='foo.log')

        np.random.seed(0)

        ad = astrofaker.create('GMOS-S')

        ad.phu['DETECTOR'] = 'GMOS-S + Hamamatsu'
        ad.phu['UT'] = '04:00:00.000'
        ad.phu['DATE'] = '2017-05-30'
        ad.phu['OBSTYPE'] = 'OBJECT'

        ad.init_default_extensions()

        for ext in ad:
            ext.hdr['GAIN'] = 1.0

        width = int(np.sum([ext.shape[1] for ext in ad]))
        height = ad[0].shape[0]
        snr = 0.1

        obj_max_weight = 300.
        obj_continnum = 600. + 0.01 * np.arange(width)

        sky = self.create_1d_spectrum(width, int(0.01 * width), 300.)
        obj = self.create_1d_spectrum(width, int(0.1 * width), obj_max_weight) \
            + obj_continnum

        obj_pos = np.random.randint(low=height // 2 - int(0.1 * height),
                                    high=height // 2 + int(0.1 * height))

        spec = np.repeat(sky[np.newaxis, :], height, axis=0)
        spec[obj_pos] += obj
        spec = ndimage.gaussian_filter(spec, sigma=(7, 3))

        spec += snr * obj_max_weight * np.random.random(spec.shape)

        for i, ext in enumerate(ad):

            left = i * ext.shape[1]
            right = (i + 1) * ext.shape[1] - 1

            ext.data = spec[:, left:right]

        p = primitives_gmos_longslit.GMOSLongslit([ad])

        p.prepare()  # Needs 'DETECTOR', 'UT', and 'DATE'
        p.addDQ(static_bpm=None)  # Needs 'GAIN'
        p.addVAR(read_noise=True)
        # p.overscanCorrect()
        # p.biasCorrect(bias=processed_bias)
        p.ADUToElectrons()
        p.addVAR(poisson_noise=True)
        p.mosaicDetectors()
        # p.makeIRAFCompatible()  # Needs 'OBSTYPE'



if __name__ == '__main__':
    pytest.main()