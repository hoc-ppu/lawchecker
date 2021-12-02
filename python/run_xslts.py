#!/usr/bin/env python3

from pathlib import Path
import sys

BASE_PATH = Path(__file__).parent

# add saxonstuff path
sys.path.append(str(BASE_PATH / 'saxonstuff'))

# 3rd party imports
from saxonstuff import saxonc

# BASE_PATH = '/Users/mark/projects/play_with_saxon_c/'


XSL_1_PATH        = BASE_PATH.parent / 'XSLT' / 'added-names-spo-rest.xsl'
XSL_2_PATH        = BASE_PATH.parent / 'XSLT' / 'post-processing-html.xsl'

INPUT_PATH        = BASE_PATH.parent / 'XML' / '2021-11-19_added-names.xml'
INTERMIDIATE_PATH = BASE_PATH.parent / 'XML' / 'intermidiate-from-python.xml'

OUT_HTML_PATH     = BASE_PATH / 'output-from-python.html'

def main():
    with saxonc.PySaxonProcessor(license=False) as proc:
        print(proc.version)

        # 1st XSLT
        xsltproc = proc.new_xslt_processor()

        document = proc.parse_xml(xml_file_name=str(INPUT_PATH))

        xsltproc.set_source(xdm_node=document)

        xsltproc.compile_stylesheet(stylesheet_file=str(XSL_1_PATH))

        xsltproc.set_jit_compilation(True)

        xsltproc.set_output_file(str(INTERMIDIATE_PATH))

        xsltproc.transform_to_file()

        # 2nd XSLT
        xsltproc2 = proc.new_xslt_processor()

        document2 = proc.parse_xml(xml_file_name=str(INTERMIDIATE_PATH))
        xsltproc2.set_source(xdm_node=document2)

        xsltproc2.compile_stylesheet(stylesheet_file=str(XSL_2_PATH))

        xsltproc2.set_jit_compilation(True)

        xsltproc2.set_output_file(str(OUT_HTML_PATH))

        xsltproc2.transform_to_file()

        print('Done.')


if __name__ == '__main__':
    main()
