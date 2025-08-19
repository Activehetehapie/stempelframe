from munch import Munch
from viktor import File

from tests.utils.mock_params import H22_0225_B_Stempelframe2_params
from tests.utils.utils import MockEntity

Mock_XMLuploadEntity = MockEntity(
    entity_id=3386,
    name='H22.0225-B Stempelframe(2).xml',
    params=H22_0225_B_Stempelframe2_params,
    entity_document=File.from_path('tests/documents/H22.0225-B Stempelframe(2).xml')
)
