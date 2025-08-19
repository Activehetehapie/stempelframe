from .Project.controller import ProjectController as Project
from .Stempelframe.controller import StempelframeController as Stempelframe
from .XMLupload.controller import XMLuploadController as XMLupload
from .project_folder.controller import ProjectFolderController as ProjectFolder

from viktor import InitialEntity

initial_entities = [
    InitialEntity('ProjectFolder', name='Projecten', children=[
        InitialEntity('Project', name='Testproject', children=[
            InitialEntity('Stempelframe', name='Stempelframe')
        ])
    ])
]
