from viktor.parametrization import (
    Parametrization,
    Tab,
    Section,
    NumberField,
    LineBreak,
    TextField)
from viktor.parametrization import ToggleButton
from viktor.parametrization import DownloadButton


class ProjectParametrization(Parametrization):

    general = Tab("General")
    general.project = Section("Project")
    general.project.locatie = TextField("Locatie")
    general.project.width = NumberField("Width (W)", suffix="mm", default=10)
    general.project.height = NumberField("Height (H)", suffix="mm", default=10)
    general.project.E = NumberField(
        "Modulus of Elasticity (E)", default=200000, suffix="N/mm2"
    )
