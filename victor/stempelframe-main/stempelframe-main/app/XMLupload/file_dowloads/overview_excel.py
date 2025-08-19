from pathlib import Path
from typing import List, Union

from munch import Munch

from app.XMLupload.calculations.calculate import (
    get_walls,
    find_row_with_max_uc_per_wall,
)
from app.XMLupload.helper_functions import (
    get_diameter_from_profile_name,
    determine_type_strut,
    get_list_columns_letters,
    get_strut_angles,
)
from viktor import File
from viktor.external.spreadsheet import (
    InputCellRange,
    DirectInputCell,
    NamedInputCell,
    render_spreadsheet,
)


class OverviewExcel:
    def __init__(self, results, params: Munch):
        self.template_file_path = (
            Path(__file__).parent.parent
            / "templates"
            / "21.0000-Download blad Viktor v0.2.xlsx"
        )
        self.template_fallback_file_path = (
            Path(__file__).parent.parent / "templates" / "test.xlsx"
        )
        self.params = params
        self.calculation_df_results = results
        self.nb_purlins = len(self.calculation_df_results["results_purlins"])

    def get_input_cells(
        self,
    ) -> List[Union[InputCellRange, DirectInputCell, NamedInputCell]]:
        """This method should return a list of InputCell objects for the SpreadsheetTemplate"""

        headers_cells = [
            DirectInputCell(
                "download algemeen",
                "B",
                1,
                value=self.params.project_general.basics.name_project,
            ),
            DirectInputCell(
                "download algemeen",
                "B",
                2,
                value=self.params.project_general.basics.name_location,
            ),
            DirectInputCell(
                "download algemeen",
                "B",
                3,
                value=self.params.project_general.basics.name_number,
            ),
            DirectInputCell(
                "download algemeen",
                "B",
                4,
                value=self.params.project_general.basics.date,
            ),
        ]
        strut_cells = self.get_struts_table()
        beam_cells = self.get_beams_table()
        overview_cells = self.get_overview_table()
        control_UGT_strut_cells = self.get_control_UGT_strut_cells()
        control_BGT_strut_cells = self.get_control_BGT_strut_cells()

        return (
            headers_cells
            + strut_cells
            + beam_cells
            + overview_cells
            + control_UGT_strut_cells
            + control_BGT_strut_cells
        )

    def get_struts_table(self) -> List[InputCellRange]:
        """Fill the template Excel for the struts ('download stempels') """
        data = self.get_stamps_data()
        nb_columns = len(self.calculation_df_results["stamps_UGT"])
        letter_list = get_list_columns_letters(nb_columns)
        table = []
        for index, column_letter in enumerate(letter_list):
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 1, data=[[data[index][0]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 2, data=[[data[index][1]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 3, data=[[data[index][2]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 4, data=[[data[index][3]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 5, data=[[data[index][4]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 6, data=[[data[index][5]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 7, data=[[data[index][6]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 8, data=[[data[index][7]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 9, data=[[data[index][8]]]
                )
            )
            table.append(
                InputCellRange(
                    "download stempels", column_letter, 10, data=[[data[index][9]]]
                )
            )
        return table

    def get_beams_table(self) -> List[InputCellRange]:
        """Fill the template Excel for the purlins/beam ('download gording') """

        data = self.get_beams_data()
        nb_columns = len(self.walls_calculation_rows)
        letter_list = get_list_columns_letters(nb_columns)
        table = []
        for index, column_letter in enumerate(letter_list):
            table.append(
                InputCellRange(
                    "download gording", column_letter, 1, data=[[data[index][0]]]
                )
            )
            table.append(
                InputCellRange(
                    "download gording", column_letter, 2, data=[[data[index][1]]]
                )
            )
            table.append(
                InputCellRange(
                    "download gording", column_letter, 3, data=[[data[index][2]]]
                )
            )
            table.append(
                InputCellRange(
                    "download gording", column_letter, 4, data=[[data[index][3]]]
                )
            )
            table.append(
                InputCellRange(
                    "download gording", column_letter, 5, data=[[data[index][4]]]
                )
            )
            table.append(
                InputCellRange(
                    "download gording", column_letter, 6, data=[[data[index][5]]]
                )
            )
            table.append(
                InputCellRange(
                    "download gording", column_letter, 7, data=[[data[index][6]]]
                )
            )

        return table

    def get_overview_table(self) -> List[InputCellRange]:
        """Fill the template Excel for the stamps ('stempel') """
        data = self.get_overview_data()
        return [InputCellRange("download overzicht", "A", 2, data=data)]

    def get_control_UGT_strut_cells(self) -> List[DirectInputCell]:
        """Fill the general calculation parameters for the UGT strut control sheet"""
        return [
            DirectInputCell(
                "Controle blad stempels UGT",
                "K",
                4,
                self.params.calculation.general.excentricity,
            ),
            DirectInputCell(
                "Controle blad stempels UGT",
                "K",
                5,
                self.params.calculation.general.k_value_sheetpile,
            ),
        ]

    def get_control_BGT_strut_cells(self) -> List[DirectInputCell]:
        """Fill the general calculation parameters for the BGT strut control sheet"""
        return [
            DirectInputCell(
                "Controle blad stempels BGT",
                "K",
                4,
                self.params.calculation.general.excentricity,
            ),
            DirectInputCell(
                "Controle blad stempels BGT",
                "K",
                5,
                self.params.calculation.general.k_value_sheetpile,
            ),
            DirectInputCell(
                "Controle blad stempels BGT",
                "K",
                8,
                self.params.calculation.calculation_type.point_load_BGT,
            ),
        ]

    def get_stamps_data(self) -> List[List]:
        """Return the data of the struts results to be used in the Excel Template. It's a rectangular list of lists"""
        df_calculation_stamps = self.calculation_df_results["calculations_stamps"]
        df_preface_forces = self.calculation_df_results["calculations_preface_forces"]
        data = []
        for _, strut_row in df_calculation_stamps.iterrows():
            angle_A, angle_B = get_strut_angles(df_preface_forces, strut_row["St."])
            data.append(
                [
                    int(strut_row["St."]),
                    determine_type_strut(df_preface_forces, int(strut_row["St."])),
                    get_diameter_from_profile_name(strut_row["Prof."]),
                    float(strut_row["wa"]),
                    strut_row["fy"],
                    strut_row["lengte"],
                    angle_A,
                    angle_B,
                    round(abs(strut_row["NXi/NXj_UGT"]), 0),
                    round(abs(strut_row["NXi/NXj_BGT"]), 0),
                ]
            )
        return data

    def get_beams_data(self) -> List[List]:
        """Return the data of the beam result to be used in the Excel template. It's a rectangular list of lists"""
        data = []
        for wall_name, wall_row in self.walls_calculation_rows.items():
            data.append(
                [
                    wall_name,
                    wall_row["profiel_naam"],
                    wall_row["n_profiles"],
                    wall_row["Sterkteklasse"],
                    wall_row["N_druk"],
                    wall_row["DZi/DZj"],
                    wall_row["MYi/MYj"],
                ]
            )

        return data

    def get_overview_data(self) -> List[List]:
        """Return the data of the struts results to be used in the Excel Template. It's a rectangular list of lists"""
        df_stamps_table_UGT = self.calculation_df_results["stamps_UGT"]
        df_stamps_table_BGT = self.calculation_df_results["stamps_BGT"]
        df_preface_forces = self.calculation_df_results["calculations_preface_forces"]

        data = []
        for ((_, row_BGT), (_, row_UGT)) in zip(
            df_stamps_table_BGT.iterrows(), df_stamps_table_UGT.iterrows()
        ):
            data.append(
                [
                    int(row_UGT["St."]),
                    determine_type_strut(df_preface_forces, int(row_UGT["St."])),
                    get_diameter_from_profile_name(row_UGT["Prof."]),
                    float(row_UGT["wa"]),
                    row_UGT["fy"],
                    row_UGT["lengte"],
                    row_UGT["uc_maatgevend"],
                    row_BGT["uc_maatgevend"],
                    row_UGT["NXi/NXj_UGT_druk"],
                    row_BGT["NXi/NXj_BGT_druk"],
                ]
            )
        return data

    @property
    def walls_calculation_rows(self):
        wall_calculations_rows = {}
        walls_dict = get_walls(self.calculation_df_results["calculations_purlins"])
        for wall_name, wall_row in find_row_with_max_uc_per_wall(
            walls_dict, self.calculation_df_results["results_purlins"], UGT=True
        ).items():
            wall_calculations_rows[wall_name] = wall_row
        return wall_calculations_rows

    def get_rendered_file(self) -> File:
        """Returns the rendered template spreadsheet and the corresponding file_name"""
        # The rendering of the Excel file will fail if some cells have been wrongly filled because of the last sheet
        # that includes some definitions of conditions based on the results.
        # In case something goes wrong, the fallback is to return the same Excel file without the last sheet.
        try:
            with open(self.template_file_path, "rb") as template:
                template = render_spreadsheet(template, self.get_input_cells())
        except ValueError:
            with open(self.template_fallback_file_path, "rb") as template:
                template = render_spreadsheet(template, self.get_input_cells())

        return template
