from viktor.core import ViktorController
from viktor.views import Summary


class ProjectFolderController(ViktorController):
    
    viktor_enforce_field_constraints = True
    
    label = "Project folder"
    summary = Summary()
    children = ["Project"]
    show_children_as = "Table"
