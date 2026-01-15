# Debug Guide - Parameter GLOD

## Cara Memeriksa Apakah Parameter Digunakan

### 1. Lihat Console Server (Terminal)

Saat menjalankan algoritma GLOD, terminal Django akan menampilkan log detail:

```
============================================================
GLOD Algorithm Parameters:
Alpha (α): 0.8
Jaccard Threshold: 0.5
============================================================

Graph created: 150 nodes, 450 edges
GLODAlgorithm initialized with alpha=0.8, jaccard_threshold=0.5
Starting GLOD with 150 nodes and 450 edges
  Expanding seed (size: 5, initial fitness: 0.4523)
    Expansion complete: 5 → 12 nodes, fitness: 0.4523 → 0.6234 (7 iterations)
...

Found 25 communities before merging

Starting merge phase with threshold: 0.5
  Merging C3 and C7 (Jaccard: 0.5234 >= 0.5)
  Merging C12 and C18 (Jaccard: 0.6123 >= 0.5)
Merging complete: 8 merges performed
Communities after merging: 17

Final 17 communities after merging
Parameters used: alpha=0.8, jaccard_threshold=0.5
Calculated modularity: 0.3456
```

### 2. Pengaruh Parameter

#### α (Alpha) - Resolution Parameter

**Nilai α mempengaruhi:**

- Fitness function: `f(C) = k_in / (k_in + k_out)^α`
- Ukuran dan kepadatan komunitas saat ekspansi

**Efek perubahan:**

- **α = 0.5** → Komunitas lebih kecil, lebih padat (fitness lebih sensitif terhadap k_out)
- **α = 0.8** → Balanced (default)
- **α = 1.5** → Komunitas lebih besar, lebih longgar (fitness kurang sensitif terhadap k_out)

**Cara melihat efeknya:**

1. Jalankan dengan α = 0.5
2. Lihat log: "Expansion complete: X → Y nodes"
3. Jalankan dengan α = 1.5
4. Bandingkan: Dengan α lebih tinggi, Y seharusnya lebih besar

**Contoh Log:**

```
α = 0.5:  Expansion complete: 5 → 8 nodes (komunitas kecil)
α = 0.8:  Expansion complete: 5 → 12 nodes (balanced)
α = 1.5:  Expansion complete: 5 → 18 nodes (komunitas besar)
```

#### Threshold Jaccard - Merging Parameter

**Nilai threshold mempengaruhi:**

- Jumlah komunitas yang di-merge
- Jumlah komunitas akhir

**Efek perubahan:**

- **Threshold = 0.2** → Banyak merge → Sedikit komunitas akhir
- **Threshold = 0.33** → Balanced (default)
- **Threshold = 0.6** → Sedikit merge → Banyak komunitas akhir

**Cara melihat efeknya:**

1. Lihat log: "Found X communities before merging"
2. Lihat log: "Merging complete: Y merges performed"
3. Lihat log: "Communities after merging: Z"

**Contoh Log:**

```
Threshold = 0.2:
  Found 25 communities before merging
  Merging complete: 18 merges performed
  Communities after merging: 7

Threshold = 0.5:
  Found 25 communities before merging
  Merging complete: 8 merges performed
  Communities after merging: 17

Threshold = 0.8:
  Found 25 communities before merging
  Merging complete: 2 merges performed
  Communities after merging: 23
```

### 3. Kemungkinan Penyebab Hasil Sama

#### A. Jaringan Terlalu Kecil

Jika jaringan hanya punya ~10-20 nodes, parameter tidak akan memberi efek signifikan.

**Solusi:**

- Gunakan jaringan dengan minimal 50-100 nodes
- Pastikan ada cukup koneksi antar node

#### B. Jaringan Terlalu Homogen

Jika semua node sangat terkoneksi (complete graph atau near-complete), struktur komunitas tidak jelas.

**Solusi:**

- Cek apakah jaringan punya struktur modular
- Lihat visualisasi - ada cluster-cluster terpisah?

#### C. Parameter Tidak Ekstrem

Perubahan kecil (0.8 → 0.85) mungkin tidak terlihat jelas.

**Solusi:**

- Coba perubahan ekstrem:
  - α: 0.3 vs 1.5
  - Threshold: 0.1 vs 0.8

#### D. Cache Browser

Browser mungkin menyimpan hasil lama.

**Solusi:**

- Hard refresh: Ctrl+Shift+R
- Clear cache
- Buka incognito/private window

### 4. Test Case untuk Validasi

#### Test 1: Pengaruh Alpha

```
Data: Jaringan dengan 100+ nodes
α = 0.5, Threshold = 0.33
→ Catat: Jumlah komunitas, ukuran rata-rata

α = 1.5, Threshold = 0.33
→ Bandingkan: Seharusnya komunitas lebih sedikit, ukuran lebih besar
```

#### Test 2: Pengaruh Threshold

```
Data: Jaringan dengan 100+ nodes
α = 0.8, Threshold = 0.2
→ Catat: Jumlah komunitas akhir

α = 0.8, Threshold = 0.7
→ Bandingkan: Seharusnya jumlah komunitas lebih banyak
```

### 5. Debugging Checklist

- [ ] Server log menampilkan parameter yang benar
- [ ] Log "Parameters used" sesuai input
- [ ] "Found X communities before merging" berubah saat α berubah
- [ ] "Merging complete: Y merges" berubah saat threshold berubah
- [ ] Jumlah komunitas akhir berubah
- [ ] Modularity berubah

### 6. Expected Behavior

**Normal:**

```
Input α=0.5, Threshold=0.3
→ Found 30 communities → After merge: 12 communities

Input α=0.5, Threshold=0.6
→ Found 30 communities → After merge: 25 communities (lebih sedikit merge)

Input α=1.2, Threshold=0.3
→ Found 18 communities → After merge: 8 communities (komunitas awal lebih sedikit karena α tinggi)
```

**Abnormal (perlu investigasi):**

```
Input α=0.5, Threshold=0.3
→ Found 25 communities → After merge: 15 communities

Input α=1.5, Threshold=0.3
→ Found 25 communities → After merge: 15 communities (SAMA - ini masalah!)
```

### 7. Quick Debug Commands

Di terminal server, tambahkan print manual di views.py jika perlu:

```python
# Di glod_result view
print(f"RECEIVED PARAMS: alpha={alpha}, threshold={jaccard_threshold}")
print(f"POST DATA: {request.POST}")

# Di GLODAlgorithm.__init__
print(f"GLOD INIT: self.alpha={self.alpha}, self.jaccard_threshold={self.jaccard_threshold}")

# Di fitness_function
print(f"  fitness calc: k_in={k_in}, k_out={k_out}, alpha={self.alpha}, result={result}")

# Di merge_communities
print(f"  checking jaccard={jaccard:.4f} vs threshold={self.jaccard_threshold}")
```

### 8. Verifikasi di Browser

Buka Developer Tools (F12) → Network tab:

1. Submit form parameter GLOD
2. Lihat POST request ke `/glod/result/`
3. Cek Form Data:
   ```
   alpha: 0.8
   jaccard_threshold: 0.5
   csrfmiddlewaretoken: ...
   ```

### 9. Common Issues

**Issue:** Hasil selalu sama
**Check:**

- [ ] POST request berisi parameter yang benar?
- [ ] Server log menampilkan parameter yang benar?
- [ ] Jaringan cukup besar (>50 nodes)?
- [ ] Perubahan parameter cukup signifikan?

**Issue:** Parameter tidak muncul di log
**Check:**

- [ ] Server Django running?
- [ ] Lihat tab terminal yang benar?
- [ ] Log tidak ter-scroll ke atas?

**Issue:** Error "parameter not found"
**Check:**

- [ ] Form field name sesuai: `name="alpha"` dan `name="jaccard_threshold"`?
- [ ] Method POST digunakan?
- [ ] CSRF token valid?
