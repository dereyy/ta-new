from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import ssl
import requests
import pandas as pd
import time
import re
from django.views.decorators.csrf import csrf_exempt
import logging

# Simple SSL context to avoid verification issues in some environments (optional)
ssl_context = ssl.create_default_context()

logger = logging.getLogger(__name__)


def index(request):
    """Redirect to Input Data Gen page for convenience."""
    return redirect('uniprot_input_data_gen')


def _build_uniprot_query_url(query: str, size: int = 25, format_: str = 'tsv', fields: str | None = None) -> str:
    base = 'https://rest.uniprot.org/uniprotkb/search'
    params = {
        'query': query,
        'format': format_,
        'size': str(size),
    }
    if fields:
        params['fields'] = fields
    return f"{base}?{urlencode(params)}"


def _fetch_uniprot(url: str, email: str | None = None) -> tuple[str, dict]:
    """
    Fetch content from UniProt REST API and return (text, headers).
    Adds a polite User-Agent with email if provided.
    """
    headers = {
        'Accept': 'text/tab-separated-values',
        'User-Agent': f"webta-uniprot/1.0{' (' + email + ')' if email else ''}",
    }
    req = Request(url, headers=headers)
    try:
        with urlopen(req, context=ssl_context) as resp:
            data = resp.read().decode('utf-8', errors='replace')
            return data, dict(resp.headers)
    except HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code}: {e.reason}")
    except URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


# Helper function to fetch the next link from API response using regex
def _get_next_link(headers):
    """Extract next page link from Link header using regex."""
    link = headers.get("Link")
    if not link:
        return None
    # Parse Link header: <url>; rel="next"
    import re
    m = re.match(r'<([^>]+)>;\s*rel="next"', link)
    if m:
        return m.group(1)
    return None


# Helper function to fetch a single page of results
def _fetch_page(query, size, cursor_url, email="contact@example.org"):
    """
    Fetch page from UniProt API.
    Returns: (Response object, next_link)
    """
    headers = {
        "User-Agent": f"webta-uniprot/1.0 (contact: {email})",
        "Accept": "application/json",
    }
    
    if cursor_url:
        # Use cursor URL directly for subsequent pages
        resp = requests.get(cursor_url, headers=headers, timeout=60)
    else:
        # First page: build query with explicit fields
        base_url = "https://rest.uniprot.org/uniprotkb/search"
        params = {
            "query": query,
            "format": "json",
            "size": str(size),
            # Explicitly request all fields we need
            "fields": "accession,id,protein_name,gene_names,gene_primary,organism_name,reviewed",
        }
        resp = requests.get(base_url, params=params, headers=headers, timeout=60)
    
    if resp.status_code != 200:
        raise Exception(f"API error: {resp.status_code} - {resp.text}")
    
    next_link = _get_next_link(resp.headers)
    return resp, next_link


# Helper function to extract protein name
def _extract_protein_name(entry):
    """
    Extract protein name with comprehensive fallback strategies.
    Handles all variations from UniProt API response.
    """
    protein_desc = entry.get("proteinDescription", {})
    
    # Strategy 1: recommendedName
    if "recommendedName" in protein_desc:
        rec_name = protein_desc["recommendedName"]
        if "fullName" in rec_name:
            if isinstance(rec_name["fullName"], dict):
                name = rec_name["fullName"].get("value")
                if name:
                    return name
            elif isinstance(rec_name["fullName"], str):
                return rec_name["fullName"]
        # Also try shortName
        if "shortName" in rec_name:
            if isinstance(rec_name["shortName"], list) and rec_name["shortName"]:
                short = rec_name["shortName"][0]
                if isinstance(short, dict):
                    name = short.get("value")
                    if name:
                        return name
            elif isinstance(rec_name["shortName"], dict):
                name = rec_name["shortName"].get("value")
                if name:
                    return name
    
    # Strategy 2: submittedName
    if "submittedName" in protein_desc and protein_desc["submittedName"]:
        submitted_list = protein_desc["submittedName"] if isinstance(protein_desc["submittedName"], list) else [protein_desc["submittedName"]]
        for submitted in submitted_list:
            if "fullName" in submitted:
                if isinstance(submitted["fullName"], dict):
                    name = submitted["fullName"].get("value")
                    if name:
                        return name
                elif isinstance(submitted["fullName"], str):
                    return submitted["fullName"]
    
    # Strategy 3: alternativeName
    if "alternativeName" in protein_desc and protein_desc["alternativeName"]:
        alt_list = protein_desc["alternativeName"] if isinstance(protein_desc["alternativeName"], list) else [protein_desc["alternativeName"]]
        for alt_name in alt_list:
            if "fullName" in alt_name:
                if isinstance(alt_name["fullName"], dict):
                    name = alt_name["fullName"].get("value")
                    if name:
                        return name
                elif isinstance(alt_name["fullName"], str):
                    return alt_name["fullName"]
    
    # Strategy 4: Direct protein field (some API responses)
    if "protein" in entry:
        if isinstance(entry["protein"], dict) and "recommendedName" in entry["protein"]:
            return entry["protein"]["recommendedName"].get("fullName", {}).get("value")
    
    # Strategy 5: Fall back to uniProtkbId parsing (last resort)
    # Example: "BRMS1_HUMAN" → extract "BRMS1"
    uniprot_id = entry.get("uniProtkbId", "")
    if uniprot_id and "_" in uniprot_id:
        # This is better than nothing for proteins without proper name
        symbol = uniprot_id.split("_")[0]
        return f"Protein {symbol}"
    
    return None


# Helper function to extract gene symbol
def _extract_gene_symbol(entry):
    """
    Extract gene symbol with comprehensive fallback strategies.
    Handles all variations from UniProt API response.
    """
    # Strategy 1: genes array (primary source)
    genes = entry.get("genes", [])
    if genes:
        gene = genes[0]
        
        # Try geneName first (most reliable)
        if "geneName" in gene:
            gene_name = gene["geneName"]
            if isinstance(gene_name, dict):
                name = gene_name.get("value")
                if name:
                    return name
            elif isinstance(gene_name, str):
                return gene_name
        
        # Try synonyms
        if "synonyms" in gene and gene["synonyms"]:
            synonym = gene["synonyms"][0] if isinstance(gene["synonyms"], list) else gene["synonyms"]
            if isinstance(synonym, dict):
                name = synonym.get("value")
                if name:
                    return name
            elif isinstance(synonym, str):
                return synonym
        
        # Try orfNames
        if "orfNames" in gene and gene["orfNames"]:
            orf = gene["orfNames"][0] if isinstance(gene["orfNames"], list) else gene["orfNames"]
            if isinstance(orf, dict):
                name = orf.get("value")
                if name:
                    return name
            elif isinstance(orf, str):
                return orf
        
        # Try orderedLocusNames
        if "orderedLocusNames" in gene and gene["orderedLocusNames"]:
            locus = gene["orderedLocusNames"][0] if isinstance(gene["orderedLocusNames"], list) else gene["orderedLocusNames"]
            if isinstance(locus, dict):
                name = locus.get("value")
                if name:
                    return name
            elif isinstance(locus, str):
                return locus
    
    # Strategy 2: Direct gene field (some API responses)
    if "gene" in entry:
        if isinstance(entry["gene"], dict):
            name = entry["gene"].get("name") or entry["gene"].get("value")
            if name:
                return name
        elif isinstance(entry["gene"], str):
            return entry["gene"]
    
    # Strategy 3: Extract from uniProtkbId
    # Example: "BRMS1_HUMAN" → extract "BRMS1"
    uniprot_id = entry.get("uniProtkbId", "")
    if uniprot_id and "_" in uniprot_id:
        symbol = uniprot_id.split("_")[0]
        # Only return if it looks like a gene symbol (not a fragment or numbered variant)
        if symbol and not symbol.startswith("Q") and not symbol.startswith("P"):
            return symbol
    
    # Strategy 4: Extract from primaryAccession patterns
    # Some entries use patterns like "BRCA1", "TP53" directly
    accession = entry.get("primaryAccession", "")
    # If accession starts with letter and is short, might be gene symbol
    if accession and len(accession) <= 6 and accession[0].isalpha():
        return accession
    
    return None


# Helper function to normalize entries from Response object
def _normalize_entries(resp):
    """
    Normalize entries from requests.Response object.
    Returns list of dicts matching template keys (Accession, ProteinName, etc).
    Handles both nested (proteinDescription) and flat (protein_name) field formats.
    """
    try:
        data = resp.json()
    except Exception:
        return []
    
    normalized = []
    for entry in data.get("results", []):
        # Extract Accession (primary key)
        accession = entry.get("primaryAccession") or entry.get("accession") or ""
        
        # Extract Entry ID
        entry_id = entry.get("uniProtkbId") or entry.get("id") or ""
        
        # Extract Protein Name
        # Strategy 1: Check if API returned flat field (when fields=protein_name)
        protein_name = None
        if "proteinName" in entry:
            protein_name = entry["proteinName"]
        elif "protein_name" in entry:
            protein_name = entry["protein_name"]
        
        # Strategy 2: Parse nested proteinDescription
        if not protein_name:
            protein_name = _extract_protein_name(entry)
        
        # Strategy 3: Fallback to Entry ID without organism suffix
        if not protein_name and entry_id:
            if "_" in entry_id:
                protein_name = entry_id.split("_")[0]
        
        # Extract Gene Symbol
        # Strategy 1: Check flat field first
        gene_symbol = None
        if "genePrimary" in entry:
            gene_symbol = entry["genePrimary"]
        elif "gene_primary" in entry:
            gene_symbol = entry["gene_primary"]
        elif "geneNames" in entry and isinstance(entry["geneNames"], list) and entry["geneNames"]:
            gene_symbol = entry["geneNames"][0]
        elif "gene_names" in entry:
            names = entry["gene_names"]
            if isinstance(names, list) and names:
                gene_symbol = names[0]
            elif isinstance(names, str):
                gene_symbol = names
        
        # Strategy 2: Parse nested genes array
        if not gene_symbol:
            gene_symbol = _extract_gene_symbol(entry)
        
        # Strategy 3: Extract from Entry ID
        if not gene_symbol and entry_id and "_" in entry_id:
            potential_symbol = entry_id.split("_")[0]
            # Only use if it doesn't look like an accession (starts with Q/P followed by digits)
            if not (len(potential_symbol) == 6 and potential_symbol[0] in ['Q', 'P'] and potential_symbol[1:].isdigit()):
                gene_symbol = potential_symbol
        
        # Extract Organism
        # Strategy 1: Flat field
        organism = None
        if "organismName" in entry:
            organism = entry["organismName"]
        elif "organism_name" in entry:
            organism = entry["organism_name"]
        
        # Strategy 2: Nested organism object
        if not organism and "organism" in entry:
            org = entry["organism"]
            if isinstance(org, dict):
                organism = org.get("scientificName") or org.get("commonName") or ""
            elif isinstance(org, str):
                organism = org
        
        # Don't add if critical fields are missing
        if not accession and not entry_id:
            continue
        
        normalized.append({
            "accession": accession or "",
            "entry_id": entry_id or "",
            "protein_name": protein_name or "",
            "gene_symbol": gene_symbol or "",
            "organism": organism or "",
        })
    return normalized


@csrf_exempt
def uniprot_search(request):
    """
    UniProt search - Fetch ALL results in one page (no pagination).
    """
    DEFAULT_PAGE_SIZE = 500
    
    # Ambil parameter dari form (keyword di POST)
    keyword = request.POST.get("keyword", "").strip()
    
    error = None
    results = []
    total_results = 0
    
    if request.method == "POST":
        if not keyword:
            error = "Silakan masukkan kata kunci pencarian."
        else:
            # Build query untuk UniProt API
            query = f"({keyword}) AND organism_id:9606"
            
            try:
                logger.info(f"Searching for: {keyword}")
                
                # Fetch ALL data dengan looping otomatis
                next_cursor = None
                
                while True:
                    # Fetch page
                    resp, next_cursor = _fetch_page(query, DEFAULT_PAGE_SIZE, next_cursor, "contact@example.org")
                    
                    if resp.status_code != 200:
                        error = f"UniProt API error: HTTP {resp.status_code}"
                        break
                    
                    # Normalize dan tambahkan ke results
                    page_results = _normalize_entries(resp)
                    results.extend(page_results)
                    
                    # Ambil total dari header (hanya sekali)
                    if total_results == 0:
                        total_str = resp.headers.get("x-total-results")
                        if total_str:
                            try:
                                total_results = int(total_str)
                            except Exception:
                                pass
                    
                    logger.info(f"Fetched {len(page_results)} results. Total so far: {len(results)}")
                    
                    # Stop jika tidak ada next link
                    if not next_cursor:
                        break
                    
                    # Sleep sebentar untuk menghindari rate limiting
                    time.sleep(0.3)
                
                logger.info(f"Completed! Total fetched: {len(results)} out of {total_results}")
                
                # Simpan hasil ke session untuk download
                request.session['uniprot_results'] = results
                request.session['uniprot_keyword'] = keyword
                request.session.modified = True  # Force session save
                
            except Exception as e:
                logger.error(f"Error fetching data: {str(e)}")
                error = f"Terjadi kesalahan: {str(e)}"
    
    return render(request, "glod_app/uniprot_input_data_gen.html", {
        "results": results,
        "total_results": total_results,
        "error": error,
        "keyword": keyword,
    })


def uniprot_download(request):
    """
    Download data hasil pencarian atau uploaded data dalam format Excel.
    Data diambil dari session untuk efisiensi.
    """
    file_type = request.GET.get("type", "excel")
    keyword = request.GET.get("q", request.session.get("uniprot_keyword", "uniprot"))
    
    # Check if downloading uploaded data or search results
    if keyword == "uploaded_data":
        data = request.session.get("uploaded_gene_data", [])
        filename_base = request.session.get("uploaded_filename", "uploaded_data").replace('.', '_')
    else:
        data = request.session.get("uniprot_results", [])
        filename_base = re.sub(r'[^a-z0-9]+', '_', keyword.lower()).strip('_') or 'uniprot'

    if not data:
        return JsonResponse({"error": "Tidak ada data untuk diunduh. Silakan lakukan pencarian atau upload terlebih dahulu."}, status=400)

    df = pd.DataFrame(data)
    
    if file_type == "excel":
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{filename_base}_results.xlsx"'
        with pd.ExcelWriter(response, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name='Results')
        return response
    else:  # Default to CSV
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename_base}_results.csv"'
        df.to_csv(response, index=False)
        return response


def uniprot_input_data_gen(request):
    """Render the Input Data Gen page."""
    return render(request, 'glod_app/uniprot_input_data_gen.html')


def uniprot_upload(request):
    """
    Handle file upload for manual gene list input.
    Supports Excel, CSV, and TXT formats.
    """
    if request.method != 'POST':
        return redirect('uniprot_input_data_gen')
    
    # Check if file was uploaded
    if 'gene_file' not in request.FILES:
        return render(request, 'glod_app/uniprot_input_data_gen.html', {
            'upload_error': 'Tidak ada file yang diupload. Silakan pilih file terlebih dahulu.'
        })
    
    uploaded_file = request.FILES['gene_file']
    
    # Validate file extension
    filename = uploaded_file.name
    file_ext = filename.split('.')[-1].lower()
    
    if file_ext not in ['csv', 'xlsx', 'xls', 'txt']:
        return render(request, 'glod_app/uniprot_input_data_gen.html', {
            'upload_error': f'Format file tidak didukung: .{file_ext}. Gunakan .csv, .xlsx, .xls, atau .txt'
        })
    
    try:
        # Read file based on extension
        if file_ext in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
        elif file_ext == 'csv':
            df = pd.read_csv(uploaded_file)
        elif file_ext == 'txt':
            # Try to read as tab-separated or comma-separated
            try:
                df = pd.read_csv(uploaded_file, sep='\t')
            except:
                uploaded_file.seek(0)  # Reset file pointer
                df = pd.read_csv(uploaded_file)
        
        # Validate dataframe
        if df.empty:
            return render(request, 'glod_app/uniprot_input_data_gen.html', {
                'upload_error': 'File kosong atau tidak memiliki data yang valid.'
            })
        
        # Get file size in KB
        filesize_kb = uploaded_file.size / 1024
        filesize_str = f"{filesize_kb:.2f} KB" if filesize_kb < 1024 else f"{filesize_kb/1024:.2f} MB"
        
        # Normalize column names (remove leading/trailing spaces, lowercase, replace spaces with underscore)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Standardize common column name variations
        column_mapping = {
            'acc': 'accession',
            'entry': 'accession',
            'protein': 'protein_name',
            'proteinname': 'protein_name',
            'gene': 'gene_symbol',
            'genesymbol': 'gene_symbol',
            'gene_name': 'gene_symbol',
            'organism_name': 'organism',
        }
        
        # Apply column mapping
        df.columns = [column_mapping.get(col, col) for col in df.columns]
        
        # Count valid rows (non-empty rows)
        valid_rows = df.dropna(how='all').shape[0]
        
        # Convert to list of dicts for template
        uploaded_data = df.to_dict('records')
        
        # Store in session
        request.session['uploaded_gene_data'] = uploaded_data
        request.session['uploaded_filename'] = filename
        request.session.modified = True  # Force session save
        
        # Prepare summary
        upload_summary = {
            'filename': filename,
            'filesize': filesize_str,
            'total_rows': len(df),
            'valid_rows': valid_rows,
            'columns': list(df.columns),
        }
        
        return render(request, 'glod_app/uniprot_input_data_gen.html', {
            'upload_success': f'File "{filename}" berhasil diupload!',
            'upload_summary': upload_summary,
            'uploaded_data': uploaded_data,
        })
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return render(request, 'glod_app/uniprot_input_data_gen.html', {
            'upload_error': f'Gagal membaca file: {str(e)}. Pastikan file memiliki format yang benar.'
        })
