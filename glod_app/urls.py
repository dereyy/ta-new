from django.urls import path

# Import semua views dari views submodule (yang sudah include GLOD functions)
from .views import (
    # Uniprot views
    index,
    uniprot_search,
    uniprot_download,
    uniprot_input_data_gen,
    uniprot_upload,
    # Preprocessing views
    preprocessing_index,
    preprocessing_use_data,
    preprocessing_remove_duplicates,
    preprocessing_reset_data,
    # String views
    string_network_input,
    # Dashboard views
    dashboard_index,
    # Results views
    results_index,
    # GLOD views
    glod_process,
    glod_result,
    download_community_data,
)

urlpatterns = [
    # Dashboard - Root path
    path('', dashboard_index, name='dashboard_home'),
    
    # UniProt App routes
    path('uniprot/', index, name='uniprot_home'),
    path('uniprot/search/', uniprot_search, name='uniprot_search'),
    path('uniprot/download/', uniprot_download, name='uniprot_download'),
    path('uniprot/input/', uniprot_input_data_gen, name='uniprot_input_data_gen'),
    path('uniprot/upload/', uniprot_upload, name='uniprot_upload'),
    
    # Preprocessing App routes
    path('preprocessing/', preprocessing_index, name='preprocessing_index'),
    path('preprocessing/use-data/', preprocessing_use_data, name='preprocessing_use_data'),
    path('preprocessing/remove-duplicates/', preprocessing_remove_duplicates, name='preprocessing_remove_duplicates'),
    path('preprocessing/reset-data/', preprocessing_reset_data, name='preprocessing_reset_data'),
    
    # String App routes
    path('string/', string_network_input, name='string_network_input'),
    
    # Results App routes
    path('results/', results_index, name='results_home'),
    
    # GLOD App routes
    path('glod/process/', glod_process, name='glod_process'),
    path('glod/result/', glod_result, name='glod_result'),
    path('glod/download/', download_community_data, name='download_community_data'),
]
