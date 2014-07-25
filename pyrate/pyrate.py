'''
Main workflow script for PyRate

Created on 17/09/2012
@author: Ben Davies, NCI
'''

import config as cf
import logging
import datetime

from shared import Ifg
import algorithm, mst, refpixel, orbital


# constants for metadata flags
META_UNITS = 'PHASE_UNITS'
MILLIMETRES = 'MILLIMETRES'
META_ORBITAL = 'ORBITAL_ERROR'
META_REMOVED = 'REMOVED'

# TODO: add basic logging statements 
def main(cfgfile='pyrate.conf', verbose=True):
	"""TODO: pirate workflow"""
	raise NotImplementedError

	# TODO: add parameter error checking to fail fast, before number crunching
	params = cf.get_config_params(cfgfile)

	# TODO: get list of mlooked/cropped ifgs
	# NB: keep source files intact, should be run after prepifg code
	#ifglist = config.parse_namelist(params[config.IFG_FILE_LIST])
	#ifg_namelist = [os.path.join(params[config.OBS_DIR], p) for p in ifglist]
	#ifgs = [Ifg(p) for p in ifg_namelist]


def process_ifgs(ifgs, params):
	'''
	High level function to perform correction steps on supplied ifgs
	ifgs: sequence of Ifg objs (unopened)
	params: dict of run config params
	'''
	init_logging(logging.DEBUG)
	for i in ifgs:
		i.open()
		convert_wavelength(i)

	remove_orbital_error(ifgs, params)

	mst_grid = mst.mst_matrix_ifgs_only(ifgs)
	# TODO: refy, refx = refpixel.ref_pixel(params, ifgs)

	# final close
	while ifgs:
		i = ifgs.pop()
		i.dataset.FlushCache()
		i = None # force close TODO: may need to implement close()

	logging.debug('End PyRate processing\n')

# TODO: write to alternate file if log exists
def init_logging(level):
	t = datetime.datetime.now()
	path = 'pyrate_%s_%02d_%02d.log' % (t.year, t.month, t.day)
	fmt = '%(asctime)s %(message)s'
	datefmt = '%d/%m/%Y %I:%M:%S %p'
	logging.basicConfig(filename=path, format=fmt, datefmt=datefmt, level=level)
	logging.debug('Log started')


def convert_wavelength(ifg):
	if ifg.dataset.GetMetadataItem(META_UNITS) == MILLIMETRES:
		msg = '%s: ignored as previous wavelength conversion detected'
		logging.debug(msg % ifg.data_path)
		return

	ifg.data = algorithm.wavelength_radians_to_mm(ifg.phase_data, ifg.wavelength)
	ifg.dataset.SetMetadataItem(META_UNITS, MILLIMETRES)
	msg = '%s: converted wavelength to millimetres'
	logging.debug(msg % ifg.data_path)

def remove_orbital_error(ifgs, params):
	if not params[cf.ORBITAL_FIT]:
		logging.debug('Orbital correction skipped')
		return

	# perform some general error/sanity checks
	flags = [i.dataset.GetMetadataItem(META_ORBITAL) for i in ifgs]

	if all(flags):
		msg = 'Skipping orbital correction as all ifgs have error removed'
		logging.debug(msg)
		return
	else:
		check_orbital_ifgs(ifgs, flags)

	if params[cf.ORBITAL_FIT_LOOKS_X] > 1 or params[cf.ORBITAL_FIT_LOOKS_Y] > 1:
		# resampling here to use all prior corrections to orig data
		# TODO: avoid writing mlooked to disk by using mock ifgs/in mem arrays?
		raise NotImplementedError('TODO: Orbital multilooking')

	orbital.orbital_correction(ifgs,
 							degree=params[cf.ORBITAL_FIT_DEGREE],
 							method=params[cf.ORBITAL_FIT_METHOD])
	for i in ifgs:
		i.dataset.SetMetadataItem(META_ORBITAL, META_REMOVED)

def check_orbital_ifgs(ifgs, flags):
	count = sum([f == META_REMOVED for f in flags])
	if count < len(flags) and count > 0:
		msg = 'Detected corrected and uncorrected orbital error in ifgs'
		logging.debug(msg)

		for i, flag in zip(ifgs, flags):
			if flag:
				msg = '%s: prior orbital error correction detected'
			else:
				msg = '%s: no orbital correction detected'
			logging.debug(msg % i.data_path)

		raise orbital.OrbitalError(msg)



# function template
#
# add check for pre-existing metadata flag / skip if required
# perform calculation
# optionally save modified data to disk if required
# optionally save correction component to disk (more useful for debugging) 
# set flag in dataset for correction
# write to log file
