# GLOD App - Global Local Overlapping Community Detection

## Deskripsi

Aplikasi Django untuk deteksi komunitas overlapping pada jaringan protein-protein interaction menggunakan algoritma GLOD.

## Fitur

- ✅ Implementasi lengkap algoritma GLOD dengan 3 fase (Seeding, Expansion, Merging)
- ✅ Input parameter α (alpha) dan Threshold Jaccard yang dapat disesuaikan
- ✅ Visualisasi jaringan dengan pewarnaan komunitas
- ✅ Tabel detail anggota komunitas
- ✅ Metrik Suzuki Modularity untuk overlapping communities
- ✅ Grafik statistik ukuran komunitas
- ✅ Export hasil ke Excel dan PNG

## Cara Penggunaan

### 1. Build Network di String App

- Buka halaman String Network (`/string/input/`)
- Build jaringan protein-protein interaction
- Bersihkan node terisolasi jika diperlukan

### 2. Proses dengan GLOD

- Klik tombol **GLOD** di samping tombol Download PNG
- Anda akan diarahkan ke halaman input parameter GLOD

### 3. Konfigurasi Parameter

#### α (Alpha) - Resolution Parameter

- **Default: 0.8**
- Mengatur kepadatan/ukuran komunitas
- **α < 1**: Komunitas lebih kecil dan lebih padat
- **α = 1**: Balanced
- **α > 1**: Komunitas lebih besar dan lebih longgar

#### Threshold Jaccard - Merging Parameter

- **Default: 0.33 (1/3)**
- Mengatur seberapa banyak overlap yang ditoleransi sebelum komunitas di-merge
- **Nilai tinggi (0.5-1.0)**: Hanya merge komunitas yang sangat mirip → lebih banyak komunitas terpisah
- **Nilai rendah (0.1-0.3)**: Merge komunitas dengan overlap kecil → lebih sedikit komunitas, lebih besar

### 4. Hasil Output

Setelah proses selesai, Anda akan mendapat:

#### Summary Cards

- Jumlah komunitas yang terbentuk
- Nilai Modularity (Suzuki)
- Total nodes dan edges

#### Visualisasi

- Graf jaringan dengan warna komunitas
- Node yang termasuk multiple communities memiliki indikasi di tooltip
- Download visualisasi dalam format PNG

#### Tabel Detail Komunitas

- ID komunitas
- Jumlah anggota per komunitas
- Daftar lengkap anggota (nodes) dalam setiap komunitas

#### Statistik

- Grafik distribusi ukuran komunitas
- Ukuran komunitas terbesar dan terkecil
- Rata-rata ukuran komunitas

## Algoritma GLOD

### Phase 1: Seeding

1. Iterasi pada semua node dalam graf
2. Untuk setiap node, hitung Common Neighbor Similarity (NC) dengan tetangganya
3. Bentuk Rough Seed dengan node pusat + tetangga dengan NC tertinggi
4. Ranking rough seeds menggunakan formula:
   ```
   Score = Σ degree(n) + Count(Nodes) + Count(Internal Edges)
   ```
5. Pilih seed dengan score tertinggi untuk ekspansi

### Phase 2: Expansion

1. Ambil shell nodes (tetangga dari komunitas saat ini)
2. Evaluasi setiap kandidat menggunakan:
   - **Fitness Function**: `f(C) = k_in / (k_in + k_out)^α`
   - **Influence Function**: `F(v, S) = |N(v) ∩ S| / |S|`
3. Tambahkan node yang meningkatkan fitness atau memiliki influence tinggi
4. Ulangi hingga tidak ada node yang dapat ditambahkan

### Phase 3: Merging

1. Bandingkan setiap pasangan komunitas menggunakan Jaccard Coefficient:
   ```
   J(C₁, C₂) = |C₁ ∩ C₂| / |C₁ ∪ C₂|
   ```
2. Jika J ≥ threshold, gabungkan kedua komunitas
3. Ulangi hingga tidak ada lagi komunitas yang dapat digabung

### Modularity (Suzuki)

Algoritma menghitung Suzuki Modularity yang khusus untuk overlapping communities:

- Mempertimbangkan belonging coefficient untuk node yang ada di multiple communities
- Nilai positif menunjukkan struktur komunitas yang baik
- Nilai mendekati 0 atau negatif menunjukkan tidak ada struktur komunitas yang jelas

## Tips Penggunaan

### Untuk Jaringan Protein yang Terkoneksi Padat

- Gunakan **α = 0.7-0.9**
- Threshold Jaccard = 0.33-0.4

### Untuk Komunitas Lebih Granular

- Turunkan **α ke 0.5-0.7**
- Turunkan Threshold ke **0.2-0.3**

### Untuk Mengurangi Overlap

- Tingkatkan **Threshold Jaccard ke 0.4-0.5**
- Ini akan merge lebih banyak komunitas

## Dependencies

- Django
- NetworkX
- vis.js (frontend)
- Chart.js (frontend)
- SheetJS (XLSX export)

## URL Endpoints

- `/glod/process/` - Halaman input parameter dan proses
- `/glod/result/` - Halaman hasil deteksi komunitas

## Struktur File

```
glod_app/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── tests.py
├── urls.py
├── views.py
└── templates/
    └── glod_app/
        ├── process.html    # Halaman input parameter
        └── result.html     # Halaman hasil
```

## Catatan

- Data jaringan disimpan dalam session untuk transfer antar halaman
- Algoritma menggunakan NetworkX untuk manipulasi graf
- Visualisasi menggunakan vis-network untuk rendering interaktif
- Overlapping communities: Satu node bisa termasuk dalam lebih dari satu komunitas
