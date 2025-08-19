import re

from viktor.parametrization import DownloadButton
from viktor.parametrization import (
    Parametrization,
    Tab,
    Section,
    NumberField,
    LineBreak,
    TextField,
    TableInput,
    SetParamsButton,
    OptionListElement,
    OptionField,
    AutocompleteField,
    MultiSelectField,
    OutputField)
from viktor.parametrization import ToggleButton

zijde_options = [
    OptionListElement("Negative"),
    OptionListElement("Positive"),
]

sterkteklasse_options = [
    OptionListElement("S235"),
    OptionListElement("S275"),
    OptionListElement("S355"),
    OptionListElement("S420"),
    OptionListElement("S460"),
]

m_factor_options = [
    OptionListElement("1/8"),
    OptionListElement("1/10"),
    OptionListElement("3/35"),
    OptionListElement("1/12"),
    OptionListElement("1/16"),
]

richting_oplegging_options = [
    OptionListElement("100"),
    OptionListElement("110"),
    OptionListElement("111"),
    OptionListElement("010"),
    OptionListElement("011"),
    OptionListElement("001"),
    OptionListElement("X--"),
    OptionListElement("XZ-"),
    OptionListElement("XZR"),
    OptionListElement("-Z-"),
    OptionListElement("-ZR"),
    OptionListElement("--R"),
]

veer_richting_options = [
    OptionListElement("X"),
    OptionListElement("Z"),
    OptionListElement("R"),
]

veer_type_options = [
    OptionListElement("Normaal"),
    OptionListElement("Trek"),
    OptionListElement("Druk"),
]

BGT_calamity_options = [
    # OptionListElement("strut_removal", "uitval"),
    OptionListElement("point_load", "stootbelasting puntlast 100kN"),
]

profile_name_regex_pattern = r"HEB\d{3,4}|B\d{3}\/\d+.?(\d+)?"  # Can be either of type 'HEB500' or of type 'B508/12.5'

BGT_options = [
    OptionListElement("point_load_0", "stootbelasting puntlast 0kN"),
    OptionListElement("point_load_100", "stootbelasting puntlast 100kN"),
    # OptionListElement("strut_removal", "uitval"),
]


def _check_beam_table(params, **kwargs):
    """Perform check on input cells of 'Staven' table."""
    fails = []

    # Allowed formats
    regex_heb = r"HEB\d{3,4}"
    regex_b = r"B\d{3}\/\d+.?(\d+)?"
    allowed_heb_sizes = list(range(100, 400, 20)) + list(range(400, 1050, 50))

    # Check if profile name is matching allowed formats
    for i, beam in enumerate(params.general.beams.staven):
        match_heb = re.fullmatch(regex_heb, beam.profiel)
        match_b = re.fullmatch(regex_b, beam.profiel)
        if match_heb:
            digits = re.findall(r"\d+", beam.profiel)[0]
            if int(digits) not in allowed_heb_sizes:
                fails.append(
                    f"Profiel '{beam.profiel}' in rij {i} grootte '{digits}' is niet toegestaan."
                )

        # If no match with any format, add exception to list
        elif not match_b:
            fails.append(
                f"Profiel '{beam.profiel}' in rij {i} moet een van volgende formaten volgen: "
                f"'HEB500' of 'B508/12.5'. "
            )

    # Return fails else return correct
    if fails:
        return "FOUT: " + " -".join(fail for fail in fails)
    return "Tabel correct ingevuld."


class XMLuploadParametrization(Parametrization):
    project_general = Tab("Algemeen")
    project_general.basics = Section("Invoer algemeen")
    project_general.basics.name_client = TextField("Opdrachtgever:")
    project_general.basics.name1 = LineBreak()
    project_general.basics.name_number = TextField("Hektec werknummer:")
    project_general.basics.name_ = LineBreak()
    project_general.basics.name_engineer = TextField("Naam engineer:")
    project_general.basics.name2 = LineBreak()
    project_general.basics.name_project = TextField("Project:")
    project_general.basics.name4 = LineBreak()
    project_general.basics.name_location = TextField("Locatie:")
    project_general.basics.nam6 = LineBreak()
    project_general.basics.date = TextField("Datum:")
    project_general.basics.name3 = LineBreak()
    project_general.basics.name_layer = TextField("Niveau:")
    project_general.basics.name5 = LineBreak()
    project_general.basics.name_attentoins = TextField("Opmerkingen:")

    general = Tab("Invoer geometrie")
    general.xml = Section("Inlezen XML-gegevens")
    general.xml.set_params = SetParamsButton("Reset XML", "set_params_in_group")
    general.xml.download = DownloadButton(
        "Download updated XML", "download_updated_xml"
    )

    general.geometry = Section("Knopen")
    general.geometry.nodes = TableInput("Knopen")
    general.geometry.nodes.id = TextField("Node ID")
    general.geometry.nodes.x = NumberField("x coördinaat")
    general.geometry.nodes.z = NumberField("z coördinaat")

    general.beams = Section("Staven")
    general.beams.section = SetParamsButton(
        "Voer staaf lengte en moment factor in", "set_params_in_group"
    )
    general.beams.warningfield = OutputField(
        "Tabel controle", value=_check_beam_table, flex=100
    )
    general.beams.staven = TableInput("Staven")
    general.beams.staven.id = TextField("Staaf nr.")
    general.beams.staven.ki = TextField("Knoop i")
    general.beams.staven.kj = TextField("Knoop j")
    general.beams.staven.profiel = TextField("Profiel")
    general.beams.staven.strength_class = AutocompleteField(
        "Sterkteklasse", options=sterkteklasse_options
    )
    general.beams.staven.aansli = TextField("Aansluiting i")
    general.beams.staven.aanslj = TextField("Aansluiting j")
    general.beams.staven.hoh = TextField("staaf lengte [m]")

    general.bedding = Section("Bedding")
    general.bedding.staven = TableInput("Bedding")
    general.bedding.staven.ID = TextField("Bedding ID")
    general.bedding.staven.BarID = TextField("Staven")
    general.bedding.staven.BeddingValue = TextField("Bedding [kN/m3]")
    general.bedding.staven.BeddingWidth = TextField("Breedte [mm]")
    general.bedding.staven.Side = OptionField("Zijde", options=zijde_options)

    general.FixedSupports = Section("Opleggingen")
    general.FixedSupports.nodes = TableInput("Opleggingen")
    general.FixedSupports.nodes.ID = TextField("Oplegging ID")
    general.FixedSupports.nodes.NodeID = TextField("Knoop")
    general.FixedSupports.nodes.DirectionXZR = OptionField(
        "Richting XZR", options=richting_oplegging_options
    )

    general.SpringSupports = Section("Veren")
    general.SpringSupports.nodes = TableInput("Veren")
    general.SpringSupports.nodes.ID = TextField("Veer ID")
    general.SpringSupports.nodes.NodeID = TextField("Knoop")
    general.SpringSupports.nodes.Direction = OptionField(
        "Richting", options=veer_richting_options
    )
    general.SpringSupports.nodes.SpringConstant = TextField("Veerwaarde")
    general.SpringSupports.nodes.SpringType = OptionField(
        "Veertype", options=veer_type_options
    )
    general.SpringSupports.nodes.LowerLimit = TextField("Ondergrens")
    general.SpringSupports.nodes.UpperLimit = TextField("Bovengrens")
    general.SpringSupports.nodes.support_lsc_angle = NumberField("Veren hoek")

    general.BarLoad_UGT = Section("Belastingen UGT")
    general.BarLoad_UGT.staven = TableInput("Staaflasten")
    general.BarLoad_UGT.staven.ID = TextField("!!>>Belasting ID<<!!")
    general.BarLoad_UGT.staven.BarID = TextField("Staaf nummer")
    general.BarLoad_UGT.staven.Type = TextField("Type")
    general.BarLoad_UGT.staven.LoadStart = TextField("q1/F/M")
    general.BarLoad_UGT.staven.LoadEnd = TextField("q2")
    general.BarLoad_UGT.staven.DistanceStart = TextField("a")
    general.BarLoad_UGT.staven.DistanceEnd = TextField("b")

    general.BarLoad_BGT = Section("Belastingen BGT")
    general.BarLoad_BGT.staven = TableInput("Staaflasten")
    general.BarLoad_BGT.staven.ID = TextField("!!>>Belasting ID<<!!")
    general.BarLoad_BGT.staven.BarID = TextField("Staaf nummer")
    general.BarLoad_BGT.staven.Type = TextField("Type")
    general.BarLoad_BGT.staven.LoadStart = TextField("q1/F/M")
    general.BarLoad_BGT.staven.LoadEnd = TextField("q2")
    general.BarLoad_BGT.staven.DistanceStart = TextField("a")
    general.BarLoad_BGT.staven.DistanceEnd = TextField("b")

    general.LoadCases = Section("Belasting gevallen")
    general.LoadCases.loads = TableInput("Belasting gevallen", visible=False)
    general.LoadCases.loads.ID = TextField("Belastinggeval ID")
    general.LoadCases.loads.description = TextField("Belastinggeval")
    general.LoadCases.loads.LoadCaseType = TextField("Belasting Type")

    calculation = Tab("Invoer berekening")
    calculation.UGT = ToggleButton("UGT Analyse", default=True)
    calculation.BGT = ToggleButton("BGT Analyse", default=True)
    calculation.calamity = MultiSelectField(
        "Calamiteit selectie", options=BGT_calamity_options, default=["point_load"]
    )
    calculation.lb = LineBreak()
    calculation.m_factor = OptionField(
        "Moment factor", options=m_factor_options, name="m_factor", default="1/16"
    )
    calculation.temperature = NumberField(
        "Temperatuurverschil", default=30, suffix="°C"
    )
    calculation.displacement = NumberField(
        "Toelaatbare vervorming", suffix="mm", default=50
    )
    calculation.thickness_plate = NumberField("dikte kopplaat", suffix="mm", default=20)
    calculation.hoh = NumberField("h.o.h. afstand:", suffix="m", default=1)
    calculation.excentricity = NumberField(
        "Excentriciteit aansluiting stempel/gording:", suffix="mm", default=30
    )
    calculation.k_value_sheetpile = NumberField(
        "K-waarde damwand:", suffix="kN/m", default=10000
    )

    downloads = Tab("Downloads")
    downloads.laden = Section("Download resultaten")
    downloads.laden.bgt = OptionField("BGT scenario", options=BGT_options)
    downloads.laden.lb = LineBreak()
    downloads.laden.xml = DownloadButton("Download updated XML", "download_updated_xml")
    downloads.laden.download_excel = DownloadButton(
        "Download Excel uitdraai", "download_excel"
    )
    downloads.laden.rtf = DownloadButton("Download RTF export", "download_rtf")

    visualization = Tab("Visualisatie")
    visualization.geometry = Section("Geometrie")
    visualization.geometry.show_labels = ToggleButton(
        "Visualiseer labels", default=True
    )
    visualization.geometry.show_nodes = ToggleButton("Visualiseer knopen", default=True)
    visualization.geometry.show_fixedsupports = ToggleButton(
        "Visualiseer opleggingen", default=True
    )
    visualization.geometry.show_springs = ToggleButton(
        "Visualiseer veren", default=True
    )
