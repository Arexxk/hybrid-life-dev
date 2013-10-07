###############################################################################
# Makefile for the version of Game of Life with no paralleism as included on 
# the BCCD (http://bccd.net)
#
# By default, include X display.
#
# Add NO_X11=1 to omit X libraries.
###############################################################################

#
# Variables and Flags
#

CC        = mpicc 


LIBS     += -lm
CFLAGS   += 
LDFLAGS  += $(LIBS)
PROGRAM   = Life
SRCS      = Life.c

###### MPI OPTIONS##
CFLAGS += -DHAS_MPI
LIBS += -lmpi
#################### 

OBJS      = $(SRCS:.c=.o)		# object file

#
# Targets
#

default: all

all: $(PROGRAM) 

$(PROGRAM): $(OBJS)
	$(CC) -o $(PROGRAM) $(SRCS) $(CFLAGS) $(LDFLAGS)

clean:
	/bin/rm -f $(OBJS) $(PROGRAM)

