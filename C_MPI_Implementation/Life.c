/*******************************************
MPI Life 1.0
Copyright 2002, David Joiner and
  The Shodor Education Foundation, Inc.
Updated 2010, Andrew Fitz Gibbon and
  The Shodor Education Foundation, Inc.
Updated 2010, Tiago Sommer Damasceno and
  The Shodor Education Foundation, Inc.

A C implementation of Conway's Game of Life.

To run:
mpirun -np <num procs> Life [Rows] [Columns] [Generations] [Display]

See the README included in this directory for
more detailed information.
*******************************************/
#
#include "Life.h"
#include "Defaults.h" // For Life's constants
#include "time.h"

int main(int argc, char ** argv) {

	int count;
	struct life_t life;
	clock_t t;

	init(&life, &argc, &argv);
	float time0 = clock();	
	for (count = 0; count < life.generations; count++) {

		copy_bounds(&life);

		eval_rules(&life);

		update_grid(&life);
	}
	double time1 = clock();	
	printf("%f\n",(time1-time0)/CLOCKS_PER_SEC);
	cleanup(&life);
	exit(EXIT_SUCCESS);
}
