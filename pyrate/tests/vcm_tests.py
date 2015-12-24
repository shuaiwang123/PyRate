'''
Tests for PyRate's interferogram covariance calculation and Variance-Covariance matrix functionality.

Created on 14/03/2013

.. codeauthor:: Ben Davies, Matt Garthwaite
'''

import unittest
from numpy import array
from numpy.testing import assert_array_almost_equal
import os
import shutil
from subprocess import call
import numpy as np

from pyrate.vcm import cvd, get_vcmt
from pyrate.tests.common import sydney5_mock_ifgs, sydney5_ifgs
from pyrate.tests.common import sydney_data_setup
from pyrate.scripts import run_pyrate
from pyrate import matlab_mst_kruskal as matlab_mst
from pyrate.tests.common import SYD_TEST_MATLAB_ORBITAL_DIR, SYD_TEST_OUT
from pyrate import config as cf
from pyrate import reference_phase_estimation as rpe


class CovarianceTests(unittest.TestCase):
    def setUp(self):
        self.ifgs = sydney_data_setup()

    def test_covariance_basic(self):
        ifgs = sydney5_ifgs()

        for i in ifgs:
            i.open()

            if bool((i.phase_data == 0).all()) is True:
                raise Exception("All zero")

            maxvar, alpha = cvd(i, calc_alpha=True)
            self.assertTrue(maxvar is not None)
            self.assertTrue(alpha is not None)
            print "maxvar: %s, alpha: %s" % (maxvar, alpha)
            print "\n"

    def test_covariance_17ifgs(self):
        # From Matlab Pirate after raw data import
        # (no reference pixel correction and units in radians)
        exp_maxvar = [5.6149, 8.7710, 2.9373, 0.3114, 12.9931, 2.0459, 0.4236,
                      2.1243, 0.4745, 0.6725, 0.8333, 3.8232, 3.3052, 2.4925,
                      16.0159, 2.8025, 1.4345]

        exp_alpha = [0.0356, 0.1601, 0.5128, 0.5736, 0.0691, 0.1337, 0.2333,
                    0.3202, 1.2338, 0.4273, 0.9024, 0.1280, 0.3585, 0.1599,
                    0.0110, 0.1287, 0.0676]

        act_maxvar = []
        act_alpha = []

        for i in self.ifgs:

            if bool((i.phase_data == 0).all()) is True:
                raise Exception("All zero")

            maxvar, alpha = cvd(i, calc_alpha=True)
            self.assertTrue(maxvar is not None)
            self.assertTrue(alpha is not None)
           
            act_maxvar.append(maxvar)
            act_alpha.append(alpha)

        assert_array_almost_equal(act_maxvar, exp_maxvar, decimal=3)

        # This test fails for greater than 1 decimal place.
        # Discrepancies observed in distance calculations.
        assert_array_almost_equal(act_alpha, exp_alpha, decimal=1)


class VCMTests(unittest.TestCase):

    def setUp(self):
        self.ifgs = sydney_data_setup()

    def test_vcm_basic(self):
        ifgs = sydney5_mock_ifgs(5, 9)
        maxvar = [8.486, 12.925, 6.313, 0.788, 0.649]

        # from Matlab Pirate make_vcmt.m code
        exp = array([[8.486, 5.2364, 0.0, 0.0, 0.0],
            [5.2364, 12.925,  4.5165,  1.5957,  0.0],
            [0.0, 4.5165, 6.313, 1.1152, 0.0],
            [0.0, 1.5957, 1.1152, 0.788, -0.3576],
            [0.0, 0.0, 0.0, -0.3576, 0.649]])

        act = get_vcmt(ifgs, maxvar)
        assert_array_almost_equal(act, exp, decimal=3)

    def test_vcm_17ifgs(self):
        # TODO: maxvar should be calculated by vcm.cvd
        maxvar = [2.879, 4.729, 22.891, 4.604, 3.290, 6.923, 2.519, 13.177,
                7.548, 6.190, 12.565, 9.822, 18.484, 7.776, 2.734, 6.411, 4.754]

        # Output from Matlab Pirate make_vcmt.m
        exp = array([[2.879, 0.0, -4.059, -1.820, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ],
            [0.0, 4.729, 0.0, 0.0, 1.972, 0.0, 0.0, -3.947, -2.987, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ],
            [-4.059, 0.0, 22.891, 5.133, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -7.497, -10.285, 0.0, 0.0, 0.0, 0.0 ],
            [-1.820, 0.0, 5.133, 4.604, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.362, 0.0, 0.0, -1.774, 0.0, 0.0 ],
            [0.0, 1.972, 0.0, 0.0, 3.290, 2.386, 1.439, -3.292, -2.492, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ],
            [0.0, 0.0, 0.0, 0.0, 2.386, 6.923, 2.088, 0.0, 0.0, -3.273, -4.663, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ],
            [0.0, 0.0, 0.0, 0.0, 1.439, 2.088, 2.519, 0.0, 0.0, 1.974, 0.0, 0.0, 0.0, -2.213, 0.0, 0.0, 0.0 ],
            [0.0, -3.947, 0.0, 0.0, -3.292, 0.0, 0.0, 13.177, 4.986, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.596, -3.957 ],
            [0.0, -2.987, 0.0, 0.0, -2.492, 0.0, 0.0, 4.986, 7.548, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.995 ],
            [0.0, 0.0, 0.0, 0.0, 0.0, -3.273, 1.974, 0.0, 0.0, 6.190, 4.410, 0.0, 0.0, -3.469, 0.0, 0.0, 0.0 ],
            [0.0, 0.0, 0.0, 0.0, 0.0, -4.663, 0.0, 0.0, 0.0, 4.410, 12.565, 0.0, 0.0, 4.942, 0.0, 0.0, 0.0 ],
            [0.0, 0.0, -7.497, 3.362, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 9.8221, 6.737, 0.0, -2.591, 0.0, 0.0 ],
            [0.0, 0.0, -10.285, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 6.737, 18.484, 0.0, 3.554, -5.443, 0.0 ],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.213, 0.0, 0.0, -3.469, 4.942, 0.0, 0.0, 7.776, 0.0, 0.0, 0.0 ],
            [0.0, 0.0, 0.0, -1.774, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.591, 3.554, 0.0, 2.734, -2.093, 0.0 ],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.596, 0.0, 0.0, 0.0, 0.0, -5.443, 0.0, -2.093, 6.411, -2.760 ],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -3.957, 2.995, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -2.760, 4.754 ]])

        act = get_vcmt(self.ifgs, maxvar)
        assert_array_almost_equal(act, exp, decimal=3)


class MatlabEqualityTestInRunPyRateSequence(unittest.TestCase):
    def setUp(self):
        self.matlab_maxvar = [15.4156637191772,
                                2.85829424858093,
                                34.3486289978027,
                                2.59190344810486,
                                3.18510007858276,
                                3.61054635047913,
                                1.64398515224457,
                                14.9226036071777,
                                5.13451862335205,
                                6.82901763916016,
                                10.9644861221313,
                                14.5026779174805,
                                29.3710079193115,
                                8.00364685058594,
                                2.06328082084656,
                                5.66661834716797,
                                5.62802362442017]


        # start each full test run cleanly
        shutil.rmtree(SYD_TEST_OUT, ignore_errors=True)

        os.makedirs(SYD_TEST_OUT)

        params = cf.get_config_params(
                os.path.join(SYD_TEST_MATLAB_ORBITAL_DIR, 'orbital_error.conf'))
        params[cf.REF_EST_METHOD] = 2
        call(["python", "pyrate/scripts/run_prepifg.py",
              os.path.join(SYD_TEST_MATLAB_ORBITAL_DIR, 'orbital_error.conf')])

        xlks, ylks, crop = run_pyrate.transform_params(params)

        base_ifg_paths = run_pyrate.original_ifg_paths(params[cf.IFG_FILE_LIST])

        dest_paths = run_pyrate.get_dest_paths(base_ifg_paths,
                                               crop, params, xlks)

        ifg_instance = matlab_mst.IfgListPyRate(datafiles=dest_paths)

        ifgs = ifg_instance.ifgs

        for i in ifgs:
            if not i.is_open:
                i.open()
            if not i.nan_converted:
                i.convert_to_nans()

            if not i.mm_converted:
                i.convert_to_mm()
                i.write_modified_phase()

        if params[cf.ORBITAL_FIT] != 0:
            run_pyrate.remove_orbital_error(ifgs, params)

        refx, refy = run_pyrate.find_reference_pixel(ifgs, params)

        if params[cf.ORBITAL_FIT] != 0:
            run_pyrate.remove_orbital_error(ifgs, params)

        _, ifgs = rpe.estimate_ref_phase(ifgs, params, refx, refy)

        # Calculate interferogram noise
        # TODO: assign maxvar to ifg metadata (and geotiff)?
        self.maxvar = [cvd(i)[0] for i in ifgs]
        self.vcmt = get_vcmt(ifgs, self.maxvar)

    def test_matlab_maxvar_equality_sydney_test_files(self):
        np.testing.assert_array_almost_equal(self.maxvar, self.matlab_maxvar,
                                             decimal=4)

    def test_matlab_vcmt_equality_sydney_test_files(self):
        from pyrate.tests.common import SYD_TEST_DIR
        MATLAB_VCM_DIR = os.path.join(SYD_TEST_DIR, 'matlab_vcm')
        matlab_vcm = np.genfromtxt(os.path.join(MATLAB_VCM_DIR,
                                   'matlab_vcmt.csv'), delimiter=',')
        np.testing.assert_array_almost_equal(matlab_vcm, self.vcmt, decimal=3)


if __name__ == "__main__":
    unittest.main()
