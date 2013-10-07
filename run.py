#!/usr/bin/python
import sys
import subprocess

sim = ''
hostfile = ''
length = 0
iter = 0

if len(sys.argv) != 5:
	print "usage: run.py simname hostfile length num_evolutions"
else:
	sim = sys.argv[1]
	hostfile = sys.argv[2]
	length = sys.argv[3]
	itr = sys.argv[4]
	#print sim + hostfile + str(length) + str(itr) 
	
	if sys.argv[1] == 'cmpi':
		subprocess.call(['mpiexec', '--hostfile', hostfile, './C_MPI_Implementation/Life', '-c', length, '-r', length, '-g', itr])
	elif sys.argv[1] == 'serial':
		subprocess.call(['python', './pi3d/demos/Conway.py', length, itr])
	elif sys.argv[1] == 'hybridmpi':
		subprocess.call(['mpiexec', '--hostfile', hostfile, 'python', './pi3d/demos/MPIConway.py', length, itr])
	
