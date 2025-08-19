from typing import Dict, List
import pandas as pd
import numpy as np
from munch import Munch
from pandas import DataFrame

from app.XMLupload.calculations.calculation_purlins import get_nodes_dict_x_z
from app.XMLupload.constants import (
    columns_calculations_stamps,
    dict_sterkte_fu,
    soortgelijk_gewicht,
    stamp_failure,
    YOUNG_MODULUS_STEEL,
    γstempel_UGT,
    lijnlast,
    uitzet_coëff,
    γeg_UGT,
    γQ_UGT,
    γstempel_BGT,
    γeg_BGT,
    γQ_BGT,
    γtemp_UGT,
    γtemp_BGT,
    M0,
    uc_uitval,
    M1,
    imperfectie_f_a,
    imperfectie_f_a0,
    Cmy,
    χLT,
    columns_results_stamps_UGT,
    columns_results_stamps_BGT,
    point_load_calamity_value)


def get_df_calculations_stamps(
    technosoft_parsed_outputs: Dict[str, pd.DataFrame],
    params: Munch,
    point_load_calamity_bool: bool,
) -> DataFrame:
    """Fill the Dataframe of the calculations stamps based on Technosoft calculation_df_results and return it"""
    ## Select Normal forces per bar for props and struts (Selecteren Normaalkrachten per staaf voor stempels en schoren)
    df_calculations_stamps = pd.DataFrame(
        data=None, columns=columns_calculations_stamps
    )

    # Determine point load to use, depends on whether calamity is selected
    puntlast = point_load_calamity_bool * point_load_calamity_value

    df_barforces_UGT = technosoft_parsed_outputs["df_barforces_UGT"]
    df_barforces_BGT = technosoft_parsed_outputs["df_barforces_BGT"]
    df_bars = technosoft_parsed_outputs["df_bars"]
    df_bars_orig = technosoft_parsed_outputs["df_bars_original"]
    df_profiles = technosoft_parsed_outputs["df_profiles"]
    df_calculations_stamps["St."] = df_barforces_UGT["St."]
    df_nodes = technosoft_parsed_outputs["df_nodes"]

    dict_stamp_nodes = df_bars_orig.set_index("St.").to_dict()
    df_calculations_stamps["ki"] = df_calculations_stamps["St."].map(
        dict_stamp_nodes["ki"]
    )
    df_calculations_stamps["kj"] = df_calculations_stamps["St."].map(
        dict_stamp_nodes["kj"]
    )

    try:
        df_calculations_stamps["ki"] = df_calculations_stamps["ki"].astype(int)
        df_calculations_stamps["kj"] = df_calculations_stamps["kj"].astype(int)
    except ValueError:
        return None

    df_calculations_stamps = df_calculations_stamps.drop_duplicates(
        subset="St.", keep="first"
    )
    df_calculations_stamps.reset_index(drop=True, inplace=True)

    ####
    dict_node_x, dict_node_z = get_nodes_dict_x_z(df_nodes)
    df_calculations_stamps.insert(
        2, "ki_x", df_calculations_stamps["ki"].map(dict_node_x)
    )
    df_calculations_stamps.insert(
        3, "ki_z", df_calculations_stamps["ki"].map(dict_node_z)
    )
    df_calculations_stamps.insert(
        6, "kj_x", df_calculations_stamps["kj"].map(dict_node_x)
    )
    df_calculations_stamps.insert(
        7, "kj_z", df_calculations_stamps["kj"].map(dict_node_z)
    )
    ####

    dict_barforce_UGT = df_barforces_UGT.set_index("St.").to_dict()
    dict_barforce_BGT = df_barforces_BGT.set_index("St.").to_dict()
    df_calculations_stamps["NXi/NXj_UGT"] = df_calculations_stamps["St."].map(
        dict_barforce_UGT["NXi/NXj"]
    )
    df_calculations_stamps["NXi/NXj_BGT"] = df_calculations_stamps["St."].map(
        dict_barforce_BGT["NXi/NXj"]
    )

    split_profile_UGT = df_bars["Profiel"].str.split("[:/]", expand=True)
    df_bars.insert(4, "Prof_ID", split_profile_UGT[0])
    df_bars.insert(5, "Prof_bu", split_profile_UGT[1])
    try:
        df_bars.insert(6, "Prof_wa", split_profile_UGT[2])
    except KeyError:
        df_bars.insert(
            6,
            "Prof_wa",
            pd.DataFrame(np.array([None] * len(split_profile_UGT)), columns=[""]),
        )

    # Add strength_class per profile in DataFrame (Toevoegen strength_class per profiel in DataFrame)
    split_material = df_profiles["Materiaal"].str.split("[:S]", expand=True)
    df_profiles.insert(3, "Materiaal_ID", split_material[0])
    df_profiles.insert(4, "Materiaal_", split_material[2])
    df_profiles_to_dict = df_profiles.set_index("Prof.").to_dict()
    df_bars.insert(
        7, "Sterkteklasse", df_bars["Prof_ID"].map(df_profiles_to_dict["Materiaal_"])
    )
    dict_bars_stamps = df_bars.set_index("St.").to_dict()

    df_calculations_stamps["Sterkteklasse"] = df_bars["Sterkteklasse"]
    df_calculations_stamps["Prof."] = df_calculations_stamps["St."].map(
        dict_bars_stamps["Profiel"]
    )
    df_calculations_stamps["prof_id"] = df_calculations_stamps["St."].map(
        dict_bars_stamps["Prof_ID"]
    )
    df_calculations_stamps["bu"] = df_calculations_stamps["St."].map(
        dict_bars_stamps["Prof_bu"]
    )
    df_calculations_stamps["wa"] = df_calculations_stamps["St."].map(
        dict_bars_stamps["Prof_wa"]
    )
    df_calculations_stamps["wa"] = df_calculations_stamps["wa"].astype(float)
    df_calculations_stamps["lengte"] = df_calculations_stamps["St."].map(
        dict_bars_stamps["Lengte"]
    )
    df_calculations_stamps["lengte"] = df_calculations_stamps["lengte"].astype(float)
    df_calculations_stamps["fy"] = df_calculations_stamps["St."].map(
        dict_bars_stamps["Sterkteklasse"]
    )
    df_calculations_stamps["fy"] = df_calculations_stamps["fy"].astype(int)
    df_calculations_stamps["fu"] = df_calculations_stamps["fy"].map(dict_sterkte_fu)

    # separating props/braces from purlin profiles (scheiden stempels/schoren van gording profielen)
    # Remove from the dataframe, all rows whose bu (profiel) that don't start with B: HEB600 for example
    df_calculations_stamps = df_calculations_stamps[
        df_calculations_stamps["bu"].str[0].isin(["B"])
    ]
    # remove text 'B' in profile type for calculations (verwijderen teks 'B' in profieltype voor berekeningen)
    df_calculations_stamps["bu"] = df_calculations_stamps["bu"].apply(lambda x: x[1:])

    df_calculations_stamps["Wpl"] = (
        df_calculations_stamps["bu"].astype(float)
        - df_calculations_stamps["wa"].astype(float)
    ) ** 2 * df_calculations_stamps["wa"].astype(float)
    df_calculations_stamps["Wel"] = (
        np.pi
        * (
            df_calculations_stamps["bu"].astype(float) ** 4
            - (
                df_calculations_stamps["bu"].astype(float)
                - 2 * df_calculations_stamps["wa"].astype(float)
            )
            ** 4
        )
        / (32 * df_calculations_stamps["bu"].astype(float))
    )
    df_calculations_stamps["I"] = (
        np.pi
        * (
            df_calculations_stamps["bu"].astype(float) ** 4
            - (
                df_calculations_stamps["bu"].astype(float)
                - 2 * df_calculations_stamps["wa"].astype(float)
            )
            ** 4
        )
        / 64
    )
    df_calculations_stamps["A"] = (
        0.25 * np.pi * df_calculations_stamps["bu"].astype(float) ** 2
    ) - (
        0.25
        * np.pi
        * (
            df_calculations_stamps["bu"].astype(float)
            - 2 * df_calculations_stamps["wa"].astype(float)
        )
        ** 2
    )
    df_calculations_stamps["Av"] = df_calculations_stamps["A"] * 2 / np.pi
    df_calculations_stamps["G"] = (
        df_calculations_stamps["A"] * 10**-6 * soortgelijk_gewicht
    ) / 100
    df_calculations_stamps["d/t/e"] = (
        df_calculations_stamps["bu"].astype(float)
        / df_calculations_stamps["wa"].astype(float)
    ) / ((235 / df_calculations_stamps["fy"].astype(float)) ** 0.5) ** 2

    list_stamp_failure = fill_young_modulus_and_get_list_stamp_failure(
        df_calculations_stamps
    )

    fill_drsn_klasse(df_calculations_stamps)
    fill_UGT_compression_and_traction(df_calculations_stamps)

    df_calculations_stamps["NXi/NXj_BGT"] = df_calculations_stamps[
        "NXi/NXj_BGT"
    ].astype(float)
    dict_N_BGT_traction = {"NXi/NXj_BGT_trek": {}}
    dict_N_BGT_pressure = {"NXi/NXj_BGT_druk": {}}
    for index_1, row_1 in df_calculations_stamps.iterrows():
        if row_1["NXi/NXj_BGT"] > 1:
            dict_N_BGT_traction["NXi/NXj_BGT_trek"].update(
                {row_1["St."]: row_1["NXi/NXj_BGT"]}
            )
            dict_N_BGT_pressure["NXi/NXj_BGT_druk"].update({row_1["St."]: 0})
        if row_1["NXi/NXj_BGT"] <= 0:
            dict_N_BGT_pressure["NXi/NXj_BGT_druk"].update(
                {row_1["St."]: row_1["NXi/NXj_BGT"]}
            )
            dict_N_BGT_traction["NXi/NXj_BGT_trek"].update({row_1["St."]: 0})
    df_calculations_stamps["NXi/NXj_BGT_trek"] = df_calculations_stamps["St."].map(
        dict_N_BGT_traction["NXi/NXj_BGT_trek"]
    )
    df_calculations_stamps["NXi/NXj_BGT_druk"] = df_calculations_stamps["St."].map(
        dict_N_BGT_pressure["NXi/NXj_BGT_druk"]
    )
    df_calculations_stamps["NXi/NXj_BGT_trek"] = df_calculations_stamps[
        "NXi/NXj_BGT_trek"
    ].fillna(0)
    df_calculations_stamps["NXi/NXj_BGT_druk"] = df_calculations_stamps[
        "NXi/NXj_BGT_druk"
    ].fillna(0)
    df_calculations_stamps["NXi/NXj_BGT_druk"] = abs(
        df_calculations_stamps["NXi/NXj_BGT_druk"]
    )

    df_calculations_stamps["NXi/NXj_UGT_γ"] = (
        df_calculations_stamps["NXi/NXj_UGT"] * γstempel_UGT
    )
    df_calculations_stamps["Meg"] = (
        df_calculations_stamps["G"] * df_calculations_stamps["lengte"] ** 2
    ) / 8
    df_calculations_stamps["Mrep_lijn_UGT"] = (
        lijnlast * df_calculations_stamps["lengte"] ** 2
    ) / 8
    df_calculations_stamps["Mrep_punt_UGT"] = (
        puntlast * df_calculations_stamps["lengte"]
    ) / 4
    df_calculations_stamps["Mrep_lijn_BGT"] = 0  # TODO: to be checked
    df_calculations_stamps["Mrep_punt_BGT"] = (
        puntlast * df_calculations_stamps["lengte"]
    ) / 4

    df_calculations_stamps["vervorming"] = (
        (5 / 384)
        * (df_calculations_stamps["G"] * (df_calculations_stamps["lengte"] * 1000) ** 4)
        / (df_calculations_stamps["E"] * df_calculations_stamps["I"])
    )
    stamps_calc_table = params.calculation
    df_calculations_stamps["Excentrisch"] = stamps_calc_table.excentricity
    df_calculations_stamps["Excentrisch"] = df_calculations_stamps[
        "Excentrisch"
    ].astype(float)
    df_calculations_stamps["M2e orde_UGT"] = df_calculations_stamps[
        "NXi/NXj_UGT_druk"
    ] * (df_calculations_stamps["vervorming"] / 1000)
    df_calculations_stamps["M2e orde_BGT"] = df_calculations_stamps[
        "NXi/NXj_BGT_druk"
    ] * (df_calculations_stamps["vervorming"] / 1000)
    df_calculations_stamps["Mrep,excen_UGT"] = (
        df_calculations_stamps["Excentrisch"] / 1000
    ) * df_calculations_stamps["NXi/NXj_UGT_druk"]
    df_calculations_stamps["Mrep,excen_BGT"] = (
        df_calculations_stamps["Excentrisch"] / 1000
    ) * df_calculations_stamps["NXi/NXj_BGT_druk"]

    df_calculations_stamps["Vrep,eg"] = (
        df_calculations_stamps["G"] * df_calculations_stamps["lengte"] / 2
    )
    df_calculations_stamps["Vrep,lijn"] = df_calculations_stamps["lengte"] / 2
    df_calculations_stamps["Vrep,punt_UGT"] = puntlast / 2
    df_calculations_stamps["Vrep,punt_BGT"] = puntlast / 2
    df_calculations_stamps["Nrep_UGT"] = (
        stamps_calc_table.hoh * df_calculations_stamps["NXi/NXj_UGT_druk"]
    )
    df_calculations_stamps["Nrep_BGT"] = (
        stamps_calc_table.hoh * df_calculations_stamps["NXi/NXj_BGT_druk"]
    )
    df_calculations_stamps["NT,rep"] = (
        df_calculations_stamps["E"]
        * df_calculations_stamps["A"]
        * uitzet_coëff
        * params.calculation.temperature
        * (
            stamps_calc_table.k_value_sheetpile
            / (
                stamps_calc_table.k_value_sheetpile
                + (
                    (df_calculations_stamps["E"] * df_calculations_stamps["A"])
                    / (0.5 * df_calculations_stamps["lengte"] * 1000)
                )
            )
        )
        / 1000
    )
    list_max_lijn_punt_Med_UGT = []
    for row_1, row_2 in zip(
        df_calculations_stamps["Mrep_lijn_UGT"], df_calculations_stamps["Mrep_punt_UGT"]
    ):
        if row_1 > row_2:
            list_max_lijn_punt_Med_UGT.append(row_1)
        else:
            list_max_lijn_punt_Med_UGT.append(row_2)
    df_calculations_stamps["max_lijn_punt_Med_UGT"] = list_max_lijn_punt_Med_UGT

    list_max_lijn_punt_Med_BGT = []
    for row_1, row_2 in zip(
        df_calculations_stamps["Mrep_lijn_BGT"], df_calculations_stamps["Mrep_punt_BGT"]
    ):
        if row_1 > row_2:
            list_max_lijn_punt_Med_BGT.append(row_1)
        else:
            list_max_lijn_punt_Med_BGT.append(row_2)
    df_calculations_stamps["max_lijn_punt_Med_BGT"] = list_max_lijn_punt_Med_BGT
    df_calculations_stamps["MEd,midden_UGT"] = (
        df_calculations_stamps["M2e orde_UGT"] * γstempel_UGT
        + df_calculations_stamps["Meg"] * γeg_UGT
        + (
            df_calculations_stamps["max_lijn_punt_Med_UGT"]
            + df_calculations_stamps["Mrep,excen_UGT"]
        )
        * γQ_UGT
    )
    df_calculations_stamps["MEd,midden_BGT"] = (
        df_calculations_stamps["M2e orde_BGT"] * γstempel_BGT
        + df_calculations_stamps["Meg"] * γeg_BGT
        + (
            df_calculations_stamps["Mrep,excen_BGT"]
            + df_calculations_stamps["max_lijn_punt_Med_BGT"]
        )
        * γQ_BGT
    )
    list_max_lijn_punt_Ved_UGT = []
    for row_1, row_2 in zip(
        df_calculations_stamps["Vrep,lijn"], df_calculations_stamps["Vrep,punt_UGT"]
    ):
        if row_1 > row_2 * 2:
            list_max_lijn_punt_Ved_UGT.append(row_1)
        else:
            list_max_lijn_punt_Ved_UGT.append(row_2 * 2)
    df_calculations_stamps["max_lijn_punt_Ved_UGT"] = list_max_lijn_punt_Ved_UGT

    list_max_lijn_punt_Ved_BGT = []
    for row_1, row_2 in zip(
        df_calculations_stamps["Vrep,lijn"], df_calculations_stamps["Vrep,punt_BGT"]
    ):
        if row_1 > row_2 * 2:
            list_max_lijn_punt_Ved_BGT.append(row_1)
        else:
            list_max_lijn_punt_Ved_BGT.append(row_2 * 2)
    df_calculations_stamps["max_lijn_punt_Ved_BGT"] = list_max_lijn_punt_Ved_BGT

    df_calculations_stamps["VEd,kop_UGT"] = (
        df_calculations_stamps["Vrep,eg"] * γeg_UGT
        + df_calculations_stamps["max_lijn_punt_Ved_UGT"] * γQ_UGT
    )
    df_calculations_stamps["VEd,kop_BGT"] = (
        df_calculations_stamps["Vrep,eg"] * γeg_BGT
        + df_calculations_stamps["max_lijn_punt_Ved_BGT"] * γQ_BGT
    )
    df_calculations_stamps["VEd,midden_UGT"] = (
        df_calculations_stamps["Vrep,punt_UGT"] * γQ_UGT
    )  # currently useless
    df_calculations_stamps["VEd,midden_BGT"] = (
        df_calculations_stamps["Vrep,punt_BGT"] * γQ_BGT
    )  # currently useless
    df_calculations_stamps["NEd,druk_UGT"] = (
        df_calculations_stamps["Nrep_UGT"] * γstempel_UGT
        + df_calculations_stamps["NT,rep"] * γtemp_UGT
    )
    df_calculations_stamps["NEd,druk_BGT"] = (
        df_calculations_stamps["Nrep_BGT"] * γstempel_BGT
        + df_calculations_stamps["NT,rep"] * γtemp_BGT
    )

    # """"TOETSING AXIALE TREK/DRUK""""
    df_calculations_stamps["NRd"] = (
        df_calculations_stamps["A"] * df_calculations_stamps["fy"] / M0 / 1000
    )
    df_calculations_stamps["NEd_UGT"] = df_calculations_stamps["NEd,druk_UGT"]
    df_calculations_stamps["uc_NEd_UGT"] = round(
        (df_calculations_stamps["NEd_UGT"] / df_calculations_stamps["NRd"]), 2
    )
    df_calculations_stamps["NEd_BGT"] = df_calculations_stamps["NEd,druk_BGT"]
    df_calculations_stamps["uc_NEd_BGT"] = round(
        (df_calculations_stamps["NEd_BGT"] / df_calculations_stamps["NRd"]), 2
    )
    # """"TOETSING BUIGEND MOMENT""""
    list_Wy_y = []
    for row_1, row_2, row_3 in zip(
        df_calculations_stamps["drsn. kl."],
        df_calculations_stamps["Wel"],
        df_calculations_stamps["Wpl"],
    ):
        if row_1 == 1:
            list_Wy_y.append(row_3)
        if row_1 == 2:
            list_Wy_y.append(row_3)
        if row_1 == 3:
            list_Wy_y.append(row_2)
        if row_1 == 4:
            list_Wy_y.append(row_2)
    df_calculations_stamps["Wy-y"] = list_Wy_y
    df_calculations_stamps["MRd"] = (
        (df_calculations_stamps["Wy-y"] * df_calculations_stamps["fy"]) / M0 / 1000000
    )
    df_calculations_stamps["MEd_UGT"] = df_calculations_stamps["MEd,midden_UGT"]
    df_calculations_stamps["uc_MEd_UGT"] = round(
        (df_calculations_stamps["MEd_UGT"] / df_calculations_stamps["MRd"]), 2
    )
    df_calculations_stamps["MEd_BGT"] = df_calculations_stamps["MEd,midden_BGT"]
    list_stamps_MEd_BGT = []
    for index_1, row_1 in df_calculations_stamps.iterrows():
        if row_1["Prof."][-6:] == stamp_failure:
            list_stamps_MEd_BGT.append(0)
        else:
            list_stamps_MEd_BGT.append(row_1["MEd_BGT"])

    df_calculations_stamps["MEd_BGT"] = df_calculations_stamps["MEd_BGT"].replace(
        np.inf, 0
    )
    df_calculations_stamps["uc_MEd_BGT"] = round(
        (df_calculations_stamps["MEd_BGT"] / df_calculations_stamps["MRd"]), 2
    )

    # """"TOETSING DWARSKRACHT""""
    df_calculations_stamps["Vc,Rd"] = (
        (df_calculations_stamps["Av"] * (df_calculations_stamps["fy"] / np.sqrt(3)))
        / M0
        / 1000
    )
    df_calculations_stamps["VEd_UGT"] = df_calculations_stamps["VEd,kop_UGT"]
    df_calculations_stamps["uc_VEd_UGT"] = round(
        (df_calculations_stamps["VEd_UGT"] / df_calculations_stamps["Vc,Rd"]), 2
    )
    df_calculations_stamps["VEd_BGT"] = df_calculations_stamps["VEd,kop_BGT"]
    df_calculations_stamps["uc_VEd_BGT"] = round(
        (df_calculations_stamps["VEd_BGT"] / df_calculations_stamps["Vc,Rd"]), 2
    )
    # """"TOETSING BUIGING EN NORMAALKRACHT"""
    df_calculations_stamps["uc_MEd_NEd_UGT_1"] = round(
        (
            df_calculations_stamps["MEd_UGT"] / (1.04 * df_calculations_stamps["MRd"])
            + (df_calculations_stamps["NEd_UGT"] / df_calculations_stamps["NRd"]) ** 1.7
        ),
        2,
    )
    df_calculations_stamps["uc_MEd_NEd_UGT_1"] = df_calculations_stamps[
        "uc_MEd_NEd_UGT_1"
    ].replace(np.nan, uc_uitval, regex=True)
    df_calculations_stamps["uc_MEd_NEd_UGT_2"] = round(
        (df_calculations_stamps["MEd_UGT"] / df_calculations_stamps["MRd"]), 2
    )
    df_calculations_stamps["uc_MEd_NEd_UGT_2"] = df_calculations_stamps[
        "uc_MEd_NEd_UGT_2"
    ].replace(np.nan, uc_uitval, regex=True)
    df_calculations_stamps["uc_MEd_NEd_BGT_1"] = round(
        (
            df_calculations_stamps["MEd_BGT"] / (1.04 * df_calculations_stamps["MRd"])
            + (df_calculations_stamps["NEd_BGT"] / df_calculations_stamps["NRd"]) ** 1.7
        ),
        2,
    )
    df_calculations_stamps["uc_MEd_NEd_BGT_1"] = df_calculations_stamps[
        "uc_MEd_NEd_BGT_1"
    ].replace(np.nan, uc_uitval, regex=True)
    df_calculations_stamps["uc_MEd_NEd_BGT_2"] = round(
        (df_calculations_stamps["MEd_BGT"] / df_calculations_stamps["MRd"]), 2
    )
    df_calculations_stamps["uc_MEd_NEd_BGT_2"] = df_calculations_stamps[
        "uc_MEd_NEd_BGT_2"
    ].replace(np.nan, uc_uitval, regex=True)
    # """TOETSING BUITING< DWARSRACHT EN NORMAAKRACHT """
    list_reductie_UGT = []
    list_q_UGT = []
    for row_1, row_2, row_3 in zip(
        df_calculations_stamps["uc_VEd_UGT"],
        df_calculations_stamps["VEd_UGT"],
        df_calculations_stamps["Vc,Rd"],
    ):
        if row_1 <= 0.5:
            list_reductie_UGT.append("VEd/Vc,Rd < 0.5: geen reductie toepassen")
            list_q_UGT.append(1)
        else:
            list_reductie_UGT.append("reductie op combinatie buiging en normaalkracht")
            list_q_UGT.append(1.03 * np.sqrt((1 - (row_2 / row_3) ** 2)))
    df_calculations_stamps["reductie_UGT"] = list_reductie_UGT
    list_reductie_BGT = []
    list_q_BGT = []
    for row_1, row_2, row_3 in zip(
        df_calculations_stamps["uc_VEd_BGT"],
        df_calculations_stamps["VEd_BGT"],
        df_calculations_stamps["Vc,Rd"],
    ):
        if row_1 <= 0.5:
            list_reductie_BGT.append("VEd/Vc,Rd < 0.5: geen reductie toepassen")
            list_q_BGT.append(1)
        else:
            list_reductie_BGT.append("reductie op combinatie buiging en normaalkracht")
            list_q_BGT.append(1.03 * np.sqrt((1 - (row_2 / row_3) ** 2)))
    df_calculations_stamps["reductie_BGT"] = list_reductie_BGT
    df_calculations_stamps["q_UGT"] = list_q_UGT
    df_calculations_stamps["q_BGT"] = list_q_BGT
    df_calculations_stamps["NV,Rd_UGT"] = (
        df_calculations_stamps["q_UGT"] * df_calculations_stamps["NRd"]
    ) / M0
    df_calculations_stamps["NV,Rd_BGT"] = (
        df_calculations_stamps["q_BGT"] * df_calculations_stamps["NRd"]
    ) / M0
    df_calculations_stamps["MV,Rd_UGT"] = (
        df_calculations_stamps["q_UGT"] * df_calculations_stamps["MRd"]
    ) / M1
    df_calculations_stamps["MV,Rd_BGT"] = (
        df_calculations_stamps["q_BGT"] * df_calculations_stamps["MRd"]
    ) / M1
    df_calculations_stamps["uc_MEd_MV,Rd_UGT_1"] = round(
        (df_calculations_stamps["MEd_UGT"] / df_calculations_stamps["MV,Rd_UGT"]), 2
    )
    df_calculations_stamps["uc_MEd_MV,Rd_UGT_1"] = df_calculations_stamps[
        "uc_MEd_MV,Rd_UGT_1"
    ].replace(np.nan, uc_uitval, regex=True)
    df_calculations_stamps["uc_MEd_MV,Rd_UGT_2"] = round(
        (
            (
                df_calculations_stamps["MEd_UGT"]
                / (1.04 * df_calculations_stamps["MV,Rd_UGT"])
            )
            + (df_calculations_stamps["NEd_UGT"] / df_calculations_stamps["NV,Rd_UGT"])
            ** 1.7
        ),
        2,
    )
    df_calculations_stamps["uc_MEd_MV,Rd_UGT_2"] = df_calculations_stamps[
        "uc_MEd_MV,Rd_UGT_2"
    ].replace(np.nan, uc_uitval, regex=True)
    df_calculations_stamps["uc_MEd_MV,Rd_BGT_1"] = round(
        (df_calculations_stamps["MEd_BGT"] / df_calculations_stamps["MV,Rd_BGT"]), 2
    )
    df_calculations_stamps["uc_MEd_MV,Rd_BGT_1"] = df_calculations_stamps[
        "uc_MEd_MV,Rd_BGT_1"
    ].replace(np.nan, uc_uitval, regex=True)
    df_calculations_stamps["uc_MEd_MV,Rd_BGT_2"] = round(
        (
            (
                df_calculations_stamps["MEd_BGT"]
                / (1.04 * df_calculations_stamps["MV,Rd_BGT"])
            )
            + (df_calculations_stamps["NEd_BGT"] / df_calculations_stamps["NV,Rd_BGT"])
            ** 1.7
        ),
        2,
    )
    df_calculations_stamps["uc_MEd_MV,Rd_BGT_2"] = df_calculations_stamps[
        "uc_MEd_MV,Rd_BGT_2"
    ].replace(np.nan, uc_uitval, regex=True)
    # """TOETSING KNIKSTABLITEIT"""
    df_calculations_stamps["Ncr"] = (
        (np.pi**2 * df_calculations_stamps["E"] * df_calculations_stamps["I"])
        / (df_calculations_stamps["lengte"] * 1000) ** 2
        / 1000
    )
    df_calculations_stamps["λrel"] = np.sqrt(
        (df_calculations_stamps["A"] * df_calculations_stamps["fy"])
        / (df_calculations_stamps["Ncr"] * 1000)
    )  # relatieve slankheid
    list_knikkromme = []
    for i in df_calculations_stamps["fy"]:
        if i <= 420:
            list_knikkromme.append(imperfectie_f_a)
        else:
            list_knikkromme.append(imperfectie_f_a0)
    df_calculations_stamps["imperfectie_f"] = list_knikkromme
    df_calculations_stamps["Φ"] = 0.5 * (
        1
        + (
            df_calculations_stamps["imperfectie_f"]
            * (df_calculations_stamps["λrel"] - 0.2)
        )
        + df_calculations_stamps["λrel"] ** 2
    )
    df_calculations_stamps["χ"] = 1 / (
        df_calculations_stamps["Φ"]
        + np.sqrt(
            df_calculations_stamps["Φ"] ** 2 - df_calculations_stamps["λrel"] ** 2
        )
    )  # reductifactor 6.3.1 voor knikkromme
    df_calculations_stamps["uc_χ"] = round(df_calculations_stamps["χ"], 2)
    df_calculations_stamps["Nb,Rd"] = (
        (
            df_calculations_stamps["χ"]
            * df_calculations_stamps["A"]
            * df_calculations_stamps["fy"]
        )
        / M1
        / 1000
    )
    df_calculations_stamps["uc_NEd_Nb,Rd_UGT"] = round(
        (df_calculations_stamps["NEd_UGT"] / df_calculations_stamps["Nb,Rd"]), 2
    )
    df_calculations_stamps["uc_NEd_Nb,Rd_BGT"] = round(
        (df_calculations_stamps["NEd_BGT"] / df_calculations_stamps["Nb,Rd"]), 2
    )
    # """TOETSING OP BUIGING EN DRUK

    df_calculations_stamps["kyy_1en2_1_UGT"] = Cmy * (
        1
        + (df_calculations_stamps["λrel"] - 0.2)
        * (
            df_calculations_stamps["NEd_UGT"]
            / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"] / M1)
        )
    )
    df_calculations_stamps["kyy_1en2_2_UGT"] = Cmy * (
        1
        + 0.8
        * df_calculations_stamps["NEd_UGT"]
        / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"] / M1)
    )
    df_calculations_stamps["uc_kyy_1en2_UGT"] = (
        df_calculations_stamps["kyy_1en2_1_UGT"]
        / df_calculations_stamps["kyy_1en2_2_UGT"]
    )
    df_calculations_stamps["kyy_3en4_1_UGT"] = Cmy * (
        1
        + 0.6
        * (
            df_calculations_stamps["λrel"]
            * (
                df_calculations_stamps["NEd_UGT"]
                / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"])
                / M1
            )
        )
    )
    df_calculations_stamps["kyy_3en4_2_UGT"] = Cmy * (
        1
        + 0.6
        * df_calculations_stamps["NEd_UGT"]
        / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"] / M1)
    )
    df_calculations_stamps["uc_kyy_3en4_UGT"] = (
        df_calculations_stamps["kyy_3en4_1_UGT"]
        / df_calculations_stamps["kyy_3en4_2_UGT"]
    )
    list_kyy_klasse_UGT = []
    list_uc_kyy_klasse_UGT = []
    for index_1, row_1 in df_calculations_stamps.iterrows():
        if row_1["drsn. kl."] < 3:
            list_kyy_klasse_UGT.append(
                min(row_1["kyy_1en2_1_UGT"], row_1["kyy_1en2_2_UGT"])
            )
            list_uc_kyy_klasse_UGT.append(row_1["uc_kyy_1en2_UGT"])
        else:
            list_kyy_klasse_UGT.append(
                min(row_1["kyy_3en4_1_UGT"], row_1["kyy_3en4_2_UGT"])
            )
            list_uc_kyy_klasse_UGT.append(row_1["uc_kyy_3en4_UGT"])
    df_calculations_stamps["kyy_UGT"] = list_kyy_klasse_UGT
    df_calculations_stamps["uc_kyy_UGT"] = list_uc_kyy_klasse_UGT
    df_calculations_stamps["kyy_1en2_1_BGT"] = Cmy * (
        1
        + (df_calculations_stamps["λrel"] - 0.2)
        * (
            df_calculations_stamps["NEd_BGT"]
            / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"] / M1)
        )
    )
    df_calculations_stamps["kyy_1en2_2_BGT"] = Cmy * (
        1
        + 0.8
        * df_calculations_stamps["NEd_BGT"]
        / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"] / M1)
    )
    df_calculations_stamps["uc_kyy_1en2_BGT"] = (
        df_calculations_stamps["kyy_1en2_1_BGT"]
        / df_calculations_stamps["kyy_1en2_2_BGT"]
    )
    df_calculations_stamps["kyy_3en4_1_BGT"] = Cmy * (
        1
        + 0.6
        * (
            df_calculations_stamps["λrel"]
            * (
                df_calculations_stamps["NEd_BGT"]
                / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"])
                / M1
            )
        )
    )
    df_calculations_stamps["kyy_3en4_2_BGT"] = Cmy * (
        1
        + 0.6
        * df_calculations_stamps["NEd_BGT"]
        / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"] / M1)
    )
    df_calculations_stamps["uc_kyy_3en4_BGT"] = (
        df_calculations_stamps["kyy_3en4_1_BGT"]
        / df_calculations_stamps["kyy_3en4_2_BGT"]
    )
    list_kyy_klasse_BGT = []
    list_uc_kyy_klasse_BGT = []
    for index_1, row_1 in df_calculations_stamps.iterrows():
        if row_1["drsn. kl."] < 3:
            list_kyy_klasse_BGT.append(
                min(row_1["kyy_1en2_1_BGT"], row_1["kyy_1en2_2_BGT"])
            )
            list_uc_kyy_klasse_BGT.append(row_1["uc_kyy_1en2_BGT"])
        else:
            list_kyy_klasse_BGT.append(
                min(row_1["kyy_3en4_1_BGT"], row_1["kyy_3en4_2_BGT"])
            )
            list_uc_kyy_klasse_BGT.append(row_1["uc_kyy_3en4_BGT"])
    df_calculations_stamps["kyy_BGT"] = list_kyy_klasse_BGT
    df_calculations_stamps["uc_kyy_BGT"] = list_uc_kyy_klasse_BGT
    df_calculations_stamps["kzy_1en2_1_UGT"] = (
        0.6 * df_calculations_stamps["kyy_1en2_1_UGT"]
    )
    df_calculations_stamps["kzy_1en2_2_UGT"] = (
        0.6 * df_calculations_stamps["kyy_1en2_2_UGT"]
    )
    df_calculations_stamps["uc_kzy_1en2_UGT"] = (
        df_calculations_stamps["kzy_1en2_1_UGT"]
        / df_calculations_stamps["kzy_1en2_2_UGT"]
    )
    df_calculations_stamps["kzy_3en4_1_UGT"] = (
        0.8 * df_calculations_stamps["kyy_3en4_1_UGT"]
    )
    df_calculations_stamps["kzy_3en4_2_UGT"] = (
        0.8 * df_calculations_stamps["kyy_3en4_2_UGT"]
    )
    df_calculations_stamps["uc_kzy_3en4_UGT"] = (
        df_calculations_stamps["kzy_3en4_1_UGT"]
        / df_calculations_stamps["kzy_3en4_2_UGT"]
    )
    list_kzy_klasse_UGT = []
    list_uc_kzy_klasse_UGT = []
    for index_1, row_1 in df_calculations_stamps.iterrows():
        if row_1["drsn. kl."] < 3:
            list_kzy_klasse_UGT.append(
                min(row_1["kzy_1en2_1_UGT"], row_1["kzy_1en2_2_UGT"])
            )
            list_uc_kzy_klasse_UGT.append(row_1["uc_kzy_3en4_UGT"])
        else:
            list_kzy_klasse_UGT.append(
                min(row_1["kzy_3en4_1_UGT"], row_1["kzy_3en4_2_UGT"])
            )
            list_uc_kzy_klasse_UGT.append(row_1["uc_kzy_3en4_UGT"])
    df_calculations_stamps["kzy_UGT"] = list_kzy_klasse_UGT
    df_calculations_stamps["uc_kzy_UGT"] = list_uc_kzy_klasse_UGT
    df_calculations_stamps["kzy_1en2_1_BGT"] = (
        0.6 * df_calculations_stamps["kyy_1en2_1_BGT"]
    )
    df_calculations_stamps["kzy_1en2_2_BGT"] = (
        0.6 * df_calculations_stamps["kyy_1en2_2_BGT"]
    )
    df_calculations_stamps["uc_kzy_1en2_BGT"] = (
        df_calculations_stamps["kzy_1en2_1_BGT"]
        / df_calculations_stamps["kzy_1en2_2_BGT"]
    )
    df_calculations_stamps["kzy_3en4_1_BGT"] = (
        0.8 * df_calculations_stamps["kyy_3en4_1_BGT"]
    )
    df_calculations_stamps["kzy_3en4_2_BGT"] = (
        0.8 * df_calculations_stamps["kyy_3en4_2_BGT"]
    )
    df_calculations_stamps["uc_kzy_3en4_BGT"] = (
        df_calculations_stamps["kzy_3en4_1_BGT"]
        / df_calculations_stamps["kzy_3en4_2_BGT"]
    )
    list_kzy_klasse_BGT = []
    list_uc_kzy_klasse_BGT = []
    for index_1, row_1 in df_calculations_stamps.iterrows():
        if row_1["drsn. kl."] < 3:
            list_kzy_klasse_BGT.append(
                min(row_1["kzy_1en2_1_BGT"], row_1["kzy_1en2_2_BGT"])
            )
            list_uc_kzy_klasse_BGT.append(row_1["uc_kzy_1en2_BGT"])
        else:
            list_kzy_klasse_BGT.append(
                min(row_1["kzy_3en4_1_BGT"], row_1["kzy_3en4_2_BGT"])
            )
            list_uc_kzy_klasse_BGT.append(row_1["uc_kzy_3en4_BGT"])
    df_calculations_stamps["kzy_BGT"] = list_kzy_klasse_BGT
    df_calculations_stamps["uc_kzy_BGT"] = list_uc_kzy_klasse_BGT
    df_calculations_stamps["uc_NEd_kyy_My,Ed_UGT"] = round(
        (
            (
                df_calculations_stamps["NEd,druk_UGT"]
                / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"])
            )
            + (
                df_calculations_stamps["kyy_UGT"]
                * (
                    df_calculations_stamps["MEd,midden_UGT"]
                    / (χLT * df_calculations_stamps["MRd"])
                )
            )
        ),
        2,
    )
    df_calculations_stamps["uc_NEd_kzy_My,Ed_UGT"] = round(
        (
            (
                df_calculations_stamps["NEd,druk_UGT"]
                / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"])
            )
            + (
                df_calculations_stamps["kzy_UGT"]
                * (
                    df_calculations_stamps["MEd,midden_UGT"]
                    / (χLT * df_calculations_stamps["MRd"])
                )
            )
        ),
        2,
    )
    df_calculations_stamps["uc_NEd_kyy_My,Ed_BGT"] = round(
        (
            (
                df_calculations_stamps["NEd,druk_BGT"]
                / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"])
            )
            + (
                df_calculations_stamps["kyy_BGT"]
                * (
                    df_calculations_stamps["MEd,midden_BGT"]
                    / (χLT * df_calculations_stamps["MRd"])
                )
            )
        ),
        2,
    )
    df_calculations_stamps["uc_NEd_kzy_My,Ed_BGT"] = round(
        (
            (
                df_calculations_stamps["NEd,druk_BGT"]
                / (df_calculations_stamps["χ"] * df_calculations_stamps["NRd"])
            )
            + (
                df_calculations_stamps["kzy_BGT"]
                * (
                    df_calculations_stamps["MEd,midden_BGT"]
                    / (χLT * df_calculations_stamps["MRd"])
                )
            )
        ),
        2,
    )
    df_calculations_stamps["Naam"] = (
        "stempel / schoor staaf: " + df_calculations_stamps["St."]
    )
    df_calculations_stamps["aan/uit"] = list_stamp_failure
    df_calculations_stamps["aan/uit"] = (
        "Staaf: "
        + df_calculations_stamps["St."]
        + " is: "
        + df_calculations_stamps["aan/uit"]
    )
    return df_calculations_stamps


def build_df_results_stamps_UGT(df_calculations_stamps: DataFrame) -> DataFrame:
    """Shorter summary of df_calculations_stamps with important columns"""
    df_results_stamps_UGT = pd.DataFrame(data=None, columns=columns_results_stamps_UGT)
    for column_name in columns_results_stamps_UGT:
        if column_name in columns_calculations_stamps:
            df_results_stamps_UGT[column_name] = df_calculations_stamps[column_name]

    df_results_stamps_UGT = df_results_stamps_UGT.where(
        pd.notnull(df_calculations_stamps), 0
    )
    fill_max_uc_UGT(df_results_stamps_UGT)

    list_results_uc_UGT = []
    for index_1, row_1 in df_results_stamps_UGT.iterrows():
        if row_1["uc_maatgevend"] <= 1:
            list_results_uc_UGT.append("Voldoet")
        else:
            list_results_uc_UGT.append("Voldoet niet")
    df_results_stamps_UGT["result"] = list_results_uc_UGT

    return df_results_stamps_UGT


def build_df_results_stamps_BGT(df_calculations_stamps: DataFrame) -> DataFrame:
    df_results_stamps_BGT = pd.DataFrame(data=None, columns=columns_results_stamps_BGT)
    for column_name in columns_results_stamps_BGT:
        if column_name in columns_calculations_stamps:
            df_results_stamps_BGT[column_name] = df_calculations_stamps[column_name]

    df_results_stamps_BGT = df_results_stamps_BGT.where(
        pd.notnull(df_calculations_stamps), 0
    )
    list_max_uc_stamps_BGT = []
    for index_1, row_1 in df_results_stamps_BGT.iterrows():
        if row_1["Prof."][-6:] != stamp_failure:
            list_max_uc_stamps_BGT.append(
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
            )

        else:
            list_max_uc_stamps_BGT.append(0)

    df_results_stamps_BGT["uc_maatgevend"] = list_max_uc_stamps_BGT

    list_name_max_uc_stamps_BGT = []
    for index_1, row_1 in df_results_stamps_BGT.iterrows():
        if row_1["uc_maatgevend"] == row_1["uc_NEd_BGT"]:
            list_name_max_uc_stamps_BGT.append("Toetsing axiale druk")
        if row_1["uc_maatgevend"] == row_1["uc_MEd_BGT"]:
            list_name_max_uc_stamps_BGT.append("Toetsing buigend moment")
        if row_1["uc_maatgevend"] == row_1["uc_VEd_BGT"]:
            list_name_max_uc_stamps_BGT.append("Toetsing dwarskracht")
        if row_1["uc_maatgevend"] == row_1["uc_MEd_NEd_BGT_1"]:
            list_name_max_uc_stamps_BGT.append("Toetsing buiging en normaakracht (1)")
        if row_1["uc_maatgevend"] == row_1["uc_MEd_NEd_BGT_2"]:
            list_name_max_uc_stamps_BGT.append("Toetsing buiging en normaakracht (2)")
        if row_1["uc_maatgevend"] == row_1["uc_MEd_MV,Rd_BGT_1"]:
            list_name_max_uc_stamps_BGT.append(
                "Toetsing buiging, dwarskracht en normaalkracht (1)"
            )
        if row_1["uc_maatgevend"] == row_1["uc_MEd_MV,Rd_BGT_2"]:
            list_name_max_uc_stamps_BGT.append(
                "Toetsing buiging, dwarskracht en normaalkracht (2)"
            )
        if row_1["uc_maatgevend"] == row_1["uc_NEd_Nb,Rd_BGT"]:
            list_name_max_uc_stamps_BGT.append("Toetsing knikstabilteit")
        if row_1["uc_maatgevend"] == row_1["uc_NEd_kyy_My,Ed_BGT"]:
            list_name_max_uc_stamps_BGT.append("Toetsing buiging en druk (kyy)")
        if row_1["uc_maatgevend"] == row_1["uc_NEd_kzy_My,Ed_BGT"]:
            list_name_max_uc_stamps_BGT.append("Toetsing buiging en druk (kzy)")
    list_results_uc_BGT = []
    for index_1, row_1 in df_results_stamps_BGT.iterrows():
        if row_1["uc_maatgevend"] <= 1:
            list_results_uc_BGT.append("Voldoet")
        else:
            list_results_uc_BGT.append("Voldoet niet")
    df_results_stamps_BGT["result"] = list_results_uc_BGT

    return df_results_stamps_BGT


def fill_max_uc_UGT(df_results_stamps_UGT: DataFrame) -> DataFrame:
    list_max_uc_stamps_UGT = []
    for index_1, row_1 in df_results_stamps_UGT.iterrows():
        list_max_uc_stamps_UGT.append(
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
        )
    df_results_stamps_UGT["uc_maatgevend"] = list_max_uc_stamps_UGT
    return df_results_stamps_UGT["uc_maatgevend"]


def get_all_uc_UGT(df_results_stamps_UGT: DataFrame):
    """Return a dictionnary with all the UGT unity checks (of every bar?)
    TO BE COMPLETED IF NEEDED LATER"""
    return {
        "uc_NEd_UGT": df_results_stamps_UGT["uc_NEd_UGT"],
    }


def fill_drsn_klasse(df_calculations_stamps: DataFrame):
    """Fills the drsn klasse into the calculations_stamps DataFrame"""
    drsn_klasse_buisprof = []
    for i in df_calculations_stamps["d/t/e"]:
        if i < 50:
            drsn_klasse_buisprof.append(1)
        elif i > 50 and i < 70:
            drsn_klasse_buisprof.append(2)
        elif i > 70:
            drsn_klasse_buisprof.append(3)
    df_calculations_stamps["drsn. kl."] = drsn_klasse_buisprof
    return None


def fill_young_modulus_and_get_list_stamp_failure(
    df_calculations_stamps: DataFrame,
) -> List:
    list_E_modules = []
    list_stamp_failure = []
    for i in df_calculations_stamps["bu"]:
        if i == stamp_failure[1:4]:
            list_E_modules.append(0)
            list_stamp_failure.append("Uitgevallen")
        else:
            list_E_modules.append(YOUNG_MODULUS_STEEL)
            list_stamp_failure.append("Actief")

    df_calculations_stamps["E"] = list_E_modules
    return list_stamp_failure


def fill_UGT_compression_and_traction(df_calculations_stamps: DataFrame):
    df_calculations_stamps["NXi/NXj_UGT"] = df_calculations_stamps[
        "NXi/NXj_UGT"
    ].astype(float)
    N_UGT_traction, N_UGT_pressure = [], []
    for i in df_calculations_stamps["NXi/NXj_UGT"]:
        if i > 1:
            N_UGT_traction.append(i)
            N_UGT_pressure.append(0)
        if i <= 0:
            N_UGT_traction.append(0)
            N_UGT_pressure.append(i)
    df_calculations_stamps["NXi/NXj_UGT_trek"] = N_UGT_traction
    df_calculations_stamps["NXi/NXj_UGT_druk"] = N_UGT_pressure
    df_calculations_stamps["NXi/NXj_UGT_druk"] = abs(
        df_calculations_stamps["NXi/NXj_UGT_druk"]
    )
    return None


def show_df(df_calculations_stamps):
    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None
    ):  # more options can be specified also
        print(df_calculations_stamps)
