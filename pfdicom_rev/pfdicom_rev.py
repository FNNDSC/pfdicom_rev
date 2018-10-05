# System imports
import      os
import      getpass
import      argparse
import      json
import      pprint
import      subprocess
import      uuid

# Project specific imports
import      pfmisc
from        pfmisc._colors      import  Colors
from        pfmisc              import  other
from        pfmisc              import  error

import      pudb
import      pftree
import      pfdicom

class pfdicom_rev(pfdicom.pfdicom):
    """

    A class based on the 'pfdicom' infrastructure that extracts 
    and processes DICOM tags according to several requirements.

    Powerful output formatting, such as image conversion to jpg/png
    and generation of html reports is also supported.

    """

    def externalExecutables_set(self):
        """
        A method to set the path/name of various executables.

        These results are obviously system specific, etc. 

        More sophisticated logic, if needed, should be added here.

        PRECONDITIONS:

            * None

        POSTCONIDTIONS:

            * Various names of executable helpers are set
        """
        self.exec_dcm2jpgConv           = '/usr/bin/dcmj2pnm'
        self.exec_jpgResize             = '/usr/bin/mogrify'
        self.exec_jpgPreview            = '/usr/bin/convert'
        self.exec_dcmAnon               = '/usr/bin/dcmodify'

    def sys_run(self, astr_cmd):
        """
        Simple method to run a command on the system.

        RETURN:

            * response from subprocess.run() call
        """

        return subprocess.run(
            astr_cmd,
            stdout  = subprocess.PIPE,
            stderr  = subprocess.STDOUT,
            shell   = True
        )

    def declare_selfvars(self):
        """
        A block to declare self variables
        """

        #
        # Object desc block
        #
        self.str_desc                   = ''
        self.__name__                   = "pfdicom_rev"
        self.str_version                = "0.0.99"

        self.b_anonDo                   = True

        # Tags
        self.b_tagList                  = False
        self.b_tagFile                  = False
        self.str_tagStruct              = ''
        self.str_tagFile                = ''
        self.d_tagStruct                = {}

        self.dp                         = None
        self.log                        = None
        self.tic_start                  = 0.0
        self.pp                         = pprint.PrettyPrinter(indent=4)
        self.verbosityLevel             = -1

        # Various executable helpers
        self.exec_dcm2jpgConv           = ''
        self.exec_jpgResize             = ''
        self.exec_jpgPreview            = ''
        self.exec_dcmAnon               = ''

    def anonStruct_set(self):
        """
        Setup the anon struct
        """
        self.d_tagStruct = {
            "PatientName":      "anon",
            "PatientID":        "anon",
            "AccessionNumber":  "anon"
        }


    def __init__(self, *args, **kwargs):
        """
        Main constructor for object.
        """

        def tagStruct_process(str_tagStruct):
            self.str_tagStruct          = str_tagStruct
            if len(self.str_tagStruct):
                self.d_tagStruct        = json.loads(str_tagStruct)

        def outputDir_process(str_outputDir):
            if str_outputDir == '%inputDir':
                self.str_outputDir  = self.str_inputDir
                kwargs['outputDir'] = self.str_inputDir

        # pudb.set_trace()

        # Process some of the kwargs by the base class
        super().__init__(*args, **kwargs)

        self.declare_selfvars()
        self.externalExecutables_set()
        self.anonStruct_set()

        for key, value in kwargs.items():
            if key == 'tagStruct':          tagStruct_process(value)
            if key == "outputDir":          outputDir_process(value) 
            if key == 'verbosity':          self.verbosityLevel         = int(value)

        # Set logging
        self.dp                        = pfmisc.debug(    
                                            verbosity   = self.verbosityLevel,
                                            within      = self.__name__
                                            )
        self.log                       = pfmisc.Message()
        self.log.syslog(True)

    def inputReadCallback(self, *args, **kwargs):
        """
        Callback for reading files from specific directory.

        In the context of pfdicom_rev, this implies reading
        DICOM files and returning the dcm data set.

        """
        str_path            = ''
        l_file              = []
        b_status            = True
        l_DCMRead           = []
        filesRead           = 0

        for k, v in kwargs.items():
            if k == 'l_file':   l_file      = v
            if k == 'path':     str_path    = v

        if len(args):
            at_data         = args[0]
            str_path        = at_data[0]
            l_file          = at_data[1]

        for f in l_file:
            self.dp.qprint("reading: %s/%s" % (str_path, f), level = 5)
            d_DCMfileRead   = self.DICOMfile_read( 
                                    file        = '%s/%s' % (str_path, f)
            )
            b_status        = b_status and d_DCMfileRead['status']
            l_DCMRead.append(d_DCMfileRead)
            str_path        = d_DCMfileRead['inputPath']
            filesRead       += 1

        if not len(l_file): b_status = False

        return {
            'status':           b_status,
            'l_file':           l_file,
            'str_path':         str_path,
            'l_DCMRead':        l_DCMRead,
            'filesRead':        filesRead
        }

    def inputAnalyzeCallback(self, *args, **kwargs):
        """
        Callback for doing actual work on the read data.

        In the context of 'ReV', the "analysis" essentially means
        calling an anonymization on input data

            * anonymize the DCM files in place

        """
        d_DCMRead           = {}
        b_status            = False
        l_dcm               = []
        l_file              = []
        filesAnalyzed       = 0

        pudb.set_trace()

        for k, v in kwargs.items():
            if k == 'd_DCMRead':    d_DCMRead   = v
            if k == 'path':         str_path    = v

        if len(args):
            at_data         = args[0]
            str_path        = at_data[0]
            d_DCMRead       = at_data[1]

        for d_DCMfileRead in d_DCMRead['l_DCMRead']:
            str_path    = d_DCMRead['str_path']
            l_file      = d_DCMRead['l_file']
            self.dp.qprint("analyzing: %s" % l_file[filesAnalyzed], level = 5)

            if self.b_anonDo:
                # For now the following are hard coded, but could in future
                # be possibly user-specified?
                for k, v in self.d_tagStruct.items():
                    d_tagsInStruct  = self.tagsInString_process(d_DCMfileRead['d_DICOM'], v)
                    str_tagValue    = d_tagsInStruct['str_result']
                    setattr(d_DCMfileRead['d_DICOM']['dcm'], k, str_tagValue)
                l_dcm.append(d_DCMfileRead['d_DICOM']['dcm'])
                b_status    = True
                filesAnalyzed += 1

        return {
            'status':           b_status,
            'l_dcm':            l_dcm,
            'str_path':         str_path,
            'l_file':           l_file,
            'filesAnalyzed':    filesAnalyzed
        }

    def outputSaveCallback(self, at_data, **kwags):
        """
        Callback for saving outputs.

        In order to be thread-safe, all directory/file 
        descriptors must be *absolute* and no chdir()'s
        must ever be called!

        Outputs saved:

            * Anon DICOMs if anonymized
            * JPGs of each DICOM
            * Preview strip
            * JSON descriptor file

        """

        pudb.set_trace()

        path                = at_data[0]
        d_outputInfo        = at_data[1]
        str_cwd             = os.getcwd()
        other.mkdir(self.str_outputDir)
        filesSaved          = 0
        other.mkdir(path)

        if self.b_anonDo:
            self.dp.qprint("Saving anonymized DICOMs", level = 3)
            for f, ds in zip(d_outputInfo['l_file'], d_outputInfo['l_dcm']):
                ds.save_as('%s/%s' % (path, f))
                self.dp.qprint("saving: %s/%s" % (path, f), level = 5)
                filesSaved += 1

        # Generate JPGs
        str_

        return {
            'status':       True,
            'filesSaved':   filesSaved
        }

    def process(self, **kwargs):
        """
        A simple "alias" for calling the pftree method.
        """
        d_process       = {}
        d_process       = self.pf_tree.tree_process(
                            inputReadCallback       = self.inputReadCallback,
                            analysisCallback        = self.inputAnalyzeCallback,
                            outputWriteCallback     = self.outputSaveCallback,
                            persistAnalysisResults  = False
        )
        return d_process

    def run(self, *args, **kwargs):
        """
        The run method calls the base class run() to 
        perform initial probe and analysis.

        Then, it effectively calls the method to perform
        the DICOM tag substitution.

        """
        b_status        = True
        d_process       = {}
        b_timerStart    = False

        self.dp.qprint(
                "Starting pfdicom_rev run... (please be patient while running)", 
                level = 1
                )

        for k, v in kwargs.items():
            if k == 'timerStart':   b_timerStart    = bool(v)

        if b_timerStart:
            other.tic()

        # Run the base class, which probes the file tree
        # and does an initial analysis. Also suppress the
        # base class from printing JSON results since those 
        # will be printed by this class
        d_pfdicom       = super().run(
                                        JSONprint   = False,
                                        timerStart  = False
                                    )

        if d_pfdicom['status']:
            str_startDir    = os.getcwd()
            os.chdir(self.str_inputDir)
            if b_status:
                d_process   = self.process()
                b_status    = b_status and d_process['status']
            os.chdir(str_startDir)

        d_ret = {
            'status':       b_status,
            'd_pfdicom':    d_pfdicom,
            'd_process':    d_process,
            'runTime':      other.toc()
        }

        if self.b_json:
            self.ret_dump(d_ret, **kwargs)

        self.dp.qprint('Returning from pfdicom_rev run...', level = 1)

        return d_ret
        