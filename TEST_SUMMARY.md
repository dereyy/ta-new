# RINGKASAN PENGUJIAN SISTEM GLOD COMMUNITY DETECTOR

## Status: ✅ ALL 38 TEST CASES PASSED

---

## TABEL RINGKASAN PENGUJIAN

| No | Skenario Pengujian | Deskripsi | Test Cases | Status |
|----|--------------------|-----------|-----------|--------|
| 1 | Input Data Gen (UniProt & Upload Manual) | Testing UniProt API search, file upload (CSV/XLSX/TXT), dan download hasil | 7 test cases | ✅ PASS (7/7) |
| 2 | Preprocessing Data | Testing display data, remove duplicates, reset data, dan session management | 7 test cases | ✅ PASS (7/7) |
| 3 | STRING DB Network Construction | Testing gene mapping, network building, confidence score, dan error handling | 7 test cases | ✅ PASS (7/7) |
| 4 | GLOD Algorithm Execution | Testing Algorithm 1-3 (seeding, expansion, merging), fitness function, omega, modularity | 8 test cases | ✅ PASS (8/8) |
| 5 | Visualization & Export | Testing result display, image/CSV/JSON export, metrics display | 8 test cases | ✅ PASS (8/8) |
| | **TOTAL** | **Pengujian Komprehensif Seluruh Sistem** | **38 test cases** | **✅ PASS (38/38)** |

---

## DETAIL SKENARIO 1: INPUT DATA GEN (7 TEST CASES)

| No | Fungsi | Kondisi dan Alur Logika | Masukan Data | Hasil yang Diharapkan | Keterangan |
|----|--------|-------------------------|---------|----------------------|------------|
| 1.1 | uniprot_search() | Pencarian keyword penyakit ke API UniProt | keyword='diabetes' | API mengembalikan data dengan kolom Accession, Entry ID, Protein Name, Gene Symbol, Organism | Data ditampilkan dalam tabel |
| 1.2 | uniprot_search() | Input keyword kosong/whitespace | keyword='' atau ' ' | Error: "Silakan masukkan kata kunci pencarian." | Validasi input sebelum API call |
| 1.3 | uniprot_upload() | Upload file CSV/XLSX/TXT dengan data valid | File CSV dengan 2 rows, kolom: accession, gene_symbol, protein_name, organism | File berhasil dibaca, metadata ditampilkan (nama, ukuran, jumlah baris) | Kolom di-normalize dan di-standardisasi |
| 1.4 | uniprot_upload() | Upload file format tidak didukung (.doc, .pdf, .zip) | File format: .doc | Error: "Format file tidak didukung: .doc. Gunakan .csv, .xlsx, .xls, atau .txt" | Validasi extension file |
| 1.5 | uniprot_upload() | Upload file kosong atau terkorupsi | File: 0 bytes atau corrupted | Error: "File kosong atau tidak memiliki data yang valid." | Error handling untuk file invalid |
| 1.6 | uniprot_download() | Download hasil pencarian dalam format Excel/CSV | Data dari session['uniprot_results'] | File .xlsx atau .csv berhasil diunduh dengan nama {keyword}_results.xlsx/csv | Menggunakan pandas ExcelWriter atau to_csv |
| 1.7 | uniprot_download() | Download tanpa ada data di session | session['uniprot_results'] = [] | Error JSON: "Tidak ada data untuk diunduh..." | Validasi data ketersediaan |

---

## DETAIL SKENARIO 2: PREPROCESSING DATA (7 TEST CASES)

| No | Fungsi | Kondisi dan Alur Logika | Masukan Data | Hasil yang Diharapkan | Keterangan |
|----|--------|-------------------------|---------|----------------------|------------|
| 2.1 | preprocessing_index() | Display data dari UniProt search | session['uniprot_results']: 3+ entries | Preview 5 data pertama, total count, original count, duplicates status ditampilkan | Data tervalidasi dengan required keys |
| 2.2 | preprocessing_index() | Display data dari file upload | session['uploaded_gene_data']: 2+ entries, filename='genes.csv' | Source: "File Upload: genes.csv", preview data, total count ditampilkan | Source info berbeda per source |
| 2.3 | preprocessing_remove_duplicates() | Hapus duplikat dengan gene symbol duplikat | Data: 5 entries (INS, HBA1, INS, TP53, HBA1) = 3 duplikat | 3 entry unik (INS, HBA1, TP53) dikembalikan. Message: "Berhasil menghapus 3 data duplikat." | drop_duplicates(subset=['gene_symbol'], keep='first') |
| 2.4 | preprocessing_remove_duplicates() | Data tanpa kolom gene_symbol | Data: accession, protein_name, organism (tanpa gene_symbol) | Error: "Kolom gene_symbol tidak ditemukan pada data." | Validasi kolom sebelum proses |
| 2.5 | preprocessing_remove_duplicates() | Data kosong | session['preprocessing_data'] = [] | Error: "Tidak ada data untuk diproses." | Validasi data sebelum proses |
| 2.6 | preprocessing_reset_data() | Reset setelah penghapusan duplikat | session['preprocessing_duplicates_removed'] = True | Data dikembalikan ke 3 entries original. Message: "Data berhasil direset..." | Reset dari source original |
| 2.7 | session['preprocessing_genes'] | Update dengan unique sorted gene symbols | Data: INS, HBA1, TP53, INS | session['preprocessing_genes'] = ['HBA1', 'INS', 'TP53'] (sorted, unique) | Untuk string_network stage |

---

## DETAIL SKENARIO 3: STRING DB NETWORK CONSTRUCTION (7 TEST CASES)

| No | Fungsi | Kondisi dan Alur Logika | Masukan Data | Hasil yang Diharapkan | Keterangan |
|----|--------|-------------------------|---------|----------------------|------------|
| 3.1 | string_network_input() GET | Display halaman dengan preprocessing data | session['preprocessing_genes']: [INS, HBA1, TP53] | Gene list ditampilkan, confidence dropdown (0.9/0.7/0.4/0.15), tombol "Build Network" | Gene review sebelum network construction |
| 3.2 | string_network_input() POST | Build network dengan confidence score | confidence='0.400', genes=[INS, HBA1, TP53] | Query STRING API, build graph dengan nodes dan edges | Network JSON response dengan total_nodes, total_edges |
| 3.3 | _get_string_ids() | Konversi gene names ke STRING IDs | gene_names=['INS', 'HBA1', 'TP53'], species='9606' | Mapping: {INS: 9606.ENSP00000..., HBA1: 9606.ENSP00000..., TP53: 9606.ENSP00000...} | requests.post() dengan identifier list limit=5 |
| 3.4 | _get_protein_interactions() | Fetch protein interactions dari STRING | string_ids=[3+], required_score=400 | List interactions dengan score >= 400. Contoh: [{'protein1': id1, 'protein2': id2, 'score': 850}] | Consolidate interactions (deduplicate) |
| 3.5 | string_network_input() response | Format network untuk JSON response | Network dengan nodes dan edges | JSON: {nodes: [{id, label}], edges: [{source, target, score}], total_nodes, total_edges} | Format untuk frontend visualization |
| 3.6 | string_network_input() error handling | API STRING error/timeout/no genes found | API error atau Network timeout | Error message: "Error building network: {msg}" atau "Tidak dapat menemukan STRING IDs..." | Exception caught dan handled |
| 3.7 | Confidence score mapping | Mapping confidence ke required_score | confidence: 0.9 / 0.7 / 0.4 / 0.15 | Mapping: 0.9→900, 0.7→700, 0.4→400, 0.15→150 | Pre-defined dalam confidence_map dict |

---

## DETAIL SKENARIO 4: GLOD ALGORITHM EXECUTION (8 TEST CASES)

| No | Fungsi | Kondisi dan Alur Logika | Masukan Data | Hasil yang Diharapkan | Keterangan |
|----|--------|-------------------------|---------|----------------------|------------|
| 4.1 | GLODAlgorithm.__init__() | Inisialisasi dengan graph dan parameter | graph (NetworkX), alpha=0.8, jaccard_threshold=0.33 | Object GLODAlgorithm berhasil dibuat | Parameter tersimpan dalam instance |
| 4.2 | create_rough_seed() (Algorithm 1) | Membuat rough seed dari center node | center_node='A', neighbors dengan CN > 0 | Rough seed = {A, B, C} (center + neighbors dengan CN > 0) | Seeding phase tanpa ekspansi |
| 4.3 | expand_seed() (Algorithm 2) | Ekspansi seed dengan fitness/omega/influence | seed={A,B}, shell nodes={C,D,E} | Community diexpand menjadi {A,B,C,D} | OR logic: fitness_gain>=threshold OR omega>0.8 OR influence>0.8 |
| 4.4 | merge_communities() (Algorithm 3) | Merge overlapping communities dengan Jaccard | communities: [C1={A,B,C}, C2={B,C,D}, C3={E,F}] | Improved Jaccard C1-C2 = 0.5 >= 0.33 → merge | Merge dilakukan iteratif sampai stabil |
| 4.5 | GLODAlgorithm.run() | Eksekusi full GLOD algorithm | NetworkX graph, alpha, jaccard_threshold | Result: communities (List[Set]), modularity metrics | Reproducible dengan seed_value=42 |
| 4.6 | fitness_function() f(C) | Hitung fitness komunitas | k_in=10, k_out=2, alpha=0.8 | f(C) = 10 / (10+2)^0.8 ≈ 1.3698 | Mengukur kepadatan internal vs eksternal |
| 4.7 | omega() function ω(vi) | Hitung neighbor similarity dengan 2-hop | CN_1hop=3, CN_2hop=2, degree=5 | ω(vi) ≈ 0.18 | Kombinasi 1-hop dan 2-hop dengan bobot 0.1 |
| 4.8 | Stability test (small & medium) | Algoritma pada small (3 nodes) dan medium (50 nodes) graph | Graph size: 3 nodes, 50 nodes | Algoritma berjalan tanpa crash, hasil valid | Stress test untuk stabilitas |

---

## DETAIL SKENARIO 5: VISUALIZATION & EXPORT (8 TEST CASES)

| No | Fungsi | Kondisi dan Alur Logika | Masukan Data | Hasil yang Diharapkan | Keterangan |
|----|--------|-------------------------|---------|----------------------|------------|
| 5.1 | glod_process() page display | Display halaman konfigurasi GLOD | session['network_data']: graph JSON | Form alpha (default 0.8) dan jaccard_threshold (default 0.33), network preview | Parameter dapat diatur sebelum eksekusi |
| 5.2 | glod_result() eksekusi | Eksekusi GLOD dengan parameter user | alpha=0.8, jaccard_threshold=0.33 | GLODAlgorithm.run() dijalankan, 2+ communities ditemukan | Modularity metrics dihitung |
| 5.3 | Result graph visualization | Visualisasi graf dengan komunitas | communities: [{A,B,C}, {D,E}, {F}] | Graph ditampilkan dengan nodes berwarna per komunitas (3 komunitas = 3 warna berbeda) | Setiap komunitas = 1 warna unik |
| 5.4 | Normalized Node Cut (NNC) | Hitung NNC = (num_com - 1) / (num_nodes - 1) | num_communities=3, num_nodes=20 | Display: "Normalized Node Cut: 0.1053" (lower is better) | Evaluasi oversegmentation level |
| 5.5 | Download as Image | Download graf sebagai file image | Graph visualization object | File PNG diunduh. Filename: glod_result_{timestamp}.png, size > 0 bytes | Export visualization ke file |
| 5.6 | Download as CSV | Download hasil sebagai CSV | communities result: [{A,B,C}, {D,E}] | CSV dengan kolom: Node, Community ID, Gene Symbol. 3 rows. | Mapping node per community |
| 5.7 | Download as JSON | Download hasil sebagai JSON | communities + modularity metrics | JSON: {communities: [...], metrics: {shen, lazar, nicosia}} | Complete result untuk dokumentasi |
| 5.8 | Display modularity metrics | Tampilkan 3 modularity scores | Shen=0.45, Lazar=0.42, Nicosia=0.47 | Display: "Shen Modularity: 0.4500", "Lazar Modularity: 0.4200", "Nicosia Modularity: 0.4700" | Evaluasi community quality |

---

## KESELURUHAN COVERAGE

### Input/Output
- ✅ UniProt API Integration (search + pagination)
- ✅ File Upload (CSV, XLSX, XLS, TXT)
- ✅ File Download (Excel, CSV, Image, JSON)
- ✅ Data Validation & Normalization
- ✅ Error Handling

### Data Processing
- ✅ Duplicate Removal (by gene_symbol)
- ✅ Session Management
- ✅ Data Transformation (DataFrame ↔ List of Dicts)

### Network Construction
- ✅ STRING DB API Integration
- ✅ Gene-to-STRING ID Mapping
- ✅ Protein Interaction Retrieval
- ✅ Confidence Score Filtering
- ✅ Network Graph Building

### GLOD Algorithm
- ✅ Algorithm 1: Seeding (create_rough_seed)
- ✅ Algorithm 2: Expansion (expand_seed with OR logic)
- ✅ Algorithm 3: Merging (merge_communities with Jaccard)
- ✅ Fitness Function
- ✅ Omega Similarity (2-hop neighbors)
- ✅ Influence Function
- ✅ Modularity Calculation (Shen, Lazar, Nicosia)

### Visualization & Export
- ✅ Graph Visualization with Community Coloring
- ✅ Metrics Display (NNC, Modularity)
- ✅ Export Formats (PNG, CSV, JSON)

---

## CARA MENJALANKAN TEST

### Menggunakan unittest:
```bash
python test_comprehensive.py
```

### Menggunakan pytest:
```bash
pytest test_comprehensive.py -v
```

### Menjalankan test spesifik:
```bash
pytest test_comprehensive.py::TestSkenario1_InputDataGen::test_1_1_uniprot_search_valid_keyword -v
```

---

## HASIL

```
============================== 38 passed in 1.05s ==============================
```

**Status Final: ✅ ALL TESTS PASSED**

File pengujian: `test_comprehensive.py` (1000+ lines, 38 test cases)
Dokumentasi: `TEST_DOCUMENTATION.py` (format tabel lengkap)
