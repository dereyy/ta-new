import json
import requests
from typing import Dict, List
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
# from ..session_storage import SessionStorage # Uncomment and adjust import if using SessionStorage

STRING_API_URL = "https://string-db.org/api"

def _safe_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def _consolidate_interactions(interactions: List[Dict]) -> List[Dict]:
    edge_map: Dict[tuple, Dict] = {}
    for it in interactions:
        p1 = it.get('protein1')
        p2 = it.get('protein2')
        if not p1 or not p2:
            continue
        key = tuple(sorted([p1, p2]))
        score = _safe_float(it.get('score', 0))
        existing = edge_map.get(key)
        if existing is None or score > existing['score']:
            edge_map[key] = {'protein1': p1, 'protein2': p2, 'score': score}
    return list(edge_map.values())

def _map_string_id_to_gene(string_id: str, id_to_gene_map: Dict[str, List[str]]) -> str:
    if string_id in id_to_gene_map and id_to_gene_map[string_id]:
        return id_to_gene_map[string_id][0]
    if '.' in string_id:
        parts = string_id.split('.')
        if len(parts) > 1 and parts[1]:
            return parts[1]
    return string_id

def _get_string_ids(gene_names: List[str], species: str = "9606", chunk_size: int = 500, limit: int = 5) -> Dict[str, str]:
    all_string_ids: Dict[str, str] = {}
    request_url = f"{STRING_API_URL}/tsv/get_string_ids"
    params = {
        "identifiers": "\r".join(gene_names),
        "species": species,
        "limit": limit,
        "echo_query": 1
    }
    try:
        response = requests.post(request_url, data=params, timeout=60)
        if response.status_code == 200 and response.text.strip():
            lines = response.text.strip().splitlines()
            for line in lines[1:]:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    query_name = parts[0].strip()
                    string_id = parts[2].strip()
                    if query_name and string_id and query_name not in all_string_ids:
                        all_string_ids[query_name] = string_id
    except Exception as e:
        print(f"Terjadi kesalahan saat mendapatkan ID STRING: {e}")
    return all_string_ids

def _get_protein_interactions(string_ids: List[str], species: str = "9606", required_score: int = 400,
                              chunk_size: int = 500, network_type: str = "full") -> List[Dict]:
    all_interactions: List[Dict] = []
    request_url = f"{STRING_API_URL}/tsv/network"
    params = {
        "identifiers": "\r".join(string_ids),
        "species": species,
        "required_score": required_score,
        "network_type": network_type
    }
    try:
        response = requests.post(request_url, data=params, timeout=120)
        if response.status_code == 200 and response.text.strip():
            lines = response.text.strip().splitlines()
            for line in lines[1:]:
                if not line.strip():
                    continue
                parts = line.split('\t')
                if len(parts) >= 3:
                    p1 = parts[0].strip()
                    p2 = parts[1].strip()
                    score = _safe_float(parts[5])
                    all_interactions.append({'protein1': p1, 'protein2': p2, 'score': score})
    except Exception as e:
        print(f"Terjadi kesalahan saat mendapatkan interaksi: {e}")
    consolidated = _consolidate_interactions(all_interactions)
    return consolidated

@require_http_methods(["GET", "POST"])
def string_network_input(request):
    gene_names: List[str] = []
    
    print(f"\n[DEBUG] string_network_input called with method: {request.method}")
    print(f"[DEBUG] POST data: {dict(request.POST)}")
    print(f"[DEBUG] GET data: {dict(request.GET)}")
    print(f"[DEBUG] Session keys: {list(request.session.keys())}")
    print(f"[DEBUG] preprocessing_genes in session: {len(request.session.get('preprocessing_genes', []))} items")
    
    if request.method == "POST":
        post_data = dict(request.POST)
        print(f"[DEBUG] POST: from_preprocessing={request.POST.get('from_preprocessing')}")
        
        if request.POST.get("from_preprocessing") == "1":
            # ✅ Data dari preprocessing - ambil LANGSUNG dari session
            session_genes = request.session.get('preprocessing_genes', [])
            print(f"[DEBUG] from_preprocessing=1: Taking from preprocessing_genes ({len(session_genes)} genes)")
        elif request.POST.get("build_network") == "1":
            # Prioritas 1: Ambil dari network_genes (jika sudah pernah di-set)
            session_genes = request.session.get('network_genes')
            
            # Prioritas 2: Jika tidak ada, ambil dari preprocessing_genes (data terbaru setelah duplikat dihapus)
            if not session_genes:
                session_genes = request.session.get('preprocessing_genes', [])
                print(f"[DEBUG] build_network=1: network_genes empty, using preprocessing_genes ({len(session_genes)} genes)")
            else:
                print(f"[DEBUG] build_network=1: Using network_genes ({len(session_genes)} genes)")
        else:
            gene_list = request.POST.get("gene_list", "")
            if gene_list:
                session_genes = [g.strip() for g in gene_list.replace('\r', '\n').replace(',', '\n').split('\n') if g.strip()]
            else:
                session_genes = []
        
        if session_genes and isinstance(session_genes, list):
            gene_names = [str(gene).strip() for gene in session_genes if gene and str(gene).strip()]
        
        if gene_names:
            # Update network_genes ke session untuk tracking
            request.session['network_genes'] = gene_names
            request.session.save()
            print(f"[DEBUG] Updated session['network_genes'] with {len(gene_names)} genes")
    else:
        # GET request
        print(f"[DEBUG] GET request processing...")
        
        # ✅ PRIORITAS 1: SELALU ambil dari preprocessing_genes dulu (data terbaru dari session)
        if 'preprocessing_genes' in request.session:
            session_genes = request.session.get('preprocessing_genes', [])
            if session_genes and isinstance(session_genes, list):
                gene_names = [str(gene).strip() for gene in session_genes if gene and str(gene).strip()]
                print(f"[DEBUG] GET: Using preprocessing_genes from session: {len(gene_names)} genes")
        
        # ✅ PRIORITAS 2: Jika tidak ada preprocessing_genes, ambil network_genes
        if not gene_names and 'network_genes' in request.session:
            session_genes = request.session.get('network_genes')
            if session_genes and isinstance(session_genes, list):
                gene_names = [str(gene).strip() for gene in session_genes if gene and str(gene).strip()]
                print(f"[DEBUG] GET: Using network_genes from session: {len(gene_names)} genes")
        
        # ⚠️ PRIORITAS 3 (LAST RESORT): Cek query parameter - HANYA jika tidak ada session data
        if not gene_names:
            genes_param = request.GET.get("genes", "")
            if genes_param:
                gene_names = [g.strip() for g in genes_param.replace('\r', '\n').replace(',', '\n').split('\n') if g.strip()]
                print(f"[DEBUG] GET: Using genes query parameter: {len(gene_names)} genes")
                print(f"[WARNING] Using query parameter instead of session! This might be stale data!")
                
                if gene_names:
                    request.session['network_genes'] = gene_names
                    request.session.save()
    
    if not gene_names:
        session_genes = request.session.get('preprocessing_genes', [])
        session_type = type(session_genes)
        session_len = len(session_genes) if hasattr(session_genes, '__len__') else 'N/A'
        error_msg = f'Tidak ada gene names yang dapat diproses. '
        error_msg += f'Session preprocessing memiliki {session_len} item (type: {session_type.__name__}). '
        if session_genes:
            sample_genes = session_genes[:3] if hasattr(session_genes, '__getitem__') else 'Cannot sample'
            error_msg += f'Sample data: {sample_genes}'
        
        print(f"[ERROR] {error_msg}")
        
        return render(request, 'glod_app/string_input.html', {
            'error': error_msg,
            'debug_info': {
                'session_keys': list(request.session.keys()),
                'has_preprocessing': 'preprocessing_genes' in request.session,
                'preprocessing_count': session_len,
                'preprocessing_type': session_type.__name__,
                'method': request.method,
                'post_data': dict(request.POST) if request.method == 'POST' else None
            }
        })
    
    original_count = len(gene_names)
    if len(gene_names) > 2000:
        gene_names = gene_names[:2000]
    
    estimated_minutes = max(1, int(len(gene_names) * 0.003))
    if len(gene_names) > 1000:
        estimated_minutes = max(5, int(len(gene_names) * 0.005))
    
    selected_confidence = request.POST.get('confidence') or request.GET.get('confidence') or "0.400"
    selected_organism = request.POST.get('organism') or request.GET.get('organism') or "9606"
    
    confidence_map = {
        "0.900": 900,
        "0.700": 700,
        "0.400": 400,
        "0.150": 150,
    }
    required_score = confidence_map.get(selected_confidence, 400)
    
    context = {
        'gene_names': gene_names,
        'total_genes': len(gene_names),
        'original_count': original_count,
        'estimated_minutes': estimated_minutes,
        'network_data': None,
        'error': None,
        'processing_status': None,
        'selected_confidence': selected_confidence,
        'selected_organism': selected_organism,
    }
    
    if request.POST.get('build_network') == '1' or request.GET.get('build') == '1':
        try:
            context['processing_status'] = f'Memproses {len(gene_names)} genes...'
            string_id_mapping = _get_string_ids(gene_names, species=selected_organism, chunk_size=500, limit=5)
            if not string_id_mapping:
                context['error'] = 'Tidak dapat menemukan STRING IDs untuk gene yang diberikan'
                return render(request, 'glod_app/string_input.html', context)
            string_ids = list(string_id_mapping.values())
            interactions = _get_protein_interactions(
                string_ids, species=selected_organism, required_score=required_score, chunk_size=500, network_type="full"
            )
            if not interactions:
                context['error'] = 'Tidak ditemukan interaksi protein untuk gene yang diberikan'
                return render(request, 'glod_app/string_input.html', context)
            nodes = set()
            edges = []
            id_to_gene: Dict[str, List[str]] = {}
            for gene, sid in string_id_mapping.items():
                id_to_gene.setdefault(sid, []).append(gene)
            network_interactions = []
            for interaction in interactions:
                protein1 = interaction['protein1']
                protein2 = interaction['protein2']
                score = interaction.get('score', 0)
                gene1 = _map_string_id_to_gene(protein1, id_to_gene)
                gene2 = _map_string_id_to_gene(protein2, id_to_gene)
                nodes.add(gene1)
                nodes.add(gene2)
                edges.append({
                    'source': gene1,
                    'target': gene2,
                    'score': score
                })
                network_interactions.append({
                    'node1': gene1,
                    'node2': gene2,
                    'score': score,
                    'uploaded_at': datetime.now().isoformat()
                })
            for mapped_gene in string_id_mapping.keys():
                nodes.add(mapped_gene)
            network_data = {
                'nodes': [{'id': node, 'label': node} for node in nodes],
                'edges': edges
            }
            # Uncomment and use storage if needed
            # storage.save_protein_interactions(network_interactions)
            context.update({
                'network_data': json.dumps(network_data),
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'mapped_genes': len(string_id_mapping),
                'processing_status': None
            })
        except Exception as e:
            context['error'] = f'Error building network: {str(e)}'
    
    return render(request, 'glod_app/string_input.html', context)
