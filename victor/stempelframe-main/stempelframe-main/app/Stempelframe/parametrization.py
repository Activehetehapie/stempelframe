from viktor.parametrization import (
    Parametrization,
    Tab,
    Section,
    NumberField,
    OptionListElement,
    AutocompleteField,
    DynamicArray)


zijde_options = [
    OptionListElement("Neg. zijde"),
    OptionListElement("Pos. zijde"),
]


class StempelframeParametrization(Parametrization):
    general = Tab("Invoer parameters")
    general.node = Section("Hoeken stempelframe")
    general.node.frame = DynamicArray("Coördinaten hoeken")
    general.node.frame.knoop_nr = NumberField("Nr", default="NumberField + 1")
    general.node.frame.knoop_x = NumberField("X", suffix="m")
    general.node.frame.knoop_y = NumberField("Y", suffix="m")

    general.bedding = Section("Damwandkrachten en bedding")
    general.bedding.frame = DynamicArray("Damwandkrachten en bedding")
    general.bedding.frame.bedding_kracht = NumberField("Bedding", suffix="kN/m3")
    general.bedding.frame.bedding_breedte = NumberField(
        "Breedte", suffix="mm", default=1000
    )
    general.bedding.frame.zijde = AutocompleteField(
        "Zijde", options=zijde_options, default="Neg. zijde"
    )
