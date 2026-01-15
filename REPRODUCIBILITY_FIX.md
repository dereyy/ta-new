# 🔧 Perbaikan: Konsistensi Hasil GLOD Algorithm

## 🎯 Masalah
Hasil algoritma GLOD menghasilkan jumlah komunitas yang berbeda-beda setiap kali dijalankan dengan parameter yang sama:
- Hari ini: 16 komunitas
- Besok: 15 komunitas  
- Sehari lagi: 17 komunitas

## 🔍 Root Cause Analysis

Ada **5 sumber non-determinisme** dalam kode original:

### 1. **`max()` tanpa Tie-breaking** (PALING PENTING)
```python
# ❌ BEFORE - Ketika ada banyak node dengan derajat sama, hasil berbeda
best_center = max(NL, key=lambda node: self.graph.degree(node))
```

```python
# ✅ AFTER - Tie-breaking dengan node ID terkecil untuk konsistensi
best_center = min(
    NL, 
    key=lambda node: (-self.graph.degree(node), node)  
)
```

**Alasan:** Ketika banyak node memiliki derajat yang sama, built-in `max()` memilih node yang tidak konsisten setiap kali dijalankan.

---

### 2. **Urutan Sorting Tidak Konsisten di `create_rough_seed()`**
```python
# ❌ BEFORE
nc_scores.sort(key=lambda x: x[1], reverse=True)

# ✅ AFTER - Tambahkan node ID sebagai secondary sort key
nc_scores.sort(key=lambda x: (-x[1], x[0]))
```

---

### 3. **Iterasi Unordered Set di `expand_seed()`**
```python
# ❌ BEFORE - Set tidak memiliki urutan garantit
for candidate in shell_nodes:
    candidate_scores[candidate] = {...}

# ✅ AFTER - Convert ke sorted list untuk urutan konsisten
for candidate in sorted(shell_nodes):
    candidate_scores[candidate] = {...}
```

---

### 4. **Argmax Selection dengan Ties**
```python
# ❌ BEFORE
argmax_nodes = {
    best_by_fitness[0],
    best_by_omega[0],
    best_by_influence[0]
}

# ✅ AFTER - Sort untuk konsistensi iterasi
argmax_nodes_set = {
    best_by_fitness[0],
    best_by_omega[0],
    best_by_influence[0]
}
argmax_nodes = sorted(argmax_nodes_set)
```

---

### 5. **Random Seed dalam NMI Calculation**
```python
# ❌ BEFORE - Tidak ada seed
random_nmis = []
nodes_list = list(self.graph.nodes())

# ✅ AFTER - Set seed untuk konsistensi
random.seed(seed_value)
random_nmis = []
nodes_list = sorted(list(self.graph.nodes()))
```

---

## ✅ Perbaikan yang Dilakukan

### **1. Method Signature Update**
```python
def run(self, seed_value: int = 42) -> Tuple[List[Set], float, float, float]:
    """
    ...
    Args:
        seed_value: Random seed untuk reproducible results (default: 42)
    """
    import random
    random.seed(seed_value)
    
    print(f"Random seed set to {seed_value} for reproducible results")
```

### **2. NMI Metrics Signature Update**
```python
def calculate_onmi_metrics(
    self, 
    detected_comms: List[Set], 
    ground_truth_comms: List[Set], 
    seed_value: int = 42
) -> Dict[str, float]:
    import random
    random.seed(seed_value)
    ...
```

### **3. View Handler Update**
```python
# Dalam glod_result() function
communities, shen_mod, lazar_mod, nicosia_mod = glod.run(seed_value=42)

# Dan saat hitung NMI metrics
nmi_results = glod.calculate_onmi_metrics(
    communities, 
    ground_truth_comms, 
    seed_value=42
)
```

---

## 🧪 Testing

Untuk memverifikasi perbaikan:

1. **Test Reproducibility** - Jalankan 3x dengan parameter yang sama:
   ```python
   alpha = 0.7
   jaccard_threshold = 0.25
   
   # Run 1
   # Run 2
   # Run 3
   
   # Seharusnya hasil komunitas PERSIS SAMA
   ```

2. **Expected Result:**
   ```
   Run 1: 16 komunitas (misalnya)
   Run 2: 16 komunitas ✅
   Run 3: 16 komunitas ✅
   ```

---

## 📊 Penjelasan Teknis

### Mengapa ini terjadi?

Python 3.6+ menjaga insertion order untuk dict, tetapi **SET tidak pernah menjamin urutan**:

```python
# ❌ Set bisa berbeda urutan tiap kali
s = {3, 1, 2}
for x in s:
    print(x)  # Bisa 3,1,2 atau 1,2,3 atau kombinasi lainnya

# ✅ Sorted list selalu sama
for x in sorted(s):
    print(x)  # SELALU 1,2,3
```

Begitu juga dengan `max()` / `min()` ketika ada **ties** (nilai yang sama):
- `max([1,2,2,1])` bisa return index 1 atau 2 tergantung kondisi internal Python
- Solution: Gunakan tuple `(value, secondary_key)` untuk deterministic ordering

---

## 🎯 Key Takeaway

**Kesimpulannya:** Random seed sendirian tidak cukup. Kita juga perlu:
1. ✅ Set random seed (`random.seed()`)
2. ✅ Deterministic node selection dengan tie-breaking
3. ✅ Sorted iterasi untuk set dan max/min operations  
4. ✅ Sorted nodes lists

---

## 📝 Catatan Perubahan

| Aspek | Before | After |
|-------|--------|-------|
| Node selection | `max()` tanpa tie-break | `min()` dengan tuple key |
| Set iteration | Unordered | `sorted()` |
| Random seed | ❌ Tidak ada | ✅ `seed_value=42` |
| Reproducibility | ❌ Non-deterministic | ✅ 100% Deterministic |

---

## 🚀 Cara Menggunakan

Tidak perlu perubahan dari sisi user interface. Algoritma sekarang otomatis:
- Menggunakan seed = 42 sebagai default
- Menghasilkan hasil yang **selalu identik** untuk parameter yang sama

Jika user ingin menggunakan seed berbeda untuk testing:
```python
# Di views.py, ubah angka seed jika perlu
glod.run(seed_value=42)  # Ubah 42 ke seed lain jika diperlukan
```
