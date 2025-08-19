from io import BytesIO
from typing import Any, Tuple

import pandas as pd
from munch import Munch
import xml.etree.ElementTree as ET


from viktor.api_v1 import API
from viktor.core import ViktorController, File, ParamsFromFile, Color, UserError
from viktor.geometry import Point, Sphere, Material, Line, CircularExtrusion
from viktor.geometry import CartesianAxes
from viktor.geometry import Group
from viktor.utils import convert_word_to_pdf
from viktor.views import (
    Summary,
    DataResult,
    GeometryAndDataView,
    GeometryAndDataResult,
    PDFView,
    PDFResult)
from viktor.views import GeometryView
from viktor.views import GeometryResult
from viktor.views import DataView
from viktor.views import Label
from viktor.result import DownloadResult, SetParametersResult
from .calculations.data_views_helper import get_data_result_struts, get_data_group_walls
from .file_downloads.overview_excel import OverviewExcel
from .file_downloads.rtf_parser import make_rtf_string_content
from .parametrization import XMLuploadParametrization

from app.XMLupload.calculations.calculate import (
    calculate_all_dataframes,
    run_worker,
    calculate_calamities,
    get_summary_failing_struts_calculation,
    calculations_failing_struts)
from .xml_parsing import XMLParser


# Below functions should be mocked when performing tests on controller methods


def get_self_entity(entity_id):
    """Get entity of XMLuploadController. Method should be mocked for tests."""
    return API().get_entity(entity_id)


class XMLuploadController(ViktorController):
    
    viktor_enforce_field_constraints = True
    
    label = "Technosoft XML"
    parametrization = XMLuploadParametrization
    summary = Summary()

    @ParamsFromFile(file_types=[".xml"])
    def process_file(self, file: File, **kwargs: Any) -> dict:
        """Parse and process the input xml file to fill the entity's params"""
        return XMLParser(file).set_length()

    @GeometryView("Geometrie", view_mode="2D", duration_guess=2)
    def visualize_geometry(self, params: Munch, **kwargs: Any):
        group, labels = self.make_geometry_frame(params)
        return GeometryResult(group, labels)

    @DataView("Stempels & Schoren", duration_guess=10)
    def get_data_view_struts(
        self, params: Munch, entity_id: int, **kwargs: Any
    ) -> DataResult:
        """DataView for the struts, the SLS content depends on the type of calculation"""
        file = get_self_entity(entity_id).get_file()
        beam_table = params.general.beams.staven
        res = calculate_all_dataframes(params, file, beam_table)

        # Calculate calamities
        calamity_BGTs = calculate_calamities(params, file, beam_table)

        data_group = get_data_result_struts(
            params=params, BGT_results=calamity_BGTs, df_results=res
        )

        return DataResult(data_group)

    @GeometryAndDataView("Zijden", view_mode="2D", duration_guess=10)
    def get_wall_data_view(
        self, params: Munch, entity_id: int, **kwargs: Any
    ) -> GeometryAndDataResult:
        """DataView for the walls"""
        file = get_self_entity(entity_id).get_file()
        beam_table = params.general.beams.staven
        res = calculate_all_dataframes(params, file, beam_table)
        group, labels = self.make_geometry_frame(params)
        data = get_data_group_walls(calculation_results=res)
        return GeometryAndDataResult(group, data=data, labels=labels)

    @PDFView("Plots", duration_guess=4)
    def plot_results(self, params: Munch, entity_id: int, **kwargs):
        """Returns the plots of the moments/forces from Technosoft RTF output"""
        file = get_self_entity(entity_id).get_file()
        beam_table = params.general.beams.staven

        root_tree = XMLParser(file)._update_xml_parameters(params, beam_table)
        number_of_materials = len(root_tree.find("Sections"))
        output = run_worker(ET.tostring(root_tree).decode(), rtf=True)
        string_content = make_rtf_string_content(number_of_materials, output)
        file = File.from_data(string_content)

        with file.open_binary() as f:
            pdf = convert_word_to_pdf(f)
        return PDFResult(file=pdf)

    def set_params_in_group(
        self, params: Munch, entity_id: int, **kwargs
    ) -> SetParametersResult:
        """Reset the length of the beams to their original value"""
        file = get_self_entity(entity_id).get_file()
        return SetParametersResult(XMLParser(file).set_length())

    def download_excel(self, params: Munch, entity_id: int, **kwargs) -> DownloadResult:
        """Download summary and calculation Excel"""
        file = get_self_entity(entity_id).get_file()
        beam_table = params.general.beams.staven
        res = calculate_all_dataframes(params, file, beam_table)

        # Get BGT in case of failing strut scenario
        if params.downloads.laden.bgt == "strut_removal":
            summary_df = get_summary_failing_struts_calculation(
                calculations_failing_struts(params, file)
            )

            # For each strut, get max BGT normal from all failing strut scenarios
            res["calculations_stamps"]["fallout_strut"] = ""
            strut_indices = summary_df["BGT_normals"][0].index.values
            for strut_index in strut_indices:
                max_BGT_normal = 0
                fallout_strut = None
                for i, bgt_normal_df in enumerate(summary_df["BGT_normals"]):
                    BGT_normal = bgt_normal_df[strut_index]
                    if BGT_normal < max_BGT_normal:
                        max_BGT_normal = BGT_normal
                        fallout_strut = summary_df.loc[i, "St."]

                # Overwrite BGT normals in original dataframe with max BGT normal from failing strut scenarios
                res["calculations_stamps"].loc[
                    strut_index, "NXi/NXj_BGT"
                ] = max_BGT_normal
                res["calculations_stamps"].loc[
                    strut_index, "fallout_strut"
                ] = fallout_strut

        file_content = OverviewExcel(res, params).get_rendered_file()
        return DownloadResult(file_content, "21.0000-Download blad Viktor v0.2.xlsx")

    def download_updated_xml(
        self, params: Munch, entity_id: int, **kwargs
    ) -> DownloadResult:
        """Download the input xml for Technosoft"""
        file = get_self_entity(entity_id).get_file()

        root_tree = XMLParser(file)._update_xml_parameters(
            params, beam_table=params.general.beams.staven
        )
        updated_xml = BytesIO()
        updated_xml.write(ET.tostring(root_tree))
        return DownloadResult(
            file_content=updated_xml, file_name="Updated_template.xml"
        )

    def download_rtf(self, params: Munch, entity_id: int, **kwargs):
        """Download the full content of the RTF output file from Technosoft as a PDF"""
        file = get_self_entity(entity_id).get_file()
        name = get_self_entity(entity_id).name
        beam_table = params.general.beams.staven

        root_tree = XMLParser(file)._update_xml_parameters(params, beam_table)

        output = run_worker(ET.tostring(root_tree).decode(), rtf=True)
        file = File.from_data(output)

        with file.open_binary() as f:
            pdf = convert_word_to_pdf(f)

        return DownloadResult(file_content=pdf, file_name=f"{name[:-4]}.pdf")

    @staticmethod
    def make_geometry_frame(params: Munch, **kwargs) -> Tuple[Group, list]:
        """Make the geometry of the frame based on the params"""
        node_table = params.general.geometry.nodes
        beam_table = params.general.beams.staven
        spring_table = params.general.SpringSupports.nodes
        fixedsupport_table = params.general.FixedSupports.nodes

        group = Group([])
        labels = []
        if params.visualization.geometry.show_nodes:
            for node in node_table:
                point = Point(node["x"], node["z"], 0)
                sphere = Sphere(
                    point, 0.2, material=Material("node", color=Color(0, 44, 106))
                )
                group.add(sphere)

                point_1 = Point(node["x"] + 0.25, node["z"] + 0.5, 0)
                text_1 = str(node["id"])
                label_1 = Label(point_1, text_1)
                labels.append(label_1)
                point_2 = Point(node["x"] - 0.7, node["z"] + 0.5, 0)
                label_2 = Label(point_2, "kn.")
                labels.append(label_2)

        if params.visualization.geometry.show_springs:
            for spring in spring_table:
                for node in node_table:
                    if spring.NodeID == node.id:
                        point1 = Sphere(
                            Point(node.x, node.z, 0),
                            0.21,
                            material=Material("veer", color=Color(200, 0, 0)),
                        )
                        label1 = Label(Point(node.x, node.z - 0.6, 0), spring.ID)
                        group.add(point1)
                        labels.append(label1)
                        point2 = Point(node.x, node.z - 0.3, 0)
                        label2 = Label(point2, "Veer:")
                        labels.append((label2))

        if params.visualization.geometry.show_fixedsupports:
            for fixedsupport in fixedsupport_table:
                for node in node_table:
                    if fixedsupport.NodeID == node.id:
                        point1 = Sphere(
                            Point(node.x, node.z, 0),
                            0.21,
                            material=Material("veer", color=Color(0, 200, 0)),
                        )
                        label1 = Label(Point(node.x, node.z - 0.6, 0), fixedsupport.ID)
                        group.add(point1)
                        labels.append(label1)
                        point2 = Point(node.x, node.z - 0.3, 0)
                        label2 = Label(point2, "Oplegging:")
                        labels.append((label2))
                        point3 = Point(node.x, node.z - 0.9, 0)
                        label3 = Label(point3, fixedsupport["DirectionXZR"])
                        labels.append((label3))

        for beam in beam_table:
            for node in node_table:
                if node.id == beam.ki:
                    start_point = Point(node.x, node.z, 0)
                if node.id == beam.kj:
                    end_point = Point(node.x, node.z, 0)
            try:
                line = Line(start_point, end_point)
            except UnboundLocalError:
                raise UserError(
                    f"Check de start- en eindknoop voor staaf {beam.id}."
                )
            _beam = CircularExtrusion(
                0.05, line, material=Material("beam", color=Color(50, 50, 50))
            )
            group.add(_beam)

        #       Labels for the beams: strengthclass and profile
        beam_id, beam_profile, beam_sterkte, start_x, start_z, end_x, end_z = (
            [],
            [],
            [],
            [],
            [],
            [],
            [],
        )

        for beam in beam_table:
            for node in node_table:
                if beam.ki == node.id:
                    beam_id.append(beam.id)
                    beam_profile.append(beam.profiel)
                    beam_sterkte.append(beam.strength_class)
                    start_x.append(node.x)
                    start_z.append(node.z)
                if beam.kj == node.id:
                    end_x.append(node.x)
                    end_z.append(node.z)

        label_x_beam = [(sx + ex) / 2 for sx, ex in zip(start_x, end_x)]
        label_z_beam = [(sz + ez) / 2 for sz, ez in zip(start_z, end_z)]

        for x, z, beam_id, profiel, sterkte in zip(
            label_x_beam, label_z_beam, beam_id, beam_profile, beam_sterkte
        ):
            point_1 = Point(x, z + 0.2)
            label_1 = Label(point_1, beam_id)
            labels.append(label_1)
            point_2 = Point(x, z - 0.2)
            label_2 = Label(point_2, profiel)
            labels.append(label_2)
            point_3 = Point(x, z - 0.6)
            label_3 = Label(point_3, sterkte)
            labels.append(label_3)
            point_4 = Point(x, z + 0.6)
            label_4 = Label(point_4, "Staaf:")
            labels.append(label_4)

        # Axis
        x_axes = min([node.x for node in node_table])
        y_axes = min([node.z for node in node_table])

        axes = CartesianAxes(
            Point(x_axes - 3, y_axes - 3, 0), axis_length=3, axis_diameter=0.05
        )
        group.add(axes)
        label_x_axis = Label(Point(x_axes, y_axes - 2.7, 0), "X-as")
        labels.append(label_x_axis)
        label_z_axis = Label(Point(x_axes - 2.7, y_axes, 0), "Z-as")
        labels.append(label_z_axis)

        if params.visualization.geometry.show_labels:
            return group, labels
        return group, []
