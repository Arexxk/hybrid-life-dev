Alexander Kissinger
PHYS244
Spring 2013

Intro:
There are three implementations that can be ran in from source: C-MPI, Serial-
GPU, and Hybrid-MPI versions. *NOTE: This was tested on and developed to be 
supported on, primarily, a Raspberry Pi Cluster. Compiling on any other system 
will not guarentee properly functioning code. This README also assumes that you
have a Raspberry Pi cluster in your disposal.

Preparing the code:
Before running/compiling, here are the following dependencies:
python-dev
python-imaging (PIL)
mpi-defualt-bin (open-mpi) 
mpi-defualt-dev
mpi4py
numpy

The above were installed on a Debian Flavored Linux Distribution (Raspbian) using
Aptitude. 

After installing the dependencies, you will have to go into the 
C_MPI_Implementation folder and perform a 'make' before making making any calls
to the C-MPI simulation. 

The run.py file is the head file for running the simulations and should be used as
so. Of course you can always study the directories and make MPIrun calls on your
own. The following illestrates how to perform the simulations:

To run a C_MPI simulation run the following:
./run.py cmpi hostfile length_of_side num_evolutions 

To run a serial-GPU simulation run the following:
./run.py serial hostfile length_of_side num_evolutions 

To run a hybrid-MPI simulation run the following:
./run.py hybridmpi hostfile length_of_side num_evolutions 

All simulations will output the time it takes for each task to compute the matrix of
length provided at the number of evolutions provided.
Be advised that the current implementation limits inputing different sized lengths
for the width and height and simply accepts a single argument and squares it for 
the area. This is becuase the base Conway.py and OpenGL ES is very selective on the
problem set size, as well as the input texture, and until we have streamlined this
issue we will wait before providing this feature until a later release.

In the case that either the Hybrid or Serial simualtions crash, it will most likely
be a result of picking length parameters that are to high/low or ones that the 
OpenGL shader does not like. If this happens just choose different parameters. 

C-MPI implementation was found on Shodor's main site and belongs to Samuel 
Leeman-Munk. The Hybrid-MPI was developed by Alexander Kissinger, guided by Rick
Wagner (SDSC), and belongs to the San Diego Super Computing Sandbox Project. The
Hybrid-MPI code, as well as the Serial-GPU implementation, was based-off, and 
originally developed by, Pi3d (pi3d.github.io) and the Pi3d Team (a special thanks
to Paddy).
