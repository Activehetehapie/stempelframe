from pathlib import Path


from viktor.views import GeometryView
from viktor.views import GeometryResult
from viktor.geometry import Point
from viktor.geometry import CartesianAxes
from viktor.geometry import SquareBeam
from viktor.geometry import Group
from viktor.core import ViktorController
from viktor.views import Summary
from viktor.views import DataResult
from viktor.views import DataGroup
from viktor.views import DataView
from viktor.views import DataItem
from viktor.views import ImageView
from viktor.views import ImageResult
from viktor.external.spreadsheet import SpreadsheetCalculationInput
from viktor.external.spreadsheet import SpreadsheetCalculation
from viktor.result import DownloadResult

from .parametrization import ProjectParametrization


class ProjectController(ViktorController):
    
    viktor_enforce_field_constraints = True
    
    label = "Project"
    children = ["XMLupload", "Stempelframe"]
    show_children_as = "Table"

    parametrization = ProjectParametrization
    summary = Summary()
