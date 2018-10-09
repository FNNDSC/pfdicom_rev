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

``pfdicom_rev`` performs a multi-pass loop over the file tree space:

1. Process all DICOMs:
    - Optional anonymize
    - Convert DCM to JPG
    - Generate preview strip
    - Generate a per-series description file in the series root directory

2. Process all JSON series files:
    - Generate a per-study JSON sumamry file

3. Create a JSON representation of the entire data space 
    - Based on the set of per-study JSON summary files, create a JSON tree used by the viewer to map incoming ``PatientAge`` to closest hit in the data tree.

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

        -e|--extension <DICOMextension>
        An optional extension to filter the DICOM files of interest from the 
        <inputDir>.

        [-O|--outputDir <outputDir>]
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

        -T|--tagStruct <JSONtagStructure>
        Parse the tags and their "subs" from a JSON formatted <JSONtagStucture>
        passed directly in the command line. This is used in the optional 
        DICOM anonymization.

        -S|--server <server>
        The name of the server hosting the ReV viewer.

        Defaults to 'http://fnndsc.tch.harvard.edu'.

        --studyJSON <studyJSONfile>
        The name of the study JSON file. 

        Defaults to 'description.json'.

        [--threads <numThreads>]
        If specified, break the innermost analysis loop into <numThreads>
        thr        -I|--inputDir <inputDir>
        Input DICOM directory to examine. By default, the first file in this
        directory is examined for its tag information. There is an implicit
        assumption that each <inputDir> contains a single DICOM series.

        -i|--inputFile <inputFile>
        An optional <inputFile> specified relative to the <inputDir>. If 
        specified, then do not perform a directory walk, but convert only 
        this file.

        -e|--extension <DICOMextension>
        An optional extension to filter the DICOM files of interest from the 
        <inputDir>.

        [-O|--outputDir <outputDir>]
        The output root directory that will contain a tree structure identical
        to the input directory, and each "leaf" node will contain the analysis
        results.

        -F|--tagFile <JSONtagFile>
        Parse the tags and their "subs" from a JSON formatted <JSONtagFile>.

        -T|--tagStruct <JSONtagStructure>
        Parse the tags and their "subs" from a JSON formatted <JSONtagStucture>
        passed directly in the command line.

        -o|--outputFileStem <outputFileStem>
        The output file stem to store data. This should *not* have a file
        extension, or rather, any "." in the name are considered part of 
        the stem and are *not* considered extensions.

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

        -v|--verbosity <level>
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
                    -I /var/www/html/rev -e dcm             \\
                    -O %inputDir                            \\
                    --threads 0 --printElapsedTime          \\
                    -v 3

which will run a DCM and JSON analysis, printing the final elapsed processing time.
