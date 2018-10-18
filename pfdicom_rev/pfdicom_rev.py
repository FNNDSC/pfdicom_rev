# System imports
import      os
import      getpass
import      argparse
import      json
import      pprint
import      subprocess
import      uuid
import      shutil

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

        pipe = subprocess.Popen(
            astr_cmd,
            stdout  = subprocess.PIPE,
            stderr  = subprocess.PIPE,
            shell   = True
        )
        bytes_stdout, bytes_stderr = pipe.communicate()
        if pipe.returncode:
            self.dp.qprint( "\n",
                            level   = 3,
                            syslog  = False)
            self.dp.qprint( "An error occured in calling \n%s\n" % pipe.args, 
                            comms   = 'error',
                            level   = 3)
            self.dp.qprint( "The error was:\n%s\n" % bytes_stderr.decode('utf-8'),
                            comms   = 'error',
                            level   = 3)
        return (bytes_stdout.decode('utf-8'), 
                bytes_stderr.decode('utf-8'), 
                pipe.returncode)

    def declare_selfvars(self):
        """
        A block to declare self variables
        """

        #
        # Object desc block
        #
        self.str_desc                   = ''
        self.__name__                   = "pfdicom_rev"
        self.str_version                = "2.0.4"

        self.b_anonDo                   = False
        self.str_dcm2jpgDirRaw          = 'dcm2jpgRaw'
        self.str_dcm2jpgDirResize       = 'dcm2jpgResize'
        self.str_previewFileName        = 'preview.jpg'
        self.str_studyFileName          = 'description.json'
        self.str_serverName             = "http://fnndsc.childrens.harvard.edu"

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
                self.b_anonDo           = True

        # pudb.set_trace()

        # Process some of the kwargs by the base class
        super().__init__(*args, **kwargs)

        self.declare_selfvars()
        self.externalExecutables_set()
        self.anonStruct_set()

        for key, value in kwargs.items():
            if key == 'tagStruct':          tagStruct_process(value)
            if key == 'verbosity':          self.verbosityLevel         = int(value)
            if key == 'server':             self.str_serverName         = value
            if key == 'studyJSON':          self.str_studyFileName      = value

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

    def inputReadCallbackJSON(self, *args, **kwargs):
        """
        Callback for reading files from specific directory.

        In the context of pfdicom_rev, this implies reading
        various contextual JSON files.

        """
        str_path            = ''
        l_file              = []
        b_status            = True
        l_JSONread          = []
        filesRead           = 0

        for k, v in kwargs.items():
            if k == 'l_file':   l_file      = v
            if k == 'path':     str_path    = v

        if len(args):
            at_data         = args[0]
            str_path        = at_data[0]
            l_file          = at_data[1]

        # pudb.set_trace()

        for f in l_file:
            self.dp.qprint("reading: %s/%s" % (str_path, f), level = 5)
            with open('%s/%s' % (str_path, f)) as fl:
                try:
                    d_json  = json.load(fl)
                    b_json  = True
                except:
                    b_json  = False
            b_status        = b_status and b_json
            l_JSONread.append(d_json)
            filesRead       += 1

        if not len(l_file): b_status = False

        return {
            'status':           b_status,
            'l_file':           l_file,
            'str_path':         str_path,
            'l_JSONread':       l_JSONread,
            'filesRead':        filesRead
        }

    def inputReadCallbackMAP(self, *args, **kwargs):
        """
        Callback for reading files from specific directory.

        In the context of pfdicom_rev, this implies reading
        DICOM files and returning the dcm data set.

        """
        b_status            = True

        return {
            'status':           b_status
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

        # pudb.set_trace()

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

    def inputAnalyzeCallbackJSON(self, *args, **kwargs):
        """
        Callback for doing actual work on the read data.

        In the context of 'ReV', the "analysis" in the JSON loop
        essentially means combining the data in the various JSON
        series files into one.

        """
        d_JSONread          = {}
        b_status            = False
        l_json              = []
        l_file              = []
        filesAnalyzed       = 0

        # pudb.set_trace()

        for k, v in kwargs.items():
            if k == 'd_JSONread':   d_JSONread  = v
            if k == 'path':         str_path    = v

        if len(args):
            at_data         = args[0]
            str_path        = at_data[0]
            d_JSONread      = at_data[1]

        for d_JSONfileRead in d_JSONread['l_JSONread']:
            str_path    = d_JSONread['str_path']
            l_file      = d_JSONread['l_file']
            self.dp.qprint("analyzing: %s" % l_file[filesAnalyzed], level = 5)
            try:
                l_json.append(d_JSONfileRead['query']['data'][0])
            except:
                pass
            b_status    = True
            filesAnalyzed += 1

        return {
            'status':           b_status,
            'l_json':           l_json,
            'str_path':         str_path,
            'l_file':           l_file,
            'filesAnalyzed':    filesAnalyzed
        }

    def inputAnalyzeCallbackJSONex(self, *args, **kwargs):
        """
        Callback for doing actual work on the read data.

        In the context of 'ReV', the "analysis" for the 'ex' 
        JSON files simply entails passing the input parameters
        straight back to the caller so as to be available to 
        the output stage.

        """
        d_JSONread          = {}
        b_status            = True
        filesAnalyzed       = 0

        # pudb.set_trace()

        for k, v in kwargs.items():
            if k == 'd_JSONread':   d_JSONread  = v
            if k == 'path':         str_path    = v

        if len(args):
            at_data         = args[0]
            str_path        = at_data[0]
            d_JSONread      = at_data[1]

        if not d_JSONread:  b_status    = False
        else: filesAnalyzed += 1

        return {
            'status':           b_status,
            'd_JSONread':       d_JSONread,
            'filesAnalyzed':    filesAnalyzed
        }

    def inputAnalyzeCallbackMAP(self, *args, **kwargs):
        """
        Callback for doing actual work on the read data.

        """
        b_status            = True

        return {
            'status':           b_status
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

        path                = at_data[0]
        d_outputInfo        = at_data[1]
        str_cwd             = os.getcwd()
        other.mkdir(self.str_outputDir)
        anonFilesSaved      = 0
        jpegsGenerated      = 0
        other.mkdir(path)
        str_relPath         = path.split(self.str_outputDir+'/./')[1]

        def anonymization_do():
            nonlocal    anonFilesSaved
            self.dp.qprint("Saving anonymized DICOMs", level = 3)
            for f, ds in zip(d_outputInfo['l_file'], d_outputInfo['l_dcm']):
                ds.save_as('%s/%s' % (path, f))
                self.dp.qprint("saving: %s/%s" % (path, f), level = 5)
                anonFilesSaved += 1

        def jpegs_generateFromDCM():
            nonlocal    jpegsGenerated
            str_jpgDir          = '%s/%s' % (path, self.str_dcm2jpgDirRaw)
            self.dp.qprint("Generating jpgs from dcm...", 
                            end         = '',
                            level       = 3,
                            methodcol   = 55)
            if not os.path.exists(str_jpgDir):
                other.mkdir(str_jpgDir)
            for f in d_outputInfo['l_file']:
                str_jpgFile     = '%s/%s/%s' % (
                                    path, 
                                    self.str_dcm2jpgDirRaw, 
                                    os.path.splitext(f)[0]
                                    )
                str_execCmd     = self.exec_dcm2jpgConv                         + \
                                    ' +oj +Wh 15 +Fa '                          + \
                                    os.path.join(d_outputInfo['str_path'], f)   + \
                                    ' ' + str_jpgFile
                ret             = self.sys_run(str_execCmd)
                jpegsGenerated  += 1
            self.dp.qprint(" generated %d jpgs." % jpegsGenerated, 
                            syslog      = False,
                            level       = 3)
 
        def jpegs_resize():
            self.dp.qprint( "Resizing jpgs... ",
                            end         = '',
                            level       = 3,
                            methodcol   = 55)
            shutil.copytree(
                '%s/%s' % (path, self.str_dcm2jpgDirRaw),
                '%s/%s' % (path, self.str_dcm2jpgDirResize)
            )
            str_execCmd         = self.exec_jpgResize                           + \
            ' -resize 96x96 -background none -gravity center -extent 96x96 '    + \
                                    '%s/%s/* '   % (path, self.str_dcm2jpgDirResize)
            self.dp.qprint( "done", syslog = False, level = 3)
            ret                 = self.sys_run(str_execCmd)

        def jpegs_middleInSet_tag():
            str_srcFile         = ""
            str_destFile        = ""
            self.dp.qprint( "Tagging 'middle' jpg... ",
                            end         = '',
                            level       = 3,
                            methodcol   = 55)
            # pudb.set_trace()
            l_jpgFiles    = [ \
                f for f in os.listdir('%s/%s' % (path, self.str_dcm2jpgDirRaw)) \
                if os.path.isfile('%s/%s/%s' % (path, self.str_dcm2jpgDirRaw, f)) \
            ]
            if len(l_jpgFiles):
                try:
                    str_jpgMiddle   = l_jpgFiles[int(len(l_jpgFiles)/2)]
                except:
                    str_jpgMiddle   = l_jpgFiles[0]

                str_series      = os.path.basename(path)
                str_srcFile     = '%s/%s/%s' % \
                                    (path, self.str_dcm2jpgDirRaw, str_jpgMiddle)
                str_destFile    = '%s/%s/middle-%s.jpg' % \
                                    (path, self.str_dcm2jpgDirRaw, str_series)
                shutil.copyfile(
                    str_srcFile,
                    str_destFile
                )
                self.dp.qprint( '%s -> %s.jpg' % (str_jpgMiddle, str_series), 
                                syslog = False, level = 3)
            return (str_srcFile, str_destFile)

        def jpegs_previewStripGenerate():
            self.dp.qprint( "Generating preview strip...",
                            level       = 3,
                            methodcol   = 55)
            str_execCmd         = self.exec_jpgPreview                          + \
                                    ' -append '                                 + \
                                    '%s/%s/* ' % (path, self.str_dcm2jpgDirResize)    + \
                                    '%s/%s'     % (path, self.str_previewFileName)
            ret                 = self.sys_run(str_execCmd)

        def jsonSeriesDescription_generate():
            # pudb.set_trace()
            DCM                         = d_outputInfo['l_dcm'][0]
            str_jsonFileName            = '%s-series.json' % path
            try:
                dcm_modalitiesInStudy   = DCM.ModalitiesInStudy
            except:
                dcm_modalitiesInStudy   = "not found"
            json_obj = {
                "query": {
                    "data": [
                        {
                            "SeriesInstanceUID": {
                                "value": '%s' % DCM.SeriesInstanceUID,
                            },
                            "uid": {
                                "value": '%s' % DCM.SeriesInstanceUID,
                            },
                            "SeriesDescription": {
                                "value": '%s' % DCM.SeriesDescription,
                            },
                            "StudyDescription": {
                                "value": '%s' % DCM.StudyDescription,
                            },
                            "ModalitiesInStudy": {
                                    "value": '%s' % dcm_modalitiesInStudy,
                            },
                            "PatientID": {
                                "value": '%s' % DCM.PatientID,
                            },
                            "PatientName": {
                                "value": '%s' % DCM.PatientName,
                            },
                            #  extra fun
                            "details": {
                                "series": {
                                    "uid":          '%s' % DCM.SeriesInstanceUID,
                                    "description":  '%s' % DCM.SeriesDescription,
                                    "date":         '%s' % DCM.SeriesDate,
                                    "data":         [str_relPath + '/' + s for s in  d_outputInfo['l_file']],
                                    "files":        str(len(d_outputInfo['l_file'])),
                                    "preview": {
                                        "blob":     '',
                                        "url":      str_relPath + "/preview.jpg",
                                    },
                                },
                            },
                        }
                    ],
                },
            }
            with open(str_jsonFileName, 'w') as f:
                json.dump(json_obj, f, indent = 4)

        def jsonExampleSummary_generate(str_image):

            def newSet_create(str_ex, str_image):
                d_set       = {
                    'name': str_ex,
                    'imageLocation': [str_image]
                }
                return d_set

            # if the ex.json file exists, read it and append
            # the image location to the internal list,
            # otherwise create a new file.
            d_summary                   = {}
            str_ex                      = os.path.basename(os.path.dirname(str_relPath))
            str_monthFileName           = '%s/%s.json' % (os.path.dirname(os.path.dirname(path)),'ex')
            if os.path.exists(str_monthFileName):
                with open(str_monthFileName) as jf:
                    d_summary = json.load(jf)
                if str_ex in d_summary:
                    d_summary[str_ex]['imageLocation'].append(str_image)
                else:
                    d_summary[str_ex] = newSet_create(str_ex, str_image)
            else:
                d_summary[str_ex]       = newSet_create(str_ex, str_image)
            with open(str_monthFileName, 'w') as mf:
                json.dump(d_summary, mf, indent = 4)

        if self.b_anonDo: anonymization_do()
        jpegs_generateFromDCM()
        jpegs_resize()
        str_srcImage, str_destImage = jpegs_middleInSet_tag()
        jpegs_previewStripGenerate()
        jsonSeriesDescription_generate()
        jsonExampleSummary_generate(str_destImage)

        return {
            'status':       True,
            'filesSaved':   jpegsGenerated
        }

    def outputSaveCallbackJSON(self, at_data, **kwags):
        """
        Callback for saving outputs.

        In order to be thread-safe, all directory/file 
        descriptors must be *absolute* and no chdir()'s
        must ever be called!

        Outputs saved:

            * JSON study descriptor file
            * index.html

        """

        def str_indexHTML_create(str_path):
            """
            Return a string to be saved in 'index.html' 
            """
            fieldFind       = lambda str_url, field: str_url.split(field)[0].split('/')[-1] 
            str_yr          = fieldFind(str_path, '-yr')
            str_mo          = fieldFind(str_path, '-mo')
            str_ex          = fieldFind(str_path, '-ex')
            str_html = """
                <html>
                    <head>
                        <title>FNNDSC</title>
                        <meta http-equiv="refresh" content="0; URL=%s?year=%s&month=%s&example=%s">
                        <meta name="keywords" content="automatic redirection">
                    </head>
                    <body style="background: black;" text="lightgreen">
                    </body>
                </html>

            """ % (self.str_serverName, str_yr, str_mo, str_ex)
            return str_html
        #pudb.set_trace()
        path                = at_data[0]
        d_outputInfo        = at_data[1]
        str_cwd             = os.getcwd()
        other.mkdir(self.str_outputDir)
        jsonFilesSaved      = 0
        other.mkdir(path)
        str_relPath         = './'
        try:
            str_relPath     = path.split(self.str_outputDir+'/./')[1]
        except:
            str_relPath     = './'
        filesSaved          = 0

        json_study          = {
            'data': d_outputInfo['l_json']
        }

        with open('%s/%s' % (path, self.str_studyFileName), 'w') as f:
            json.dump(json_study, f, indent = 4)
            filesSaved += 1 
        f.close()
        str_html = str_indexHTML_create(path)
        with open('%s/index.html' % (path), 'w') as f:
            f.write(str_html)
            filesSaved += 1 
        f.close()

        return {
            'status':       True,
            'filesSaved':   filesSaved
        }

    def outputSaveCallbackJSONex(self, at_data, **kwags):
        """
        Callback for saving outputs.

        In order to be thread-safe, all directory/file 
        descriptors must be *absolute* and no chdir()'s
        must ever be called!

        Outputs saved:

            * JSON study descriptor file
            * index.html

        """

        def table_generate(str_title, lstr_images):
            """
            Generate a table of thumbnails about a list of images
            """
            lstr_images     = [i for i in lstr_images if 'mo/' in i]
            lstr_i          = [i.split('mo/')[1] for i in lstr_images]
            str_tableStyle  = """
            <style type="text/css">
            .tg {background-color: #000;}
            .tg {border-collapse:collapse;border-spacing:0;}
            .tg td{font-family:Arial, sans-serif;font-size:14px;padding:2px 2px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;border-color:black;}
            .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:2px 2px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;border-color:black;}
            .tg tr:hover{cursor: pointer; background-color: #fff;}
            .tg .tg-0lax{text-align:left;vertical-align:middle;}
            a {text-decoration: none; color: #999;}
            </style>
            """
            # Create the header row
            str_th = ""
            str_th += """<th class="tg-0lax" style="text-align: center;"></th>\n"""
            for str_image in lstr_i:
                str_header = str_image.split('ex/')[1].split('/dcm2jpg')[0]
                str_header = str_header.split('-')[0][0:14]
                str_th += """<th class="tg-0lax" style="text-align: center;">%s</th>\n""" % str_header
            # Now create the image row
            str_td = ""
            str_td += """<td class="tg-0lax" style="font-size: 18px; padding 0px 10px"><a href=%s>%s</a</td>\n""" % (str_title, str_title)
            for str_image in lstr_i:
                str_htmlImage   = '<img src="%s" width="128" height="128";">' % str_image
                str_td          += """<td class="tg-0lax">%s</td>\n""" % str_htmlImage
            # And combine into a table:
            str_table = """
            %s
            <table class="tg">
               <tr>
               %s
               </tr>
               <tr>
               %s
               </tr>
            </table>
            <br>
            """ % (str_tableStyle, str_th, str_td)
            return str_table

        def str_indexHTML_create(str_heading, d_ex):
            """
            Return a string to be saved in 'index.html' 
            """
            str_html        = """
<!DOCTYPE html>
<html>
<head>
        <title>%s</title>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
</head>

<body style = "background-color: #1d1f21; color: white">
    <h1 style="font-family: Arial, sans-serif;">%s</h1>
    <p style="font-family: Arian, sans-serif;">Click on an image set below.</p>
    <br>
            """ % (str_heading, str_heading)
            str_table = ""
            for str_key, d_singleEx in sorted(d_ex.items()):
                l_images = d_singleEx['imageLocation']
                str_table += table_generate(str_key, l_images)
            str_html += """
            %s
<script>
    $(".tg tr").click(function(){
        var href = $(this).find("a").attr("href");
        if(href) {
            window.location = href;
        }
    });
</script>
</body>
</html>
            """ % str_table

            return str_html

        # pudb.set_trace()
        path                = at_data[0]
        d_JSONex            = at_data[1]
        str_cwd             = os.getcwd()
        other.mkdir(self.str_outputDir)
        jsonFilesSaved      = 0
        other.mkdir(path)
        str_relPath         = './'
        try:
            str_relPath     = path.split(self.str_outputDir+'/./')[1]
        except:
            str_relPath     = './'
        filesSaved          = 0

        str_html = str_indexHTML_create(
                        str_relPath,
                        d_JSONex['d_JSONread']['l_JSONread'][0]
        )
        with open('%s/index.html' % (path), 'w') as f:
            f.write(str_html)
            filesSaved += 1 
        f.close()

        return {
            'status':       True,
            'filesSaved':   filesSaved
        }


    def outputSaveCallbackMAP(self, at_data, **kwags):
        """
        Callback for saving outputs.

        In order to be thread-safe, all directory/file 
        descriptors must be *absolute* and no chdir()'s
        must ever be called!

        Outputs saved:

            * JSON study descriptor file
            * index.html

        """
        filesSaved          = 0

        return {
            'status':       True,
            'filesSaved':   filesSaved
        }

    def processDCM(self, **kwargs):
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

    def processJSON(self, **kwargs):
        """
        A simple "alias" for calling the pftree method.
        """
        d_process       = {}
        d_process       = self.pf_tree.tree_process(
                            inputReadCallback       = self.inputReadCallbackJSON,
                            analysisCallback        = self.inputAnalyzeCallbackJSON,
                            outputWriteCallback     = self.outputSaveCallbackJSON,
                            persistAnalysisResults  = False
        )
        return d_process

    def processJSONex(self, **kwargs):
        """
        A simple "alias" for calling the pftree method.
        """
        d_process       = {}
        d_process       = self.pf_tree.tree_process(
                            inputReadCallback       = self.inputReadCallbackJSON,
                            analysisCallback        = self.inputAnalyzeCallbackJSONex,
                            outputWriteCallback     = self.outputSaveCallbackJSONex,
                            persistAnalysisResults  = False
        )
        return d_process        
    
    def processMAP(self, **kwargs):
        """
        A simple "alias" for calling the pftree method.
        """
        d_process       = {}
        d_process       = self.pf_tree.tree_process(
                            inputReadCallback       = self.inputReadCallbackMAP,
                            analysisCallback        = self.inputAnalyzeCallbackMAP,
                            outputWriteCallback     = self.outputSaveCallbackMAP,
                            persistAnalysisResults  = False
        )
        d_library = {
            "data": list(self.pf_tree.d_inputTree.keys())
            }
        self.dp.qprint("mapping: %s" % d_library, level = 1)
        with open("%s/map.json" % self.str_inputDir, 'w') as outfile:
            json.dump(d_library, outfile, indent = 4)
        
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

        func_process    = self.processDCM
        str_analysis    = 'DICOM analysis'

        for k, v in kwargs.items():
            if k == 'timerStart':   b_timerStart    = bool(v)
            if k == 'func_process': func_process    = v
            if k == 'description':  str_analysis    = v          

        self.dp.qprint(
                "Starting pfdicom_rev %s... (please be patient while running)" % \
                    str_analysis, 
                level = 1
                )

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
                d_process   = func_process()
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

        self.dp.qprint('Returning from pfdicom_rev %s...' % str_analysis, level = 1)

        return d_ret
        