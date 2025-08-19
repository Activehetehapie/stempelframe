import unittest
from io import BytesIO
from unittest.mock import patch

from viktor.result import SetParamsResult, DownloadResult
from viktor.views import GeometryResult, PDFResult, DataResult, GeometryAndDataResult

from tests.utils.mock_entities import Mock_XMLuploadEntity
from app.XMLupload.controller import XMLuploadController
from tests.utils.utils import get_method_names


def mock_get_self_entity(entity_id):
    """Mock method to get self entity"""
    return Mock_XMLuploadEntity


def mock_run_worker(input_file: str, rtf: bool = False, message: str = "") -> str:
    """Mock method to run worker"""
    with open('tests/documents/output.rtf' if rtf else 'tests/documents/output.txt', 'rb') as f:
        return str(BytesIO(f.read()).getvalue(), "ISO-8859-1")


def mock_word_to_pdf(word_file):
    """Mock method to turn word into pdf (happens through external api)"""
    return word_file


def mock_render_spreadsheet(template, input_cells):
    """Mock method to render spreasheet (happens through external api)"""
    return template


@patch("app.XMLupload.controller.get_self_entity", mock_get_self_entity)
@patch("app.XMLupload.calculations.calculate.run_worker", mock_run_worker)
@patch("app.XMLupload.controller.run_worker", mock_run_worker)
@patch("app.XMLupload.controller.convert_word_to_pdf", mock_word_to_pdf)
@patch("app.XMLupload.file_downloads.overview_excel.render_spreadsheet", mock_render_spreadsheet)
class TestController(unittest.TestCase):

    # Make XML upload controller instance, and fill with params from mock entity
    controller_instance = XMLuploadController()
    kwargs = {
        'params': Mock_XMLuploadEntity.last_saved_params,
        'name': Mock_XMLuploadEntity.name,
        'entity_id': Mock_XMLuploadEntity.id,
    }

    def test_if_all_methods_covered(self):
        """Checks if the defined methods on the controller and the methods in this test class correspond."""
        specified_names = get_method_names(self.__class__, True)
        expected_names = get_method_names(XMLuploadController, True)
        for expected_name in expected_names:
            found = False
            for specified_name in specified_names:
                if expected_name in specified_name:
                    found = True
                    break
            if not found:
                print(f"\n\nWARNING: \nMethod '{expected_name}' is not tested.\n")

    def test_get_wall_data_view(self):
        res = self.controller_instance.get_wall_data_view(self.controller_instance, **self.kwargs)
        self.assertIsInstance(res, GeometryAndDataResult)

    def test_download_rtf(self):
        res = self.controller_instance.download_rtf(**self.kwargs)
        self.assertIsInstance(res, DownloadResult)

    def test_set_params_in_group(self):
        res = self.controller_instance.set_params_in_group(**self.kwargs)
        self.assertIsInstance(res, SetParamsResult)

    def test_get_data_view_struts(self):
        res = self.controller_instance.get_data_view_struts(self.controller_instance, **self.kwargs)
        self.assertIsInstance(res, DataResult)

    def test_download_updated_xml(self):
        res = self.controller_instance.download_updated_xml(**self.kwargs)
        self.assertIsInstance(res, DownloadResult)

    def test_make_geometry_frame(self):
        res = self.controller_instance.make_geometry_frame(**self.kwargs)
        self.assertTrue(res)

    def test_visualize_geometry(self):
        res = self.controller_instance.visualize_geometry(self.controller_instance, **self.kwargs)
        self.assertIsInstance(res, GeometryResult)

    def test_download_excel(self):
        res = self.controller_instance.download_excel(**self.kwargs)
        self.assertIsInstance(res, DownloadResult)

    def test_plot_results(self):
        res = self.controller_instance.plot_results(self.controller_instance, **self.kwargs)
        self.assertIsInstance(res, PDFResult)
