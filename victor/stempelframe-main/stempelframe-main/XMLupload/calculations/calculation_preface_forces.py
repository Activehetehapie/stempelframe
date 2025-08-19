from munch import Munch
from numpy import nan, where, degrees, arccos, sqrt, pi, sin, arcsin
from pandas import DataFrame, option_context

from app.XMLupload.calculations.calculation_purlins import (
    get_nodes_dict_x_z,
    add_profile_parameters_to_df)
from app.XMLupload.constants import (
    columns_calculations_preface_forces,
    γstempel_UGT,
    γstempel_BGT,
    γm_gording_UGT,
    γm_gording_BGT,
    YOUNG_MODULUS_STEEL,
    columns_results_preface_forces)


def get_df_calculations_preface_forces(
    df_calculations_purlins: DataFrame,
    df_calculations_stamps: DataFrame,
    df_nodes: DataFrame,
    params: Munch,
) -> DataFrame:

    df_calculations_preface_forces = DataFrame(
        data=None, columns=columns_calculations_preface_forces
    )
    df_calculations_preface_forces["g_fy"] = df_calculations_purlins["Sterkteklasse"]
    df_calculations_preface_forces["Kn. Pos."] = df_calculations_purlins["Kn. Pos."]

    df_angle_struts = get_df_angle_struts(
        df_calculations_purlins, df_calculations_stamps, df_nodes
    )
    for column_name in df_angle_struts.columns:
        if column_name in columns_calculations_preface_forces:
            df_calculations_preface_forces[column_name] = df_angle_struts[column_name]
    df_calculations_preface_forces["Kn. Pos."] = df_calculations_preface_forces[
        "Kn. Pos."
    ].replace(nan, "REMOVE")

    # verwijderen alle gordingen met waarden tussen de knopen

    list_keep_values = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if "REMOVE" not in str(row_1["Kn. Pos."]):
            list_keep_values.append(row_1["Kn. Pos."])
    df_calculations_preface_forces = df_calculations_preface_forces[
        df_calculations_preface_forces["Kn. Pos."].isin(list_keep_values)
    ]

    dict_stamps = df_calculations_stamps.set_index("St.").to_dict()
    df_calculations_preface_forces["s_fy"] = df_calculations_preface_forces[
        "s_aansl_St."
    ].map(dict_stamps["fy"])
    df_calculations_preface_forces["s_bu"] = df_calculations_preface_forces[
        "s_aansl_St."
    ].map(dict_stamps["bu"])
    df_calculations_preface_forces["s_wa"] = df_calculations_preface_forces[
        "s_aansl_St."
    ].map(dict_stamps["wa"])
    dict_purlins = df_calculations_purlins.set_index("St.").to_dict()
    df_calculations_preface_forces["g_n"] = df_calculations_preface_forces["g_St."].map(
        dict_purlins["n_profiles"]
    )
    df_calculations_preface_forces.insert(
        2,
        "g_sterkte",
        df_calculations_preface_forces["g_St."].map(dict_purlins["Sterkteklasse"]),
    )
    df_calculations_preface_forces.insert(
        3,
        "g_profiel",
        df_calculations_preface_forces["g_St."].map(dict_purlins["profiel_naam"]),
    )

    df_calculations_preface_forces.insert(
        30,
        "s_kracht UGT",
        df_calculations_preface_forces["s_aansl_St."].map(dict_stamps["NXi/NXj_UGT"]),
    )
    df_calculations_preface_forces.insert(
        31, "NXi/NXj UGT", df_calculations_purlins["NXi/NXj"]
    )
    df_calculations_preface_forces.insert(
        32, "MYi/MYj UGT", df_calculations_purlins["MYi/MYj"]
    )
    df_calculations_preface_forces.insert(33, "Naam", "Staaf: ")
    df_calculations_preface_forces["Naam"] = (
        df_calculations_preface_forces["Naam"]
        + df_calculations_preface_forces["g_St."].astype("str")
        + "; Knoop/punt: "
        + df_calculations_preface_forces["Kn. Pos."].astype(str)
    )
    add_profile_parameters_to_df(df_calculations_preface_forces, "g_profiel")

    df_calculations_preface_forces["s_NEd_druk_UGT"] = df_calculations_preface_forces[
        "s_aansl_St."
    ].map(dict_stamps["NXi/NXj_UGT"])
    df_calculations_preface_forces["s_NEd_druk_BGT"] = df_calculations_preface_forces[
        "s_aansl_St."
    ].map(dict_stamps["NXi/NXj_BGT"])
    df_calculations_preface_forces["g_NEd_trek_UGT"] = df_calculations_preface_forces[
        "g_St."
    ].map(dict_purlins["N_trek"])
    df_calculations_preface_forces["g_NEd_druk_UGT"] = df_calculations_preface_forces[
        "g_St."
    ].map(dict_purlins["N_druk"])
    df_calculations_preface_forces["g_MYi/MYj_UGT"] = df_calculations_preface_forces[
        "g_St."
    ].map(dict_purlins["MYi/MYj"])
    df_calculations_preface_forces["g_NEd_BGT"] = df_calculations_preface_forces[
        "g_St."
    ].map(dict_purlins["N_BGT"])
    df_calculations_preface_forces["g_NEd_BGT"] = df_calculations_preface_forces[
        "g_NEd_BGT"
    ].astype(float)
    df_calculations_preface_forces["g_MYi/MYj_BGT"] = df_calculations_preface_forces[
        "g_St."
    ].map(dict_purlins["M_BGT"])
    df_calculations_preface_forces["g_MYi/MYj_BGT"] = abs(
        df_calculations_preface_forces["g_MYi/MYj_BGT"].astype(float)
    )

    list_N_trek_BGT, list_N_druk_BGT = [], []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if row_1["g_NEd_BGT"] <= 0:
            list_N_druk_BGT.append(row_1["g_NEd_BGT"])
            list_N_trek_BGT.append(0)
        else:
            list_N_druk_BGT.append(0)
            list_N_trek_BGT.append(row_1["g_NEd_BGT"])

    df_calculations_preface_forces["g_NEd_druk_BGT"] = list_N_druk_BGT
    df_calculations_preface_forces["g_NEd_druk_BGT"] = abs(
        df_calculations_preface_forces["g_NEd_druk_BGT"]
    )
    df_calculations_preface_forces["g_NEd_trek_BGT"] = list_N_trek_BGT

    df_calculations_preface_forces["g_ε"] = sqrt(
        235 / df_calculations_preface_forces["g_sterkte"]
    )
    df_calculations_preface_forces["s_ε"] = sqrt(
        235 / df_calculations_preface_forces["s_fy"]
    )
    df_calculations_preface_forces["g_λ1"] = pi * sqrt(
        YOUNG_MODULUS_STEEL / df_calculations_preface_forces["g_sterkte"]
    )
    df_calculations_preface_forces["s_λ1"] = pi * sqrt(
        YOUNG_MODULUS_STEEL / df_calculations_preface_forces["s_fy"]
    )
    df_calculations_preface_forces["g_hw"] = (
        df_calculations_preface_forces["h"]
        - df_calculations_preface_forces["tf"]
        - df_calculations_preface_forces["tf"]
    )
    df_calculations_preface_forces["s_bu"] = df_calculations_preface_forces[
        "s_bu"
    ].astype(float)
    df_calculations_preface_forces["s_wa"] = df_calculations_preface_forces[
        "s_wa"
    ].astype(float)
    df_calculations_preface_forces["s_d_inw"] = (
        df_calculations_preface_forces["s_bu"]
        - df_calculations_preface_forces["s_wa"]
        - df_calculations_preface_forces["s_wa"]
    )
    df_calculations_preface_forces["s_A"] = (
        0.25 * pi * df_calculations_preface_forces["s_bu"] ** 2
    ) - (0.25 * pi * df_calculations_preface_forces["s_d_inw"] ** 2)
    df_calculations_preface_forces["s_I"] = (
        pi
        * (
            df_calculations_preface_forces["s_bu"] ** 4
            - df_calculations_preface_forces["s_d_inw"] ** 4
        )
    ) / 64
    df_calculations_preface_forces["s_Wel"] = (
        pi
        * (
            df_calculations_preface_forces["s_bu"] ** 4
            - df_calculations_preface_forces["s_d_inw"] ** 4
        )
        / (32 * df_calculations_preface_forces["s_bu"])
    )
    df_calculations_preface_forces["s_Wpl"] = (
        df_calculations_preface_forces["s_bu"] - df_calculations_preface_forces["s_wa"]
    ) ** 2 * df_calculations_preface_forces["s_wa"]
    df_calculations_preface_forces["s_NEd_druk_UGT"] = (
        df_calculations_preface_forces["s_NEd_druk_UGT"].astype(float) * -1
    )
    list_preface_max_N_UGT, list_preface_max_N_BGT = [], []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        list_preface_max_N_UGT.append(
            max(row_1["g_NEd_trek_UGT"], row_1["g_NEd_druk_UGT"])
        )
        list_preface_max_N_BGT.append(
            max(row_1["g_NEd_trek_BGT"], row_1["g_NEd_druk_BGT"])
        )
    df_calculations_preface_forces["g_max_N_UGT"] = list_preface_max_N_UGT
    df_calculations_preface_forces["g_max_N_BGT"] = list_preface_max_N_BGT
    df_calculations_preface_forces["s_FEd_UGT"] = (
        df_calculations_preface_forces["s_NEd_druk_UGT"]
        * γstempel_UGT
        * sin(df_calculations_preface_forces["[°]"] * pi / 180)
    ) / (df_calculations_preface_forces["g_n"] * 2)
    df_calculations_preface_forces["s_FEd_BGT"] = (
        df_calculations_preface_forces["s_NEd_druk_BGT"]
        * γstempel_BGT
        * sin(df_calculations_preface_forces["[°]"] * pi / 180)
    ) / (df_calculations_preface_forces["g_n"] * 2)
    df_calculations_preface_forces["s_FEd_BGT"] = abs(
        df_calculations_preface_forces["s_FEd_BGT"]
    )
    df_calculations_preface_forces[
        "thickness_plate"
    ] = params.calculation.thickness_plate
    list_preface_beff = []

    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        l1 = (
            row_1["tw"]
            + 2 * row_1["r"]
            + 2 * row_1["tf"]
            + 2 * row_1["thickness_plate"]
            + (row_1["tw"] + 2 * row_1["tf"] + 2 * row_1["thickness_plate"])
        )
        l2 = ((4 * (arcsin(150 / (0.5 * row_1["s_bu"]))) * 180 / pi) / 360) * pi * (
            row_1["s_bu"] / 2
        ) + 2 * row_1["thickness_plate"]
        if l1 < l2:
            list_preface_beff.append(l1)
        else:
            list_preface_beff.append(l2)

    df_calculations_preface_forces["s_beff"] = list_preface_beff
    df_calculations_preface_forces["FR_d"] = (
        df_calculations_preface_forces["s_fy"]
        * df_calculations_preface_forces["s_beff"]
        * df_calculations_preface_forces["s_wa"]
        / 1000
    )
    df_calculations_preface_forces["s_uc_FEd_FRd_UGT"] = (
        df_calculations_preface_forces["s_FEd_UGT"]
        / df_calculations_preface_forces["FR_d"]
    )
    df_calculations_preface_forces["s_uc_FEd_FRd_BGT"] = (
        df_calculations_preface_forces["s_FEd_BGT"]
        / df_calculations_preface_forces["FR_d"]
    )
    # TOETSING KRACHTSINLEIDING ZONDER VERSTIJVERS
    list_preface_buiging = []
    df_calculations_preface_forces["c/tε_lijf"] = (
        (
            df_calculations_preface_forces["h"]
            - df_calculations_preface_forces["tf"]
            - df_calculations_preface_forces["tf"]
            - df_calculations_preface_forces["r"]
            - df_calculations_preface_forces["r"]
        )
        / df_calculations_preface_forces["tw"]
        / df_calculations_preface_forces["g_ε"]
    )
    df_calculations_preface_forces["c/tε_flens"] = (
        (
            df_calculations_preface_forces["b"] / 2
            - (df_calculations_preface_forces["tw"] / 2)
            - df_calculations_preface_forces["r"]
        )
        / df_calculations_preface_forces["tf"]
        / df_calculations_preface_forces["g_ε"]
    )
    list_preface_klasse_lijf_buiging = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if row_1["c/tε_lijf"] <= 72:
            list_preface_klasse_lijf_buiging.append(1)
        elif 72 > row_1["c/tε_lijf"] <= 83:
            list_preface_klasse_lijf_buiging.append(2)
        elif 83 > row_1["c/tε_lijf"] <= 124:
            list_preface_klasse_lijf_buiging.append(3)
        else:
            list_preface_klasse_lijf_buiging.append(4)
    df_calculations_preface_forces[
        "drsn. kl. lijf_buiging"
    ] = list_preface_klasse_lijf_buiging
    list_preface_Wy_klasse_lijf_buiging = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if row_1["drsn. kl. lijf_buiging"] < 3:
            list_preface_Wy_klasse_lijf_buiging.append(row_1["Wy_pl"])
        else:
            list_preface_Wy_klasse_lijf_buiging.append(row_1["Wy_el"])
    df_calculations_preface_forces["g_Wyy"] = list_preface_Wy_klasse_lijf_buiging
    df_calculations_preface_forces["g_σfEd_UGT"] = (
        (
            (df_calculations_preface_forces["g_MYi/MYj_UGT"] * 10**6 * γm_gording_UGT)
            / (
                df_calculations_preface_forces["g_Wyy"]
                * df_calculations_preface_forces["g_n"]
            )
        )
        + (
            (df_calculations_preface_forces["g_max_N_UGT"] * γm_gording_UGT * 10**3)
            / (
                df_calculations_preface_forces["A"]
                * df_calculations_preface_forces["g_n"]
            )
        )
    ) / 2
    df_calculations_preface_forces["g_σfEd_BGT"] = (
        (
            (df_calculations_preface_forces["g_MYi/MYj_BGT"] * 10**6 * γm_gording_BGT)
            / (
                df_calculations_preface_forces["g_Wyy"]
                * df_calculations_preface_forces["g_n"]
            )
        )
        + (
            (df_calculations_preface_forces["g_max_N_BGT"] * γm_gording_BGT * 10**3)
            / (
                df_calculations_preface_forces["A"]
                * df_calculations_preface_forces["g_n"]
            )
        )
    ) / 2

    list_preface_g_bf = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if row_1["b"] <= (25 * row_1["tf"]):
            list_preface_g_bf.append(row_1["b"])
        else:
            list_preface_g_bf.append(25 * row_1["tf"])
    df_calculations_preface_forces["g_bf"] = list_preface_g_bf

    df_calculations_preface_forces["c"] = (
        df_calculations_preface_forces["s_wa"]
        + (2 * df_calculations_preface_forces["thickness_plate"])
        + (2 * df_calculations_preface_forces["tf"])
    )
    df_calculations_preface_forces["g_d1_UGT"] = (
        2
        * df_calculations_preface_forces["tf"]
        * sqrt(
            df_calculations_preface_forces["g_bf"]
            / df_calculations_preface_forces["tw"]
        )
        * sqrt(
            df_calculations_preface_forces["g_fy"]
            / df_calculations_preface_forces["g_fy"]
        )
        * sqrt(
            1
            - (
                df_calculations_preface_forces["g_σfEd_UGT"]
                / df_calculations_preface_forces["g_fy"]
            )
            ** 2
        )
    )
    df_calculations_preface_forces["g_d1_BGT"] = (
        2
        * df_calculations_preface_forces["tf"]
        * sqrt(
            df_calculations_preface_forces["g_bf"]
            / df_calculations_preface_forces["tw"]
        )
        * sqrt(
            df_calculations_preface_forces["g_fy"]
            / df_calculations_preface_forces["g_fy"]
        )
        * sqrt(
            1
            - (
                df_calculations_preface_forces["g_σfEd_BGT"]
                / df_calculations_preface_forces["g_fy"]
            )
            ** 2
        )
    )
    df_calculations_preface_forces["F1Rd_UGT"] = (
        (
            df_calculations_preface_forces["c"]
            + df_calculations_preface_forces["g_d1_UGT"]
        )
        * df_calculations_preface_forces["tw"]
        * df_calculations_preface_forces["g_fy"]
        / 1000
    )
    df_calculations_preface_forces["F1Rd_BGT"] = (
        (
            df_calculations_preface_forces["c"]
            + df_calculations_preface_forces["g_d1_BGT"]
        )
        * df_calculations_preface_forces["tw"]
        * df_calculations_preface_forces["g_fy"]
        / 1000
    )
    df_calculations_preface_forces["g_uc_FEd_F1Rd_UGT"] = (
        df_calculations_preface_forces["s_FEd_UGT"]
        / df_calculations_preface_forces["F1Rd_UGT"]
    )
    df_calculations_preface_forces["g_uc_FEd_F1Rd_BGT"] = (
        df_calculations_preface_forces["s_FEd_BGT"]
        / df_calculations_preface_forces["F1Rd_BGT"]
    )
    # """ TOETSING LOKAAL PLOOIEN VAN HET LIJF"""
    list_preface_c_h_2t_tf = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if (row_1["c"] / (row_1["h"] - (2 * row_1["tf"]))) <= 0.2:
            list_preface_c_h_2t_tf.append(row_1["c"] / (row_1["h"] - (2 * row_1["tf"])))
        else:
            list_preface_c_h_2t_tf.append(0.2)
    df_calculations_preface_forces["c/(h-2t*tf)"] = list_preface_c_h_2t_tf
    df_calculations_preface_forces["F2Rd"] = (
        0.5
        * df_calculations_preface_forces["tw"] ** 2
        * sqrt(YOUNG_MODULUS_STEEL * df_calculations_preface_forces["g_fy"])
        * (
            sqrt(
                df_calculations_preface_forces["tf"]
                / df_calculations_preface_forces["tw"]
            )
            + (
                3
                * (
                    df_calculations_preface_forces["tw"]
                    / df_calculations_preface_forces["tf"]
                )
                * df_calculations_preface_forces["c/(h-2t*tf)"]
            )
        )
        / 1000
    )
    df_calculations_preface_forces["uc_FEd_F2Rd_UGT"] = (
        df_calculations_preface_forces["s_FEd_UGT"]
        / df_calculations_preface_forces["F2Rd"]
    )
    df_calculations_preface_forces["uc_FEd_F2Rd_BGT"] = (
        df_calculations_preface_forces["s_FEd_BGT"]
        / df_calculations_preface_forces["F2Rd"]
    )
    df_calculations_preface_forces["uc_FEd_F2RD_MyEd_MyRd_UGT"] = (
        df_calculations_preface_forces["s_FEd_UGT"]
        / (1.5 * df_calculations_preface_forces["F2Rd"])
    ) + (
        (
            (
                (df_calculations_preface_forces["g_MYi/MYj_UGT"] * γm_gording_UGT)
                / df_calculations_preface_forces["g_n"]
            )
            * 10**6
        )
        / (
            1.5
            * df_calculations_preface_forces["g_fy"]
            * df_calculations_preface_forces["g_Wyy"]
        )
    )
    df_calculations_preface_forces["uc_FEd_F2RD_MyEd_MyRd_BGT"] = (
        df_calculations_preface_forces["s_FEd_BGT"]
        / (1.5 * df_calculations_preface_forces["F2Rd"])
    ) + (
        (
            (
                (df_calculations_preface_forces["g_MYi/MYj_BGT"] * γm_gording_BGT)
                / df_calculations_preface_forces["g_n"]
            )
            * 10**6
        )
        / (
            1.5
            * df_calculations_preface_forces["g_fy"]
            * df_calculations_preface_forces["g_Wyy"]
        )
    )
    # """TOETSING GLOBAAL PLOOIEN VAN HET LIJF"""
    list_preface_beff_2 = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if ((row_1["h"] / 2) + (row_1["s_bu"] / 2)) < row_1["h"]:
            list_preface_beff_2.append((row_1["h"] / 2) + (row_1["s_bu"] / 2))
        else:
            list_preface_beff_2.append(row_1["h"])
    df_calculations_preface_forces["g_beff"] = list_preface_beff_2
    df_calculations_preface_forces["Fcr"] = (
        (
            pi**2
            * (
                (1 / 12)
                * df_calculations_preface_forces["g_beff"]
                * df_calculations_preface_forces["tw"] ** 3
            )
            * YOUNG_MODULUS_STEEL
        )
        / df_calculations_preface_forces["h"] ** 2
        / 1000
    )
    df_calculations_preface_forces["g_λrel"] = sqrt(
        (df_calculations_preface_forces["A"] * df_calculations_preface_forces["g_fy"])
        / (df_calculations_preface_forces["Fcr"] * 1000)
    )
    df_calculations_preface_forces["uc_FEd_Fcr_UGT"] = (
        df_calculations_preface_forces["s_FEd_UGT"]
        / df_calculations_preface_forces["Fcr"]
    )
    df_calculations_preface_forces["uc_FEd_Fcr_BGT"] = (
        df_calculations_preface_forces["s_FEd_BGT"]
        / df_calculations_preface_forces["Fcr"]
    )
    list_preface_uc_FEd_Fcr_UGT = []
    list_preface_uc_FEd_Fcr_BGT = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if row_1["uc_FEd_Fcr_UGT"] <= 0.04:
            list_preface_uc_FEd_Fcr_UGT.append("Knikeffecten verwaarlozen")
        else:
            list_preface_uc_FEd_Fcr_UGT.append("knikeffecten niet verwaarlozen")
        if row_1["uc_FEd_Fcr_BGT"] <= 0.04:
            list_preface_uc_FEd_Fcr_BGT.append("Knikeffecten verwaarlozen")
        else:
            list_preface_uc_FEd_Fcr_BGT.append("knikeffecten niet verwaarlozen")
    df_calculations_preface_forces["check_FEd_Fcr_UGT"] = list_preface_uc_FEd_Fcr_UGT
    df_calculations_preface_forces["check_FEd_Fcr_BGT"] = list_preface_uc_FEd_Fcr_BGT
    list_knikkromme_yy_txt = (
        []
    )  ###### NAVRAGEN OVER KNIKKROMME IVM INTERPRETATIE -> nu is kromme c toegepast, maar de vraag is of dat goed is
    list_knikkromme_yy = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if (row_1["h"] / row_1["b"]) > 1.2:
            if row_1["tf"] <= 40:
                list_knikkromme_yy_txt.append("b")
                list_knikkromme_yy.append(0.34)
            if 40 < row_1["tf"] <= 100:
                list_knikkromme_yy_txt.append("c")
                list_knikkromme_yy.append(0.49)
        else:
            if row_1["tf"] <= 100:
                list_knikkromme_yy_txt.append("c")
                list_knikkromme_yy.append(0.49)
            else:
                list_knikkromme_yy_txt.append("d")
                list_knikkromme_yy.append(0.76)
    df_calculations_preface_forces["knikkromme_txt"] = list_knikkromme_yy_txt
    df_calculations_preface_forces["knikkromme"] = list_knikkromme_yy
    df_calculations_preface_forces["knikkromme"] = 0.49
    df_calculations_preface_forces["g_Φ"] = 0.5 * (
        1
        + (
            df_calculations_preface_forces["knikkromme"]
            * (df_calculations_preface_forces["g_λrel"] - 0.2)
        )
        + df_calculations_preface_forces["g_λrel"] ** 2
    )
    df_calculations_preface_forces["g_χ"] = 1 / (
        df_calculations_preface_forces["g_Φ"]
        + sqrt(
            df_calculations_preface_forces["g_Φ"] ** 2
            - df_calculations_preface_forces["g_λrel"] ** 2
        )
    )
    df_calculations_preface_forces["uc_g_χ"] = df_calculations_preface_forces["g_χ"] / 1
    df_calculations_preface_forces["FbRd"] = (
        df_calculations_preface_forces["g_χ"]
        * df_calculations_preface_forces["A"]
        * df_calculations_preface_forces["g_fy"]
    ) / 1000
    df_calculations_preface_forces["uc_FEd_FbRD_UGT"] = (
        df_calculations_preface_forces["s_FEd_UGT"]
        / df_calculations_preface_forces["FbRd"]
    )
    df_calculations_preface_forces["uc_FEd_FbRD_BGT"] = (
        df_calculations_preface_forces["s_FEd_BGT"]
        / df_calculations_preface_forces["FbRd"]
    )
    return df_calculations_preface_forces


def get_df_results_preface_forces(
    df_calculations_preface_forces: DataFrame,
) -> DataFrame:
    df_results_preface_forces = DataFrame(
        data=None, columns=columns_results_preface_forces
    )
    for column_name in columns_results_preface_forces:
        if column_name in columns_calculations_preface_forces:
            df_results_preface_forces[column_name] = df_calculations_preface_forces[
                column_name
            ]

    df_results_preface_forces["St."] = df_calculations_preface_forces[
        "g_St."
    ]  # ???? why
    df_results_preface_forces["g_profiel_naam"] = df_calculations_preface_forces[
        "g_profiel"
    ]
    df_results_preface_forces["n_profiles"] = df_calculations_preface_forces["g_n"]
    df_results_preface_forces["g_Sterkteklasse"] = df_calculations_preface_forces[
        "g_fy"
    ]
    df_results_preface_forces["s_profiel_naam"] = df_calculations_preface_forces[
        "s_aansl_St."
    ]
    df_results_preface_forces["s_Sterkteklasse"] = df_calculations_preface_forces[
        "s_fy"
    ]
    df_results_preface_forces["Hoek"] = df_calculations_preface_forces["[°]"]
    df_results_preface_forces["t_drukschot"] = df_calculations_preface_forces["tw"]
    df_results_preface_forces["FEd_UGT"] = df_calculations_preface_forces["s_FEd_UGT"]
    df_results_preface_forces["NXi/NXj_UGT"] = df_calculations_preface_forces[
        "g_max_N_UGT"
    ]
    df_results_preface_forces["MYi/MYj_UGT"] = df_calculations_preface_forces[
        "g_MYi/MYj_UGT"
    ]
    df_results_preface_forces["FEd_BGT"] = df_calculations_preface_forces["s_FEd_BGT"]
    df_results_preface_forces["NXi/NXj_BGT"] = df_calculations_preface_forces[
        "g_max_N_BGT"
    ]
    df_results_preface_forces["MYi/MYj_BGT"] = df_calculations_preface_forces[
        "g_MYi/MYj_BGT"
    ]
    df_results_preface_forces["s_uc_FEd_FRd_UGT"] = df_calculations_preface_forces[
        "s_uc_FEd_FRd_UGT"
    ]
    df_results_preface_forces["s_uc_FEd_FRd_BGT"] = df_calculations_preface_forces[
        "s_uc_FEd_FRd_BGT"
    ]
    df_results_preface_forces[
        "uc_FEd_F2RD_MyEd_MyRd_BGT"
    ] = df_calculations_preface_forces["uc_FEd_F2RD_MyEd_MyRd_BGT"]
    df_results_preface_forces["uc_g_χ"] = df_calculations_preface_forces["uc_g_χ"]
    df_results_preface_forces["uc_FEd_FbRD_UGT"] = df_calculations_preface_forces[
        "uc_FEd_FbRD_UGT"
    ]
    df_results_preface_forces["uc_FEd_FbRD_BGT"] = df_calculations_preface_forces[
        "uc_FEd_FbRD_BGT"
    ]
    df_results_preface_forces["check_FEd_Fcr_UGT"] = df_calculations_preface_forces[
        "check_FEd_Fcr_UGT"
    ]
    df_results_preface_forces["check_FEd_Fcr_BGT"] = df_calculations_preface_forces[
        "check_FEd_Fcr_BGT"
    ]
    df_results_preface_forces = df_results_preface_forces.replace(nan, 0)
    list_max_uc_preface_UGT = []
    list_max_uc_preface_U = []
    list_max_uc_preface_BGT = []
    list_max_uc_preface_B = []

    for index_1, row_1 in df_results_preface_forces.iterrows():
        list_max_uc_preface_UGT.append(
            max(
                row_1["s_uc_FEd_FRd_UGT"],
                row_1["g_uc_FEd_F1Rd_UGT"],
                row_1["uc_FEd_F2Rd_UGT"],
                row_1["uc_FEd_F2RD_MyEd_MyRd_UGT"],
                row_1["uc_FEd_Fcr_UGT"],
                row_1["uc_FEd_FbRD_UGT"],
            )
        )
        list_max_uc_preface_U.append(
            max(
                row_1["s_uc_FEd_FRd_UGT"],
                row_1["g_uc_FEd_F1Rd_UGT"],
                row_1["uc_FEd_F2Rd_UGT"],
                row_1["uc_FEd_F2RD_MyEd_MyRd_UGT"],
                row_1["uc_FEd_Fcr_UGT"],
                row_1["uc_FEd_FbRD_UGT"],
                row_1["uc_g_χ"],
            )
        )

        list_max_uc_preface_BGT.append(
            max(
                row_1["s_uc_FEd_FRd_BGT"],
                row_1["g_uc_FEd_F1Rd_BGT"],
                row_1["uc_FEd_F2Rd_BGT"],
                row_1["uc_FEd_F2RD_MyEd_MyRd_BGT"],
                row_1["uc_FEd_Fcr_BGT"],
                row_1["uc_FEd_FbRD_BGT"],
            )
        )
        list_max_uc_preface_B.append(
            max(
                row_1["s_uc_FEd_FRd_BGT"],
                row_1["g_uc_FEd_F1Rd_BGT"],
                row_1["uc_FEd_F2Rd_BGT"],
                row_1["uc_FEd_F2RD_MyEd_MyRd_BGT"],
                row_1["uc_FEd_Fcr_BGT"],
                row_1["uc_FEd_FbRD_BGT"],
                row_1["uc_g_χ"],
            )
        )

    df_results_preface_forces["uc_maatgevend_UGT"] = list_max_uc_preface_UGT
    df_results_preface_forces["uc_maatgevend_U"] = list_max_uc_preface_U
    df_results_preface_forces["uc_maatgevend_BGT"] = list_max_uc_preface_BGT
    df_results_preface_forces["uc_maatgevend_B"] = list_max_uc_preface_B

    list_results_preface_uc_UGT = []
    for index_1, row_1 in df_results_preface_forces.iterrows():
        if row_1["uc_maatgevend_U"] <= 1:
            list_results_preface_uc_UGT.append("Voldoet")
        else:
            list_results_preface_uc_UGT.append("Voldoet niet")
    df_results_preface_forces["result"] = list_results_preface_uc_UGT

    list_results_preface_uc_BGT = []
    for index_1, row_1 in df_results_preface_forces.iterrows():
        if row_1["uc_maatgevend_B"] <= 1:
            list_results_preface_uc_BGT.append("Voldoet")
        else:
            list_results_preface_uc_BGT.append("Voldoet niet")
    df_results_preface_forces["result"] = list_results_preface_uc_BGT

    return df_results_preface_forces


def get_df_angle_struts(
    df_calculations_purlins: DataFrame,
    df_calculations_stamps: DataFrame,
    df_nodes: DataFrame,
) -> DataFrame:
    """Return The portion of the dataframe which calculates angles between the struts"""
    df_calculations_preface_forces = DataFrame(data=None, columns=None)
    df_calculations_preface_forces["g_St."] = df_calculations_purlins["St."]
    df_calculations_preface_forces["g_ki"] = df_calculations_purlins["ki"]
    df_calculations_preface_forces["g_ki_x"] = df_calculations_purlins["ki_x"]
    df_calculations_preface_forces["g_ki_z"] = df_calculations_purlins["ki_z"]
    df_calculations_preface_forces["g_kj"] = df_calculations_purlins["kj"]
    df_calculations_preface_forces["g_kj_x"] = df_calculations_purlins["kj_x"]
    df_calculations_preface_forces["g_kj_z"] = df_calculations_purlins["kj_z"]
    df_calculations_preface_forces["Kn. Pos."] = df_calculations_purlins["Kn. Pos."]

    # verwijderen alle gordingen met waarden tussen de knopen
    # This will remove all row for which Kn. Pos. is a float, that is to say row for which Position is given and not node
    list_keep_values = []
    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if "." not in row_1["Kn. Pos."]:
            list_keep_values.append(row_1["Kn. Pos."])
    df_calculations_preface_forces = df_calculations_preface_forces[
        df_calculations_preface_forces["Kn. Pos."].isin(list_keep_values)
    ]
    # aanlsuiting stempel op knoop in gording

    dict_stamps_nodes = {"stamps": {}, "ki": {}, "kj": {}}
    for index_1, row_1 in df_calculations_stamps.iterrows():
        dict_stamps_nodes["stamps"].update({str(row_1["ki"]): row_1["St."]})
        dict_stamps_nodes["stamps"].update({str(row_1["kj"]): row_1["St."]})
        dict_stamps_nodes["ki"].update({row_1["St."]: row_1["ki"]})
        dict_stamps_nodes["kj"].update({row_1["St."]: row_1["kj"]})

    df_calculations_preface_forces["s_aansl_St."] = df_calculations_preface_forces[
        "Kn. Pos."
    ].map(dict_stamps_nodes["stamps"])
    df_calculations_preface_forces["s_aansl_St."] = df_calculations_preface_forces[
        "s_aansl_St."
    ].replace(nan, ".")

    list_keep_values_2 = []
    df_calculations_preface_forces["s_aansl_St."] = df_calculations_preface_forces[
        "s_aansl_St."
    ].replace(nan, 0)

    for index_1, row_1 in df_calculations_preface_forces.iterrows():
        if "." not in row_1["s_aansl_St."]:
            list_keep_values_2.append(row_1["s_aansl_St."])

    df_calculations_preface_forces = df_calculations_preface_forces[
        df_calculations_preface_forces["s_aansl_St."].isin(list_keep_values_2)
    ]
    df_calculations_preface_forces = df_calculations_preface_forces.sort_values(
        by=["s_aansl_St."]
    )

    df_calculations_preface_forces["s_ki"] = df_calculations_preface_forces[
        "s_aansl_St."
    ].map(dict_stamps_nodes["ki"])
    df_calculations_preface_forces["s_ki"] = df_calculations_preface_forces[
        "s_ki"
    ].replace(nan, 0)
    df_calculations_preface_forces["s_kj"] = df_calculations_preface_forces[
        "s_aansl_St."
    ].map(dict_stamps_nodes["kj"])
    df_calculations_preface_forces["s_kj"] = df_calculations_preface_forces[
        "s_kj"
    ].replace(nan, 0)
    df_calculations_preface_forces["s_ki"] = df_calculations_preface_forces[
        "s_ki"
    ].astype(int)
    df_calculations_preface_forces["s_kj"] = df_calculations_preface_forces[
        "s_kj"
    ].astype(int)
    dict_node_x, dict_node_z = get_nodes_dict_x_z(df_nodes)

    df_calculations_preface_forces["s_ki_x"] = df_calculations_preface_forces[
        "s_ki"
    ].map(dict_node_x)
    df_calculations_preface_forces["s_ki_z"] = df_calculations_preface_forces[
        "s_ki"
    ].map(dict_node_z)
    df_calculations_preface_forces["s_kj_x"] = df_calculations_preface_forces[
        "s_kj"
    ].map(dict_node_x)
    df_calculations_preface_forces["s_kj_z"] = df_calculations_preface_forces[
        "s_kj"
    ].map(dict_node_z)
    df_calculations_preface_forces["Kn. Pos."] = df_calculations_preface_forces[
        "Kn. Pos."
    ].astype(int)
    df_calculations_preface_forces["x_A"] = df_calculations_preface_forces[
        "Kn. Pos."
    ].map(dict_node_x)
    df_calculations_preface_forces["z_A"] = df_calculations_preface_forces[
        "Kn. Pos."
    ].map(dict_node_z)
    df_calculations_preface_forces["x_B"] = where(
        (
            df_calculations_preface_forces["x_A"]
            == df_calculations_preface_forces["g_ki_x"]
        )
        & (
            df_calculations_preface_forces["z_A"]
            == df_calculations_preface_forces["g_ki_z"]
        ),
        df_calculations_preface_forces["g_kj_x"],
        df_calculations_preface_forces["g_ki_x"],
    )
    df_calculations_preface_forces["z_B"] = where(
        (
            df_calculations_preface_forces["x_A"]
            == df_calculations_preface_forces["g_ki_x"]
        )
        & (
            df_calculations_preface_forces["z_A"]
            == df_calculations_preface_forces["g_ki_z"]
        ),
        df_calculations_preface_forces["g_kj_z"],
        df_calculations_preface_forces["g_ki_z"],
    )
    df_calculations_preface_forces["x_C"] = where(
        (
            df_calculations_preface_forces["x_A"]
            == df_calculations_preface_forces["s_ki_x"]
        )
        & (
            df_calculations_preface_forces["z_A"]
            == df_calculations_preface_forces["s_ki_z"]
        ),
        df_calculations_preface_forces["s_kj_x"],
        df_calculations_preface_forces["s_ki_x"],
    )
    df_calculations_preface_forces["z_C"] = where(
        (
            df_calculations_preface_forces["x_A"]
            == df_calculations_preface_forces["s_ki_x"]
        )
        & (
            df_calculations_preface_forces["z_A"]
            == df_calculations_preface_forces["s_ki_z"]
        ),
        df_calculations_preface_forces["s_kj_z"],
        df_calculations_preface_forces["s_ki_z"],
    )
    a = (
        (
            df_calculations_preface_forces["x_C"].astype(float)
            - df_calculations_preface_forces["x_B"].astype(float)
        )
        ** 2
        + (
            df_calculations_preface_forces["z_C"].astype(float)
            - df_calculations_preface_forces["z_B"].astype(float)
        )
        ** 2
    ) ** 0.5
    b = (
        (
            df_calculations_preface_forces["x_A"].astype(float)
            - df_calculations_preface_forces["x_B"].astype(float)
        )
        ** 2
        + (
            df_calculations_preface_forces["z_A"].astype(float)
            - df_calculations_preface_forces["z_B"].astype(float)
        )
        ** 2
    ) ** 0.5
    c = (
        (
            df_calculations_preface_forces["x_A"].astype(float)
            - df_calculations_preface_forces["x_C"].astype(float)
        )
        ** 2
        + (
            df_calculations_preface_forces["z_A"].astype(float)
            - df_calculations_preface_forces["z_C"].astype(float)
        )
        ** 2
    ) ** 0.5

    # df_calculations_preface_forces['[°]'] = df_calculations_preface_forces['[°]'].astype(float)
    arccos_arg: DataFrame = (-(a**2) + (b**2) + (c**2)) / (2 * b * c)
    arccos_arg = arccos_arg.apply(
        lambda row: max(min(1, row), -1)
    )  # Make sure each arccos input is in range -1 to 1
    df_calculations_preface_forces["[°]"] = arccos(arccos_arg)
    df_calculations_preface_forces["[°]"] = degrees(
        df_calculations_preface_forces["[°]"]
    )
    return df_calculations_preface_forces


def show_df(df_calculations_stamps):
    with option_context(
        "display.max_rows", None, "display.max_columns", None
    ):  # more options can be specified also
        print(df_calculations_stamps)
