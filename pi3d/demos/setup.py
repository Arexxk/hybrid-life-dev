from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("c_MPIConway", ["c_MPIConway.pyx"])]

setup(
	name = 'SDSC+Pi3d Conways MPI Hybrid Demo',
	cmdclass = {'build_ext': build_ext},
	ext_modules = ext_modules
)
