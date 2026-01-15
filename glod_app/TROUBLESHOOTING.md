# Troubleshooting Guide - Tombol GLOD

## Masalah yang Diperbaiki

Tombol GLOD tidak mengirim data ke server saat diklik.

## Perubahan yang Dilakukan

### 1. Improved JavaScript Function `processGLOD()`

- ✅ Menambahkan console.log untuk debugging
- ✅ Menambahkan konfirmasi dialog sebelum proses
- ✅ Improved CSRF token detection (mencoba dari input field dan cookie)
- ✅ Menangani error dengan lebih baik
- ✅ Memastikan form ter-submit dengan benar

### 2. Added CSRF Token to Network Visualization

- ✅ Menambahkan `{% csrf_token %}` di card-body visualisasi
- ✅ Token akan tersedia untuk JavaScript

### 3. Enhanced Server-Side Logging

- ✅ Menambahkan print statements di `glod_process` view
- ✅ Logging untuk debugging request POST

## Cara Testing

### 1. Buka Browser Console

- Chrome: F12 atau Ctrl+Shift+I
- Firefox: F12 atau Ctrl+Shift+K
- Edge: F12

### 2. Build Network

1. Buka `/string/input/`
2. Build jaringan protein
3. Tunggu sampai visualisasi selesai

### 3. Test Tombol GLOD

1. Klik tombol **GLOD** (biru)
2. Perhatikan console browser untuk log:
   - "processGLOD called"
   - "Current nodes: X"
   - "Current edges: Y"
   - "Network data prepared: {...}"
   - "CSRF token found: ..."
   - "Submitting form to /glod/process/"

### 4. Periksa Halaman Tujuan

- Seharusnya redirect ke `/glod/process/`
- Menampilkan form input parameter α dan Threshold Jaccard
- Menampilkan jumlah nodes dan edges yang diterima

### 5. Periksa Terminal/Server Logs

Di terminal yang menjalankan Django server, Anda harus melihat:

```
glod_process called with method: POST
Received network_data_json: {"nodes":[...
Parsed network data: X nodes, Y edges
Network data saved to session
```

## Possible Issues & Solutions

### Issue 1: CSRF Token Not Found

**Error**: "CSRF token tidak ditemukan"

**Solution**:

- Pastikan Django session berjalan
- Refresh halaman
- Clear browser cache

### Issue 2: Network Data Empty

**Error**: "Jaringan kosong. Tidak ada data untuk diproses."

**Solution**:

- Pastikan network sudah di-build
- Pastikan ada nodes dan edges di visualisasi
- Jangan hapus semua nodes dengan "Hapus Node Terisolasi"

### Issue 3: Form Not Submitting

**Symptoms**: Tombol diklik tapi tidak ada yang terjadi

**Debug Steps**:

1. Buka console browser
2. Lihat apakah ada error JavaScript
3. Check network tab (F12 > Network)
4. Lihat apakah ada POST request ke `/glod/process/`

**Common Fixes**:

- Refresh halaman
- Clear browser cache
- Check CORS settings
- Verify URL configuration di `urls.py`

### Issue 4: Server Error 500

**Symptoms**: Redirect tapi muncul error page

**Debug Steps**:

1. Lihat terminal Django untuk traceback
2. Check apakah `glod_app` sudah registered di `INSTALLED_APPS`
3. Check URL configuration

**Solution**:

```python
# webta/settings.py
INSTALLED_APPS = [
    ...
    'glod_app',  # Harus ada
    ...
]

# webta/urls.py
urlpatterns = [
    ...
    path('glod/', include('glod_app.urls')),  # Harus ada
    ...
]
```

## Manual Test Flow

### Complete Test Scenario:

1. ✅ Start Django server: `python manage.py runserver`
2. ✅ Open browser: `http://localhost:8000/string/input/`
3. ✅ Build network dengan parameter default
4. ✅ Tunggu network selesai render
5. ✅ (Optional) Hapus node terisolasi
6. ✅ Klik tombol **GLOD**
7. ✅ Dialog konfirmasi muncul → Klik OK
8. ✅ Redirect ke `/glod/process/`
9. ✅ Form parameter muncul dengan data nodes/edges
10. ✅ Isi parameter α dan Threshold
11. ✅ Klik "Jalankan Algoritma GLOD"
12. ✅ Redirect ke `/glod/result/`
13. ✅ Hasil komunitas ditampilkan

## Expected Console Output (Success)

```javascript
processGLOD called
Current nodes: 150
Current edges: 450
Network data prepared: {nodes: Array(150), edges: Array(450)}
CSRF token found: abc123def4...
Submitting form to /glod/process/
```

## Expected Server Log (Success)

```
glod_process called with method: POST
Received network_data_json: {"nodes":[{"id":"TP53","label":"TP53"},...
Parsed network data: 150 nodes, 450 edges
Network data saved to session
[02/Dec/2025 10:30:45] "POST /glod/process/ HTTP/1.1" 200 5432
```

## Quick Fix Commands

Jika masih error, coba:

```bash
# 1. Restart Django server
# Ctrl+C di terminal
python manage.py runserver

# 2. Clear Django cache (jika ada)
python manage.py clear_cache

# 3. Clear browser cache
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete

# 4. Test URL directly
# Buka browser: http://localhost:8000/glod/process/
# Harusnya muncul error "Tidak ada data jaringan" (normal untuk GET request)
```

## Contact & Support

Jika masih ada masalah:

1. Screenshot error console
2. Copy server log dari terminal
3. Jelaskan step yang dilakukan sebelum error
