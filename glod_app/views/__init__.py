# Import all views dari submodules
from .views_uniprot import (
    index,
    uniprot_search,
    uniprot_download,
    uniprot_input_data_gen,
    uniprot_upload,
)

from .views_preprocessing import (
    preprocessing_index,
    preprocessing_use_data,
    preprocessing_remove_duplicates,
    preprocessing_reset_data,
)

from .views_string import (
    string_network_input,
)

from .views_dashboard import (
    dashboard_index,
)

from .views_results import (
    results_index,
)

# Import GLOD views dari parent glod_app/views.py module
# We need to import directly from the original views.py file
import os
import importlib.util

# Get path to original views.py file
_views_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'views.py')

# Load the original views module
_spec = importlib.util.spec_from_file_location("_glod_original_views", _views_file_path)
_glod_original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_glod_original)

# Re-export GLOD functions
glod_process = _glod_original.glod_process
glod_result = _glod_original.glod_result
download_community_data = _glod_original.download_community_data
GLODAlgorithm = _glod_original.GLODAlgorithm

__all__ = [
    # Uniprot
    'index',
    'uniprot_search',
    'uniprot_download',
    'uniprot_input_data_gen',
    'uniprot_upload',
    # Preprocessing
    'preprocessing_index',
    'preprocessing_use_data',
    'preprocessing_remove_duplicates',
    'preprocessing_reset_data',
    # String
    'string_network_input',
    # Dashboard
    'dashboard_index',
    # Results
    'results_index',
    # GLOD
    'glod_process',
    'glod_result',
    'download_community_data',
    'GLODAlgorithm',
]
