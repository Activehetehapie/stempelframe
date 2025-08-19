import copy
from string import ascii_uppercase
from typing import List, Dict
import xml.etree.ElementTree as ET

import pandas as pd
from io import BytesIO

from munch import Munch
from numpy import arccos, degrees
from pandas import DataFrame, Series
from viktor.core import progress_message
from viktor.errors import ExecutionError
from viktor.views import DataStatus

from app.XMLupload.calculations.calculation_preface_forces import (
    get_df_calculations_preface_forces,
    get_df_results_preface_forces)
from app.XMLupload.calculations.calculation_purlins import (
    get_df_calculations_purlins,
    get_df_results_purlins,
    get_df_displacement)
from app.XMLupload.calculations.calculation_stamps import (
    get_df_calculations_stamps,
    build_df_results_stamps_UGT,
    build_df_results_stamps_BGT)

from app.XMLupload.constants import RWW_DICT
from app.XMLupload.helper_functions import iter_all_strings, determine_type_strut
from app.XMLupload.xml_parsing import XMLParser
from viktor import UserError, File
from viktor.external.generic import GenericAnalysis
from viktor.geometry import Vector, Line, Point
from viktor.utils import memoize


def parse_technosoft_output_file(output_file: BytesIO) -> Dict[str, pd.DataFrame]:
    """Parse the output file from a Technosoft analysis and and map the result into relevant dataframes"""
    dataframe_names_mapping = {
        "df_stramienlijnen": "STRAMIENLIJNEN",
        "df_layers": "NIVEAUS",
        "df_materials": "MATERIALEN",
        "df_profiles_start": "PROFIELEN [mm]",
        "df_profiles_continuation": "PROFIELEN vervolg [mm]",
        "df_nodes": "KNOPEN",
        "df_bars": "STAVEN",
        "df_springsupports": "VEREN",
        "df_supports": "VASTE STEUNPUNTEN",
        "df_beddings": "BEDDINGEN",
        "df_barloads_UGT": "STAAFBELASTINGEN   B.G:1 UGT",
        "df_barloads_BGT": "STAAFBELASTINGEN   B.G:2 BGT",
        "df_barforces_BGT": "STAAFKRACHTEN  B.C:2 Vervorming",
        "df_barforces_UGT": "STAAFKRACHTEN  B.C:1 Sterkte",
        "df_displacement_BGT": "TUSSENPUNTEN VERPLAATSINGEN  B.C:2 Vervorming",
        "df_belastingcombinaties": "BELASTINGCOMBINATIES",
    }

    dict_dataframes = {}
    for key, value in dataframe_names_mapping.items():
        dict_dataframes[key] = create_table(
            output_file.getvalue(), value, RWW_DICT[value]["columns"]
        )
        if value == "PROFIELEN vervolg [mm]":
            dict_dataframes["df_profiles"] = dict_dataframes["df_profiles_start"].merge(
                dict_dataframes["df_profiles_continuation"], on="Prof.", how="left"
            )
        elif value == "STAVEN":
            dict_dataframes["df_bars_original"] = dict_dataframes["df_bars"].copy()
        elif value == "STAAFKRACHTEN  B.C:1 Sterkte":
            dict_dataframes[key]["NXi/NXj"] = dict_dataframes[key]["NXi/NXj"][
                dict_dataframes[key]["NXi/NXj"].str.strip() != ""
            ]
            dict_dataframes[key]["DZi/DZj"] = dict_dataframes[key]["DZi/DZj"][
                dict_dataframes[key]["DZi/DZj"].str.strip() != ""
            ]
            dict_barforce_UGT = dict_dataframes[key].set_index("St.").to_dict()
            dict_dataframes[key]["NXi/NXj"] = dict_dataframes[key]["St."].map(
                dict_barforce_UGT["NXi/NXj"]
            )

    return dict_dataframes


def calculate_all_dataframes(
    params: Munch,
    file: File,
    beam_table: List[Munch],
    message: str = "",
    point_load: bool = False,
) -> Dict[str, DataFrame]:
    """Launch the Technosoft calculations and process the results into Dataframes.

    :params:
    file: is the uploaded entity file, this is the 'raw' xml content of the structure. It is updated afterwards if
    the user changes some fields in the parametrization.
    beam_table: is the TableInput of the beam that can be modified when performing different types of analysis.
    When a beam is disactivated, it has effects on this beam_table and the xml is updated accordingly.
    point_load: if true, BGT is calculated assuming point load calamity.
    """

    root_tree = XMLParser(file)._update_xml_parameters(params, beam_table)

    output = run_worker(ET.tostring(root_tree).decode(), message=message)
    output_file = BytesIO(output.encode("utf-8"))
    technosoft_parsed_outputs = parse_technosoft_output_file(output_file)

    df_calculations_stamps = get_df_calculations_stamps(
        technosoft_parsed_outputs, params, point_load
    )
    df_results_stamps_UGT = build_df_results_stamps_UGT(df_calculations_stamps)
    df_results_stamps_BGT = build_df_results_stamps_BGT(df_calculations_stamps)
    df_calculations_purlins = get_df_calculations_purlins(
        technosoft_parsed_outputs, params
    )
    df_results_purlins = get_df_results_purlins(df_calculations_purlins)
    df_calculations_preface_forces = get_df_calculations_preface_forces(
        df_calculations_purlins,
        df_calculations_stamps,
        df_nodes=technosoft_parsed_outputs["df_nodes"],
        params=params,
    )
    df_results_preface_forces = get_df_results_preface_forces(
        df_calculations_preface_forces
    )
    df_displacement = get_df_displacement(
        df_calculations_purlins, technosoft_parsed_outputs["df_displacement_BGT"]
    )
    return {
        "calculations_stamps": df_calculations_stamps,
        "stamps_BGT": df_results_stamps_BGT,
        "stamps_UGT": df_results_stamps_UGT,
        "calculations_purlins": df_calculations_purlins,
        "results_purlins": df_results_purlins,
        "results_preface_forces": df_results_preface_forces,
        "calculations_preface_forces": df_calculations_preface_forces,
        "displacement": df_displacement,
    }


def calculate_calamities(
    params: Munch, file: File, beam_table: List[Munch]
) -> Dict[str, List[dict]]:
    """Calculate BGT for default case and calamities depending on parametrization settings."""

    # Calculate regular BGT
    data_dict_stamps_BGT = {}
    if params.calculation.BGT:
        temp_df_results = calculate_all_dataframes(
            params, file, beam_table, "Berekenen BGT.", False
        )
        data_dict_stamps_BGT = make_data_dict_stamps_BGT_point_load(
            temp_df_results["stamps_BGT"],
            temp_df_results["calculations_preface_forces"],
        )

    # Calculate BGT in case of strut removal
    data_dict_stamps_strut_removal_BGT = {}
    if "strut_removal" in params.calculation.calamity:
        summary_df = get_summary_failing_struts_calculation(
            calculations_failing_struts(params, file)
        )
        temp_df_results = calculate_all_dataframes(
            params, file, beam_table, "Berekenen scenario met puntlast."
        )
        data_dict_stamps_strut_removal_BGT = make_data_dict_stamps_BGT_strut_removal(
            summary_df, temp_df_results["calculations_preface_forces"]
        )

    # Calculate BGT in case of point load
    data_dict_stamps_point_load_BGT = {}
    if "point_load" in params.calculation.calamity:
        temp_df_results = calculate_all_dataframes(
            params, file, beam_table, "Berekenen scenario met puntlast.", True
        )
        data_dict_stamps_point_load_BGT = make_data_dict_stamps_BGT_point_load(
            temp_df_results["stamps_BGT"],
            temp_df_results["calculations_preface_forces"],
        )

    return {
        "BGT": data_dict_stamps_BGT,
        "strut_removal": data_dict_stamps_strut_removal_BGT,
        "point_load": data_dict_stamps_point_load_BGT,
    }


def calculations_failing_struts(
    params: Munch, file: File
) -> Dict[int, Dict[str, DataFrame]]:
    """Returns the calculation results for the analysis where a strut is failing.
    A failing strut is modelled as a strut with a Young Modulus assigned to 0 and is discriminated as a special
    section with a stamp 'B121/5'.
    The failing struts are tested one at a time.
    """
    index_updated = []
    profile_combinations = []
    all_results = {}
    beam_table = params.general.beams.staven
    for index, row in enumerate(beam_table):
        stamp_failure = "B121/5"
        new_beam_table = copy.deepcopy(beam_table)
        if index not in index_updated:
            if row["profiel"].startswith("B"):
                new_beam_table[index]["profiel"] = stamp_failure
                index_updated.append(index)

        profiles = [
            row["profiel"] for row in new_beam_table
        ]  # ['HEB400', 'HEB400', ..., 'B406/10']
        if (
            profiles not in profile_combinations
        ):  # is this sequence of beams has not been analysed yet
            profile_combinations.append(profiles)
            df_results = calculate_all_dataframes(
                params,
                file,
                new_beam_table,
                message=f"Berekenen scenario {index}/{len(beam_table)} met stempelverwijdering.",
            )
            if index > 0:
                all_results[index + 1] = df_results
            else:  # index=0 corresponds to the case where no strut is deactivated
                all_results[index] = df_results

    return all_results


def get_summary_failing_struts_calculation(
    res: Dict[int, Dict[str, DataFrame]]
) -> DataFrame:
    """Return a summary Dataframe of the BGT calculations with of the strategy `strut_removal`
    Naam :str: Strut name that has been removed
    max_uc_strut :int: strut id for which the highest u.c. has been calculated
    max_uc :float: highest (BGT maatgevend) u.c. calculated among all the struts, except the one removed
    """
    df_results = DataFrame()
    for strut_index, all_df_results in res.items():
        if strut_index != 0:
            df_stamps_BGT = all_df_results["stamps_BGT"]
            df_normal_force_BGT = all_df_results["calculations_stamps"]["NXi/NXj_BGT"]
            max_uc_row = df_stamps_BGT.loc[df_stamps_BGT["uc_maatgevend"].idxmax()]

            df_results = df_results.append(
                {
                    "St.": str(strut_index),
                    "Prof.": max_uc_row["Prof."],
                    "BGT_normals": df_normal_force_BGT,
                    "max_uc": max_uc_row["uc_maatgevend"],
                    "max_uc_strut": max_uc_row["St."],
                },
                ignore_index=True,
            )
    return df_results


def get_row(path: bytes, target_string: str, start_row: int = 0) -> int:
    path = BytesIO(path)
    with path as f:
        lines = f.readlines()
        target_row = 0
        for index, line in enumerate(lines):
            line = line.decode("utf-8")
            if (line[: len(target_string)] == target_string) & (index >= start_row):
                target_row = index
                break
    return target_row


def create_table(
    file_path: bytes, table_name: str, table_columns: List[str]
) -> DataFrame:
    """Create a DataFrame for the category 'table_name' from the technosoft results stored in 'file_path'"""
    header_start_row = get_row(file_path, table_name)
    header_end_row = get_row(file_path, "-----", header_start_row + 2)
    file_path = BytesIO(file_path)
    with file_path as f:
        lines = f.readlines()
    data = []

    for line in lines[header_end_row + 1 :]:
        line = line.decode("utf-8")
        if line.split()[0].isdigit():
            if not len(line.split()) == len(table_columns):
                if table_name in [
                    "STAAFKRACHTEN  B.C:1 Sterkte",
                    "STAAFKRACHTEN  B.C:2 Vervorming",
                ]:
                    line_data = line.split()
                    if len(table_columns) - len(line.split()) == 1:
                        line_data.insert(2, "")
                    if len(table_columns) - len(line.split()) == 2:
                        line_data.insert(2, "")
                        line_data.insert(2, "")

                    data.append(line_data)
                else:
                    line_data = line.split()
                    for add in range(len(table_columns) - len(line.split())):
                        line_data.append("")
                    data.append(line_data)
            else:
                data.append(line.split())
        else:
            if "gronddruk" in line.lower() and table_name in [
                "TUSSENPUNTEN VERPLAATSINGEN  B.C:2 Vervorming"
            ]:  # Skip 'som gronddruk lines'
                continue
            else:
                break
    df = pd.DataFrame.from_records(data, columns=table_columns)
    return df


@memoize
def run_worker(input_file: str, rtf: bool = False, message: str = "") -> str:
    """Runs the worker and memoizes the result such that it can be used in 'Resultaten' and 'Rapport
    views.
    executable_key can be "txt_export" in this case."""
    executable_key = "rtf_export" if rtf else "txt_export"
    out_filename = "output.rtf" if rtf else "output.txt"
    progress_message(message=f"Running TechnoSoft Raamwerken worker... {message}")
    generic_analysis = GenericAnalysis(
        files=[("input.xml", BytesIO(input_file.encode()))],
        executable_key=executable_key,
        output_filenames=[out_filename],
    )

    try:
        generic_analysis.execute(timeout=600)
    except TimeoutError as e:
        raise UserError(
            f"Timeout tijdens draaien Raamwerken: geen response binnen de gestelde tijdslimiet (={600} seconden). "
            f"Controleer status Raamwerken integratie."
        )
    except ConnectionError as e:
        raise UserError(
            "Kan geen connectie maken met worker. "
            "Controleer de status van de integraties rechtsboven in het app dashboard."
        )
    except ExecutionError as e:
        raise UserError("Fout tijdens runnen van Raamwerken worker.")
    try:
        out_file = generic_analysis.get_output_file(out_filename)
    except AttributeError:  # generic_analysis.get_output_file() may result in None for file formats.
        raise UserError(
            "Fout: Er kan geen output gegenereerd worden met deze input. Check of .xml file correct is in Raamwerken."
        )
    try:
        return str(out_file.getvalue(), "ISO-8859-1")
    except AttributeError:
        raise UserError(
            "Fout: Er kan geen output gegenereerd worden met deze input. Check of .xml file correct is in Raamwerken."
        )


def show_df(df_calculations_stamps):
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None
    ):  # more options can be specified also
        print(df_calculations_stamps)


# ======================================================================================================================
#
#                                               WALL FUNCTIONS
#
# ======================================================================================================================


def get_walls(df_calculations_purlins) -> Dict[str, List]:
    """Return a dictionary containing all the walls of the excavation in a format {'A': ['1', '2', '3'], ...} where
    the wall 'A' is made of 3 beams 1, 2 and 3.
    If the vector direction of two consecutive beams is the same, then both belong to the same wall,
    otherwise a new wall is created.
    """
    df_calculations_purlins = df_calculations_purlins.drop_duplicates(
        subset="St.", keep="first"
    )
    previous_vector = Vector(0, 0, 0)
    previous_profile = df_calculations_purlins["profiel_naam"][0]
    wall_list = []
    for _, beam in df_calculations_purlins.iterrows():

        beam_line = Line(
            Point(float(beam["ki_x"]), 0, float(beam["ki_z"])),
            Point(float(beam["kj_x"]), 0, float(beam["kj_z"])),
        )
        beam_vector = beam_line.direction(normalize=True)
        angle = arccos(min(beam_vector.dot(previous_vector), 1.0))

        if (
            degrees(angle) > 5
        ):  # if the angle between two consecutive beams is greater than the tolerance (5 degrees)
            wall_list.append([beam["St."]])
        else:
            if beam["profiel_naam"] != previous_profile:
                raise UserError(
                    f'Could not create walls: at least one wall shares two or more different profiles: {beam["St."]-1}'
                )
            wall_list[-1].append(beam["St."])

        previous_vector = beam_vector
        previous_profile = beam["profiel_naam"]

    letters_list = [letter for letter, _ in zip(iter_all_strings(), wall_list)]

    return {letter: wall for wall, letter in zip(wall_list, letters_list)}


def find_row_with_max_uc_per_wall(
    walls_dict: Dict[str, List], results_purlins: DataFrame, UGT: bool
) -> Dict[str, Series]:
    """Find the row with has the maximum uc for all beams, and all calculations per beam, per wall.

    For a wall 'A': [1, 2], the structure of results_purlins is:
    Naam                            uc
    Staaf nr: 1, Kn. Pos.1          0.5
    Staaf nr: 1, Kn. Pos.2          0.6                 => max uc of the wall 'A' is 0.6
    Staaf nr: 2, Kn. Pos.3          0.3                 => return the full corresponding row
    Staaf nr: 2, Kn. Pos.2          0.4

    UGT == True: apply function for uc_maatgevend_UGT
    UGT == False: apply function for uc_maatgevend
    """
    results_purlins = results_purlins.reset_index()

    # First find the max u.c of beams for every calculations per beam
    if UGT:
        id_list = results_purlins.groupby("St.")["uc_maatgevend_UGT"].idxmax().to_list()

    else:
        id_list = results_purlins.groupby("St.")["uc_maatgevend"].idxmax().to_list()

    # This dataframe only keeps a unique row per beam, this is the row for which uc_maatgevend was the highest
    df_results_purlins_shortened = results_purlins.iloc[id_list, :]

    # Then find the max u.c of a wall for every beam of the wall
    dict_wall_max_uc = {}
    for wall_name, wall_beams in walls_dict.items():
        max_uc_per_beam = 0
        row = None
        for _, beam_row in df_results_purlins_shortened.iterrows():
            if beam_row["St."] in wall_beams:
                if beam_row["uc_maatgevend_UGT"] > max_uc_per_beam:
                    max_uc_per_beam = beam_row["uc_maatgevend_UGT"]
                    row = beam_row

        dict_wall_max_uc[wall_name] = row

    return dict_wall_max_uc


def make_data_dict_stamps_BGT_strut_removal(
    summary_df: DataFrame, df_calculations_preface_forces: DataFrame
) -> List[dict]:
    data_groups_stamps_BGT = []
    for strut_index, row_summary in summary_df.iterrows():
        if row_summary["max_uc"] > 1:
            status_stamps = DataStatus.ERROR
            status_msg_stamps = f"Voldoet niet! "
        else:
            status_stamps = DataStatus.SUCCESS
            status_msg_stamps = f"Voldoet !"
        type_Strut = determine_type_strut(
            df_calculations_preface_forces, strut_id=int(row_summary["St."])
        )
        item_name = (
            f'Staaf {row_summary["St."]}: {type_Strut}'
            + f' ({row_summary["Prof."].split(":")[-1]})'
        )

        sub_group = {
            "label": item_name,
            "value": row_summary["max_uc"],
            "explanation_label": f'Hoogest u.c. voor stempel/staaf {row_summary["max_uc_strut"]}',
            "status": status_stamps,
            "status_message": status_msg_stamps,
        }
        data_groups_stamps_BGT.append(sub_group)
    return data_groups_stamps_BGT


def make_data_dict_stamps_BGT_point_load(
    df_results_stamps_BGT: DataFrame, df_calculations_preface_forces: DataFrame
) -> List[dict]:
    data_groups_stamps_BGT = []
    for index_1, row_1 in df_results_stamps_BGT.iterrows():
        if (
            max(
                row_1["uc_NEd_BGT"],
                row_1["uc_MEd_BGT"],
                row_1["uc_VEd_BGT"],
                row_1["uc_MEd_NEd_BGT_1"],
                row_1["uc_MEd_NEd_BGT_2"],
                row_1["uc_MEd_MV,Rd_BGT_1"],
                row_1["uc_MEd_MV,Rd_BGT_2"],
                row_1["uc_NEd_Nb,Rd_BGT"],
                row_1["uc_NEd_kyy_My,Ed_BGT"],
                row_1["uc_NEd_kzy_My,Ed_BGT"],
            )
            > 1
        ):
            status_stamps = DataStatus.ERROR
            status_msg_stamps = f"Voldoet niet! "
        elif row_1["uc_χ"] > 1:
            status_stamps = DataStatus.WARNING
            status_msg_stamps = (
                f"Let op waarde in som voldoet niet, waarden moeten > 1! "
            )
        else:
            status_stamps = DataStatus.SUCCESS
            status_msg_stamps = f"Voldoet !"
        type_Strut = determine_type_strut(
            df_calculations_preface_forces, strut_id=int(row_1["St."])
        )
        item_name = (
            f'Staaf {row_1["St."]}: {type_Strut} '
            + f' ({row_1["Prof."].split(":")[-1]})'
        )
        sub_group = {
            "label": item_name,
            "value": row_1["uc_maatgevend"],
            "explanation_label": "maatgevende uc",
            "status": status_stamps,
            "status_message": status_msg_stamps,
        }
        data_groups_stamps_BGT.append(sub_group)
    return data_groups_stamps_BGT
