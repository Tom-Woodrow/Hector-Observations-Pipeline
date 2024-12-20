![Build Status](https://github.com/samvaughan/Hector-Observations-Pipeline/actions/workflows/run_tests.yaml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/hector-observations-pipeline/badge/?version=latest)](https://hector-observations-pipeline.readthedocs.io/en/latest/?badge=latest)

# The Hector Galaxy Survey Observation Pipeline

### From an input catalogue to a list of hexabundle positions

This pipeline:

* creates a catalogue of galaxies to observe from a master catalogue (or can be given an input catalogue)
* assigns galaxies to individual survey tiles, avoiding clashes
* converts the RA and DEC of objects on the sky to (x,y) coordinates on the Hector field plate
* configures the positions of the Hector hexabundles so they don't clash with each other
* assigns which hexabundle size will be used to observe each galaxy
* creates final output files which can be read in by the robot software to actually position each hexabundle on the plate

You can read the documentation at https://hector-observations-pipeline.readthedocs.io/en/latest/