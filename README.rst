pfdicom_rev
==================

.. image:: https://badge.fury.io/py/pfdicom_rev.svg
    :target: https://badge.fury.io/py/pfdicom_rev

.. image:: https://travis-ci.org/FNNDSC/pfdicom_rev.svg?branch=master
    :target: https://travis-ci.org/FNNDSC/pfdicom_rev

.. image:: https://img.shields.io/badge/python-3.5%2B-blue.svg
    :target: https://badge.fury.io/py/pfdicom_rev

.. contents:: Table of Contents


Quick Overview
--------------

-  ``pfdicom_rev`` processes DICOM trees for the ReV viewer.

Overview
--------

``pfdicom_rev`` processes directories containing DICOM files for the ReV viewer by converting DCM files to JPG previews and generating JSON series and study summary files, as well as index.html per study.

The script accepts an ``<inputDir>`` which should be the (absolute) root dir of the ReV library. All file locations will be referenced relative to this root dir in the JSON descriptor files.

``pfdicom_rev`` performs a mulit-pass loop over the file tree space as defined in the ``[--stage <stage>]`` flag below.

NOTE:

* ``pfdicom_rev`` relies on ImageMagick for many of its operations, including the DCM to JPG conversion, JPG resize, and preview  strip creation.

* In some cases, default limits for ``ImageMagick`` are too low for generating preview strips, especially if a given DICOM series has many (more than 100) DICOM files. One fix for this is to edit the ``policy.xml`` file pertaining to ``ImageMagick`` and set the image ``width`` and ``height`` specifiers to 100 kilo-pixels (the default is about 16KP).

.. code:: xml

    <policy domain="resource" name="width" value="100KP"/>
    <policy domain="resource" name="height" value="100KP"/>        

Please see here_ for more information.

.. _here: https://imagemagick.org/script/resources.php

Installation
------------

Dependencies
~~~~~~~~~~~~

The following dependencies are installed on your host system/python3 virtual env (they will also be automatically installed if pulled from pypi):

-  ``pfmisc`` (various misc modules and classes for the pf* family of objects)
-  ``pftree`` (create a dictionary representation of a filesystem hierarchy)
-  ``pfdicom`` (handle underlying DICOM file reading)

Using ``PyPI``
~~~~~~~~~~~~~~

The best method of installing this script and all of its dependencies is
by fetching it from PyPI

.. code:: bash

        pip3 install pfdicom_rev

Command line arguments
----------------------

.. code:: html

        -I|--inputDir <inputDir>
        Input DICOM directory to examine. By default, the first file in this
        directory is examined for its tag information. There is an implicit
        assumption that each <inputDir> contains a single DICOM series.

        [-e|--extension <DICOMextension>]
        An optional extension to filter the DICOM files of interest from the 
        <inputDir>.

        -O|--outputDir <outputDir>
        The output root directory that will contain a tree structure identical
        to the input directory, and each "leaf" node will contain the analysis
        results.

        For ReV, this is often the special directive '%inputDir' which directs
        the system to generate all outputs in the input tree directly.

        [--outputLeafDir <outputLeafDirFormat>]
        If specified, will apply the <outputLeafDirFormat> to the output
        directories containing data. This is useful to blanket describe
        final output directories with some descriptive text, such as 
        'anon' or 'preview'. 

        This is a formatting spec, so 

            --outputLeafDir 'preview-%s'

        where %s is the original leaf directory node, will prefix each
        final directory containing output with the text 'preview-' which
        can be useful in describing some features of the output set.

        [-T|--tagStruct <JSONtagStructure>]
        Parse the tags and their "subs" from a JSON formatted <JSONtagStucture>
        passed directly in the command line. This is used in the optional 
        DICOM anonymization.

        [-S|--server <server>]
        The name of the server hosting the ReV viewer.

        Defaults to empty string '' which is interpreted as the current host, 
        i.e. the host running `pfdicom_rev`. If the actual viewer is hosted
        elsewhere, use this flag to specify the *viewer* host.

        [--stage <stage>]
        Stage to execute -- mostly for debugging purposes and useful if running a 
        particular stage repeatedly. There are some caveats to this -- mostly that
        stages are serially dependent, thus running "--stage 4" off the bat will
        not work since previous stages have not completed.

        The actual thread of stage flow and dependencies are:



                                      /--stage 2 
                                     /              
                            stage 1--               
                                     \             
                                      \--stage 3----stage 4 


            [1] analyize all the DCM files in the <inputDir>
                *   convert each DCM to JPG (native)
                *   resize all JPGs to  96x96  and generate mosaic preview strip
                *   resize all JPGs to 300x300 and generate DCMtag preview
                *   tag middle JPG in series based on series length
                *   create JSON per example series-level descriptors in each example
                    directory:
                        * declare location of actual series DCM files
                *   create JSON per month example-level descriptors in each month 
                    directory: 
                        * declare location of middle thumbnail JPGs
                
                In each series directory:
                    <YY>-yr/<MM>-mo/<XX>-ex/
                        forall(<SERIES>):
                            o dcm2jpgDCMresize/*jpg
                            o dcm2jpgRaw/*jpg
                            o preview.jpg
                            o raw-preview.jpg
                        o <SERIES>-series.json
                    <YY>-yr/<MM>-mo/
                        o ex.json

            [2] analyze all the JSON series-level descriptors from stage [1] and 
                in each example directory:
                *   create study-level JSON descriptors that summarize
                    all series JSON data into one file
                *   create study-level index.html that directs to the ReV viewer
                    with this yr/mo/ex tuple.

                In each study directory:
                    <YY>-yr/<MM>-mo/<XX>-ex/
                        o description.json
                        o index.html

            [3] analyze all the JSON per month example-level descriptors
                from stage [1] and in each month directory:
                *   create overview per-month index.html that shows
                    per-example thumbnails

                In each month direcory:
                    <YY>-yr/<MM>-mo
                    o index.html

            [4] analyze all JSON study level descriptors from stage [2]
                *   create tree map for mapping of arbitrary patient age to
                    closest hits in tree
                
                In the root dir:
                    o map.json

        [--studyJSON <studyJSONfile>]
        The name of the study JSON file. 

        Defaults to 'description.json'.

        [--threads <numThreads>]
        If specified, break the innermost analysis loop into <numThreads>
        threads.

        [-x|--man]
        Show full help.

        [-y|--synopsis]
        Show brief help.

        [--json]
        If specified, output a JSON dump of final return.

        [--followLinks]
        If specified, follow symbolic links.

        [-v|--verbosity <level>]
        Set the app verbosity level. 

            0: No internal output;
            1: Run start / stop output notification;
            2: As with level '1' but with simpleProgress bar in 'pftree';
            3: As with level '2' but with list of input dirs/files in 'pftree';
            5: As with level '3' but with explicit file logging for
                    - read
                    - analyze
                    - write
            
Examples
--------

Process a tree containing DICOM files for ReV:

.. code:: bash

        pfdicom_rev                                         \\
                    -I /var/www/html/rev                    \\
                    -O %inputDir                            \\
                    --threads 0 --printElapsedTime          \\
                    -v 3

which will run a DCM and JSON analysis, printing the final elapsed processing time.
