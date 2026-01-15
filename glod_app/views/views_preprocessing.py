from django.shortcuts import render, redirect
from django.contrib import messages
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Create your views here.

def preprocessing_index(request):
    """View untuk halaman preprocessing - menampilkan data yang dipilih dari UniProt"""
    
    # Get data source from query parameter
    source = request.GET.get('source', '')
    
    # Retrieve data from session based on source
    if source == 'search':
        # Data dari hasil pencarian UniProt
        keyword = request.GET.get('q', '')
        data = request.session.get('uniprot_results', [])
        data_source = f"Hasil Pencarian UniProt: {keyword}"
    elif source == 'upload':
        # Data dari file upload
        data = request.session.get('uploaded_gene_data', [])
        filename = request.session.get('uploaded_filename', 'Unknown')
        data_source = f"File Upload: {filename}"
    else:
        # Try to get existing preprocessing data if available
        data = request.session.get('preprocessing_data', [])
        data_source = request.session.get('preprocessing_source', 'Unknown')
        
        if not data:
            # No data available
            messages.error(request, 'Tidak ada data yang dipilih. Silakan pilih data dari halaman Input Data Gen.')
            return redirect('uniprot_input_data_gen')
    
    if not data or not isinstance(data, list) or len(data) == 0:
        messages.error(request, 'Data tidak ditemukan atau format data tidak sesuai. Silakan pilih data terlebih dahulu.')
        return redirect('uniprot_input_data_gen')

    # Debug: Log kolom yang ada di data
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        logger.info(f"Data keys: {list(data[0].keys())}")
    else:
        logger.warning("Format data tidak sesuai, data harus berupa list of dict.")

    # Store original data and source in session for preprocessing
    current_source = request.session.get('preprocessing_source', '')
    if current_source != data_source:
        request.session['preprocessing_original_count'] = len(data)
        request.session['preprocessing_duplicates_removed'] = False
    elif 'preprocessing_original_count' not in request.session:
        request.session['preprocessing_original_count'] = len(data)

    request.session['preprocessing_data'] = data
    request.session['preprocessing_source'] = data_source
    request.session.modified = True  # Force session save

    # Check if duplicates have been removed
    duplicates_removed = request.session.get('preprocessing_duplicates_removed', False)

    # Validasi: pastikan setiap item adalah dict dan punya minimal satu key yang dibutuhkan
    required_keys = {'accession', 'protein_name', 'gene_symbol', 'organism'}
    valid_data = []
    for item in data:
        if isinstance(item, dict) and required_keys.intersection(item.keys()):
            valid_data.append(item)

    if len(valid_data) == 0:
        messages.error(request, 'Format data tidak sesuai. Data harus berupa list of dict dengan key: accession, protein_name, gene_symbol, organism. Silakan pilih atau upload data yang benar dari halaman Input Data Gen.')
        return redirect('uniprot_input_data_gen')

    # Fallback: pastikan preview selalu punya key yang dibutuhkan
    preview_data = []
    for row in valid_data[:5]:
        preview_data.append({
            'accession': row.get('accession', '-'),
            'protein_name': row.get('protein_name', '-'),
            'gene_symbol': row.get('gene_symbol', '-'),
            'organism': row.get('organism', '-')
        })

    context = {
        'data': preview_data,
        'total_count': len(valid_data),
        'original_count': request.session.get('preprocessing_original_count', len(valid_data)),
        'data_source': data_source,
        'duplicates_removed': duplicates_removed,
    }

    # Update session dengan data yang valid saja
    request.session['preprocessing_data'] = valid_data
    # Simpan gene symbol unik ke session dengan nama preprocessing_genes
    gene_symbols = [row.get('gene_symbol') for row in valid_data if row.get('gene_symbol')]
    request.session['preprocessing_genes'] = list(sorted(set(gene_symbols)))
    request.session.modified = True

    return render(request, 'glod_app/preprocessing_index.html', context)


def preprocessing_use_data(request):
    """Redirect view to pass data from UniProt to preprocessing"""
    return preprocessing_index(request)


def preprocessing_remove_duplicates(request):
    """Remove duplicate gene symbols from the data"""
    if request.method != 'POST':
        return redirect('preprocessing_index')
    
    # Get data from session
    data = request.session.get('preprocessing_data', [])
    
    if not data:
        messages.error(request, 'Tidak ada data untuk diproses.')
        return redirect('preprocessing_index')
    
    # Validasi data sebelum proses
    if not isinstance(data, list) or len(data) == 0 or not isinstance(data[0], dict):
        messages.error(request, 'Format data tidak sesuai untuk penghapusan duplikat.')
        return redirect('preprocessing_index')

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Store original count
    original_count = len(df)

    # Remove duplicates based on gene_symbol
    if 'gene_symbol' in df.columns:
        df_unique = df.drop_duplicates(subset=['gene_symbol'], keep='first')
        removed_count = original_count - len(df_unique)
        unique_data = df_unique.to_dict('records')
        
        # Update session dengan data yang sudah difilter
        request.session['preprocessing_data'] = unique_data
        request.session['preprocessing_duplicates_removed'] = True
        
        # PENTING: Update preprocessing_genes dengan data terbaru setelah duplikat dihapus
        gene_symbols = [row.get('gene_symbol') for row in unique_data if row.get('gene_symbol')]
        request.session['preprocessing_genes'] = list(sorted(set(gene_symbols)))
        
        # PENTING: Reset network_genes agar tidak menggunakan data lama
        # Ini memastikan string_app akan menggunakan preprocessing_genes terbaru
        if 'network_genes' in request.session:
            del request.session['network_genes']
        
        request.session.modified = True
        print(f"[DEBUG] remove_duplicates: Updated preprocessing_genes with {len(request.session['preprocessing_genes'])} unique genes")
        messages.success(request, f'Berhasil menghapus {removed_count} data duplikat. Data sekarang: {len(unique_data)} entries.')
    else:
        messages.error(request, 'Kolom gene_symbol tidak ditemukan pada data. Tidak dapat menghapus duplikat.')

    return redirect('preprocessing_index')


def preprocessing_reset_data(request):
    """Reset data to original state before preprocessing"""
    if request.method != 'POST':
        return redirect('preprocessing_index')
    
    # Get original data source to reload the data
    source = request.session.get('preprocessing_source', '')
    
    # Clear preprocessing flags
    request.session['preprocessing_duplicates_removed'] = False
    
    # Determine where to reload data from
    if 'uniprot' in source.lower() or 'pencarian' in source.lower():
        # Reload from uniprot_results
        original_data = request.session.get('uniprot_results', [])
    elif 'upload' in source.lower() or 'file' in source.lower():
        # Reload from uploaded_gene_data
        original_data = request.session.get('uploaded_gene_data', [])
    else:
        messages.error(request, 'Tidak dapat mereset data. Sumber data tidak dikenali.')
        return redirect('preprocessing_index')
    
    if original_data:
        # Reset preprocessing data to original
        request.session['preprocessing_data'] = original_data
        request.session['preprocessing_original_count'] = len(original_data)
        messages.success(request, f'Data berhasil direset ke keadaan semula. Total data: {len(original_data)} entries.')
    else:
        messages.error(request, 'Data asli tidak ditemukan. Silakan muat ulang data dari halaman Input Data Gen.')
    
    return redirect('preprocessing_index')
