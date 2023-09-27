"""
Wrappers for some common XML processing tasks. This module relies on SaxonC HE 12.2.0:
https://pypi.org/project/saxonche/
https://www.saxonica.com/saxon-c/documentation12/index.html#!api/saxon_c_python_api
"""

from saxonche import PySaxonProcessor, PyXdmNode, PyXdmValue, PySaxonApiError

from . import pp_log


def load_xml(xml_file_path: str) -> PyXdmNode | None:
    """
    Load an XML document from `xml_file_path`.
    """

    pp_log.logger.info(f"Loading XML from <{xml_file_path}>...")

    return_value = None

    with PySaxonProcessor(license=False) as processor:

        try:

            result = processor.parse_xml(xml_file_name=xml_file_path)

            if type(result) is PyXdmNode:

                return_value = result

                pp_log.logger.info(f"XML loaded from <{xml_file_path}>.")

            else:

                pp_log.logger.error(f"<{xml_file_path}> could not be read as XML.")

        except TypeError as e:

            pp_log.logger.error(
                f"`load_xml` expects `xml_file_path` to be a string. ({e})"
            )

        except PySaxonApiError as e:

            pp_log.logger.error(f"<{xml_file_path}> could not be parsed as XML. ({e})")

        except Exception as e:

            pp_log.logger.critical(f"An unexpected error occurred. ({e})")

    return return_value


def transform_xml(
    xml_file_path: str,
    xsl_file_path: str,
    output_xml_file_path: str | None = None,
    parameters: dict = {},
) -> PyXdmValue | None:
    """
    Transform XML using XSLT and return the result.
    """

    pp_log.logger.info("Transforming XML...")

    return_value = None

    with PySaxonProcessor(license=False) as processor:

        try:
            xslt_processor = processor.new_xslt30_processor()

            executable = xslt_processor.compile_stylesheet(
                stylesheet_file=xsl_file_path
            )

            executable.set_result_as_raw_value(True)
            executable.set_initial_match_selection(file_name=xml_file_path)

            # If we have some parameters to pass into the stylesheet...
            if type(parameters) is dict:

                for name, value in parameters.items():

                    # Convert `value` to a PyXdmNode
                    xdm_value = processor.make_string_value(value)

                    # Set parameter on `executable`
                    executable.set_parameter(name, xdm_value)

            result = executable.apply_templates_returning_value()

            if type(result) is PyXdmValue:

                pp_log.logger.info("XML transformed successfully.")

                return_value = result

                if (type(output_xml_file_path) is str) and (
                    len(output_xml_file_path) > 0
                ):

                    executable.apply_templates_returning_file(
                        output_file=output_xml_file_path
                    )

                    pp_log.logger.info(
                        f"Transformed XML written to <{output_xml_file_path}>."
                    )

            else:

                pp_log.logger.error("There was a problem in the XSL transformation.")

        except PySaxonApiError as e:

            pp_log.logger.error(f"A problem occurred during the transformation. ({e})")

        except Exception as e:

            pp_log.logger.critical(f"An unexpected error occurred. ({e})")

    return return_value
