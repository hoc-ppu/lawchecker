#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import sys



# print(BASE_PATH)

# add saxonstuff to pythonpath
sys.path.append(str(Path(__file__).parent / 'pythonsaxon'))

# we also need to set an envoroment variable
# I think this is for accessing:
    # libsaxon[EDITION].dylib - Saxon/C library
    # rt directory - Excelsior JET runtime which handles VM calls
    # saxon-data directory
os.environ["SAXONC_HOME"] = str(Path(Path(__file__).parent / 'saxonstuff').resolve())
print(os.environ.get("SAXONC_HOME", None))
# os.environ["SAXONC_HOME"] = r"C:\Users\markj\projects\added-names\python\saxonstuff"

print(sys.path)

# 3rd party imports
# from pythonsaxon import nodekind  # type: ignore
import nodekind  # type: ignore
import saxonc


# xsl_1_Path        = BASE_PATH.parent / 'XSLT' / 'added-names-spo-rest.xsl'
# xsl_2_Path        = BASE_PATH.parent / 'XSLT' / 'post-processing-html.xsl'

# input_Path        = BASE_PATH.parent / 'XML' / '2021-11-19_added-names.xml'
# intermidiate_Path = BASE_PATH.parent / 'XML' / 'intermidiate-from-python.xml'

# out_html_Path     = BASE_PATH / 'output-from-python.html'

# print(f'{xsl_1_Path=}')
# print(f'{xsl_2_Path=}')
# print(f'{input_Path=}')
# print(f'{intermidiate_Path=}')
# print(f'{out_html_Path=}')


# def dir_path(string):
#     if Path.is_dir(string):
#         return string
#     else:
#         raise NotADirectoryError(string)


def dir_path(path):
    if Path(path).is_dir():
        return path
    else:
        raise argparse.ArgumentTypeError(f"readable_dir:{path} is not a valid path")



def main():
    # do cmd line version
    parser = argparse.ArgumentParser(
        description='Create an HTML report of added names from XML downloaded form the Dashboard')

    parser.add_argument('file', metavar='XML File', type=open,
                        help='File path to the XML you wish to process. '
                             'If there are spaces in the path you must use quotes.')

    parser.add_argument('XSLTs', metavar='XSLT Folder', type=dir_path,
                        help='Path to the folder containg the XSLTs wish to run. '
                             'If there are spaces in the path you must use quotes.')


    args = parser.parse_args(sys.argv[1:])
    # print(args)

    input_Path = Path(args.file.name)

    xsl_1_Path = Path(args.XSLTs) / 'added-names-spo-rest.xsl'
    xsl_2_Path = Path(args.XSLTs) / 'post-processing-html.xsl'

    intermidiate_Path = input_Path.with_name('intermidiate-from-python.xml').resolve()

    out_html_Path     = input_Path.with_name('output-from-python.html').resolve()

    print(out_html_Path.resolve())



    with saxonc.PySaxonProcessor(license=False) as proc:
        print(proc.version)

        # 1st XSLT
        xsltproc = proc.new_xslt_processor()

        document = proc.parse_xml(xml_file_name=str(input_Path))

        xsltproc.set_source(xdm_node=document)

        xsltproc.compile_stylesheet(stylesheet_file=str(xsl_1_Path))

        xsltproc.set_jit_compilation(True)

        xsltproc.set_output_file(str(intermidiate_Path))

        xsltproc.transform_to_file()

        # 2nd XSLT
        xsltproc2 = proc.new_xslt_processor()

        document2 = proc.parse_xml(xml_file_name=str(intermidiate_Path))
        xsltproc2.set_source(xdm_node=document2)

        xsltproc2.compile_stylesheet(stylesheet_file=str(xsl_2_Path))

        xsltproc2.set_jit_compilation(True)

        xsltproc2.set_output_file(str(out_html_Path))

        xsltproc2.transform_to_file()

        print('Done.')


if __name__ == '__main__':
    main()
