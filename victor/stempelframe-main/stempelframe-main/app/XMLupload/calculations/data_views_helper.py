from typing import List, Dict, Optional

from munch import Munch
from pandas import DataFrame, Series

from app.XMLupload.calculations.calculate import (
    get_walls,
    find_row_with_max_uc_per_wall)
from app.XMLupload.helper_functions import determine_type_strut
from viktor.views import DataItem, DataStatus, DataResult, DataGroup


def get_data_result_struts(
    params: Munch, BGT_results: Dict[str, List[dict]], df_results: Dict[str, DataFrame]
) -> DataGroup:
    """UGT calculations and DataGroup is common for both analysis `point_load` and 'strut_removal'.
    Only the BGT DataGroup is discriminated"""

    data_items = []

    # Get UGT
    if params.calculation.UGT:
        data_item_UGT = DataItem(
            label="Toetsresultaten UGT",
            value=f'max. u.c.{round(max(df_results["stamps_UGT"]["uc_maatgevend"]), 2)}',
            subgroup=make_data_group_stamps_UGT(
                df_results["stamps_UGT"], df_results["calculations_preface_forces"]
            ),
        )
        data_items.append(data_item_UGT)

    # Get BGT
    if BGT_results["BGT"]:
        data_item_point_load_BGT = DataItem(
            "Toetsresultaten BGT",
            f"max. u.c.{round(max(result['value'] for result in BGT_results['BGT']), 2)}",
            subgroup=DataGroup(*[DataItem(**args) for args in BGT_results["BGT"]]),
        )
        data_items.append(data_item_point_load_BGT)

    # Get BGT with point load
    if BGT_results["point_load"]:
        data_item_point_load_BGT = DataItem(
            "Toetsresultaten BGT (Calamiteit puntlast)",
            f"max. u.c.{round(max(result['value'] for result in BGT_results['point_load']), 2)}",
            subgroup=DataGroup(
                *[DataItem(**args) for args in BGT_results["point_load"]]
            ),
        )
        data_items.append(data_item_point_load_BGT)

    # Get BGT with strut removal
    if BGT_results["strut_removal"]:
        data_item_strut_removal_BGT = DataItem(
            "Toetsresultaten BGT (Calamiteit uitval)",
            f"max. u.c.",
            subgroup=DataGroup(
                *[DataItem(**args) for args in BGT_results["strut_removal"]]
            ),
        )
        data_items.append(data_item_strut_removal_BGT)

    # Return UGT calculation and all BGT calculations
    return DataGroup(*data_items)


def get_data_group_walls(calculation_results: Dict[str, DataFrame]) -> DataGroup:
    walls_dict = get_walls(calculation_results["calculations_purlins"])
    data_item_list_UGT, data_item_list_BGT = [], []
    for wall_name, wall_uc_row in find_row_with_max_uc_per_wall(
        walls_dict, calculation_results["results_purlins"], UGT=True
    ).items():
        if wall_uc_row["uc_maatgevend_UGT"] <= 1:
            status = DataStatus.SUCCESS
        else:
            status = DataStatus.ERROR

        explanation_label_UGT = make_explanation_label_wall_data_item_UGT(
            wall_name, wall_uc_row, walls_dict
        )

        data_item_list_UGT.append(
            DataItem(
                wall_name,
                round(wall_uc_row["uc_maatgevend_UGT"], 2),
                explanation_label=explanation_label_UGT,
                status=status,
                status_message="",
            )
        )

    for wall_name, wall_list in walls_dict.items():
        explanation_label_BGT = make_explanation_label_wall_data_item_BGT(
            wall_list, calculations_purlins=calculation_results["calculations_purlins"]
        )
        data_item_list_BGT.append(
            DataItem(
                wall_name,
                None,
                explanation_label=explanation_label_BGT,
                status_message="",
            )
        )

    data = DataGroup(
        DataItem("Wall UGT", value=None, subgroup=DataGroup(*data_item_list_UGT)),
        DataItem("Wall BGT", value=None, subgroup=DataGroup(*data_item_list_BGT)),
    )

    return data


def make_explanation_label_wall_data_item_BGT(
    wall_list: List, calculations_purlins: DataFrame
) -> str:
    """Make a custom explanation label for the BGT DataItems of the wallView, it should look like:
    q1={q_value}kN/m | Staaf {id_start}-{id-end} | L={L_value}m

    Special case is handled for walls with a unique beam.

    :param wall_list: list containing the strut_id of the current wall
    :param calculations_purlins: dataframe of the calculation of the beams, required to get the L_BGT_value
    """
    calculations_purlins = calculations_purlins.drop_duplicates(subset=["St."])
    list_BGT_length_wall = [
        (row["St."], row["L_BGT_wall"], row["BGT_stempelkracht"])
        for _, row in calculations_purlins.iterrows()
        if row["St."] in wall_list
    ]
    explanation_label = ""
    _, _, previous_load = list_BGT_length_wall[0]
    last_beam_id_of_group = wall_list[0]
    for first, second in zip(list_BGT_length_wall, list_BGT_length_wall[1:]):
        first_beam_id, first_beam_l_value, first_beam_load = first
        second_beam_id, second_beam_l_value, second_beam_load = second

        if first_beam_load != second_beam_load:
            explanation_label = (
                explanation_label
                + f"q1={first_beam_load}kN/m | Staaf {last_beam_id_of_group} - {first_beam_id} | L= {round(first_beam_l_value, 2)} m"
                + f"    \n  "
            )
            last_beam_id_of_group = second_beam_id

        if second_beam_id == list_BGT_length_wall[-1][0]:
            explanation_label = (
                explanation_label
                + f"q1={second_beam_load}kN/m | Staaf {last_beam_id_of_group} - {second_beam_id}: L= {round(second_beam_l_value, 2)} m"
                + f"    \n  "
            )
            last_beam_id_of_group = second_beam_id

    if (
        len(set(list_BGT_length_wall)) == 1
    ):  # all the beams of the wall have the same BGT applied linear load
        beam_id, beam_l_value, beam_load = list_BGT_length_wall[0]
        explanation_label = (
            explanation_label
            + f"q1={beam_load}kN/m | Staaf {beam_id} | L= {round(beam_l_value, 2)} m"
            + f"    \n  "
        )

    return explanation_label


def make_explanation_label_wall_data_item_UGT(
    wall_name: str, wall_row: Series, walls_dict
) -> str:
    """Return the explanation label for the BGT datagroup of the Wall Dataview. It should contain in this order:
    the beam number, their common profile and the forces/moment N/D/M responsible for the highest uc for the wall."""
    wall = walls_dict[wall_name]
    explanation_label = f'Staaf nr. {wall[0]} - {wall[-1]} | {wall_row["Naam"]} | {wall_row["profiel_naam"]} | N={wall_row["N_druk"]} | D={wall_row["DZi/DZj"]} | M={wall_row["MYi/MYj"]} '
    return explanation_label


def make_data_group_stamps_UGT(
    df_results_stamps_UGT: DataFrame, df_calculations_preface_forces: DataFrame
) -> DataGroup:
    data_groups_stamps_UGT = []
    for index_1, row_1 in df_results_stamps_UGT.iterrows():
        if (
            max(
                row_1["uc_NEd_UGT"],
                row_1["uc_MEd_UGT"],
                row_1["uc_VEd_UGT"],
                row_1["uc_MEd_NEd_UGT_1"],
                row_1["uc_MEd_NEd_UGT_2"],
                row_1["uc_MEd_MV,Rd_UGT_1"],
                row_1["uc_MEd_MV,Rd_UGT_2"],
                row_1["uc_NEd_Nb,Rd_UGT"],
                row_1["uc_NEd_kyy_My,Ed_UGT"],
                row_1["uc_NEd_kzy_My,Ed_UGT"],
            )
            > 1
        ):
            status_stamps = DataStatus.ERROR
            status_msg_stamps = f"Voldoet niet! "
        elif row_1["uc_χ"] > 1:
            status_stamps = DataStatus.WARNING
            status_msg_stamps = (
                f"Let op waarde in som voldoet niet, waarden moeten > 1!"
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

        sub_group = DataItem(
            label=item_name,
            value=row_1["uc_maatgevend"],
            explanation_label="maatgevende uc",
            status=status_stamps,
            status_message=status_msg_stamps,
        )
        data_groups_stamps_UGT.append(sub_group)
    return DataGroup(*data_groups_stamps_UGT)


def make_data_group_stamps_BGT_point_load(
    df_results_stamps_BGT: DataFrame, df_calculations_preface_forces: DataFrame
) -> List[DataItem]:
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
        sub_group = DataItem(
            item_name,
            row_1["uc_maatgevend"],
            explanation_label="maatgevende uc",
            status=status_stamps,
            status_message=status_msg_stamps,
        )
        data_groups_stamps_BGT.append(sub_group)
    return data_groups_stamps_BGT


def make_data_group_stamps_BGT_strut_removal(
    summary_df: DataFrame, df_calculations_preface_forces: DataFrame
) -> List[DataItem]:
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

        sub_group = DataItem(
            item_name,
            row_summary["max_uc"],
            explanation_label=f'Hoogest u.c. voor stempel/staaf {row_summary["max_uc_strut"]}',
            status=status_stamps,
            status_message=status_msg_stamps,
        )
        data_groups_stamps_BGT.append(sub_group)
    return data_groups_stamps_BGT
