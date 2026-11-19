# Mini Image Processing Toolkit

Aplikasi desktop berbasis Python untuk membuka gambar atau kamera, menerapkan operasi pengolahan citra, melihat histogram secara langsung, dan menyimpan hasilnya.

## 1. Instalasi library

Pastikan Python sudah terpasang. Buka PowerShell di folder proyek, lalu (opsional, tetapi disarankan) buat dan aktifkan virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Pasang semua library yang tercantum di `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

Isi dependensi proyek:

| Paket yang dipasang | Digunakan untuk |
|---|---|
| `opencv-python` | Membaca, memproses, menampilkan, dan menyimpan gambar serta mengambil video dari kamera (`cv2`) |
| `numpy` | Operasi numerik pada piksel dan array gambar |
| `Pillow` | Menampilkan gambar pada antarmuka Tkinter (`PIL`) |
| `matplotlib` | Menggambar histogram di dalam jendela aplikasi |

`tkinter` juga digunakan untuk antarmuka. Biasanya sudah disertakan pada instalasi Python Windows dan tidak perlu dipasang melalui `pip`. Jika aplikasi gagal saat membuat jendela Tkinter, gunakan instalasi Python yang menyertakan Tcl/Tk.

## 2. Menjalankan aplikasi

Di PowerShell yang masih berada di folder proyek, jalankan:

```powershell
python mini_image_processing.py
```

Jalankan aplikasi menggunakan interpreter yang sama dengan interpreter yang digunakan untuk memasang dependensi. Di VS Code, interpreter dapat dipilih melalui **Python: Select Interpreter**.

## 3. Cara menggunakan

1. Klik **Open Image** dan pilih gambar JPG, JPEG, atau PNG; atau klik **Start Camera** untuk memakai kamera default komputer.
2. Klik salah satu tombol operasi untuk memproses gambar/frame. Hasilnya terlihat pada panel **Processed Image**.
3. Histogram RGB berada di panel kanan dan diperbarui otomatis. Histogram menunjukkan gambar hasil pemrosesan; untuk gambar grayscale, ketiga kurva menampilkan histogram intensitas yang sama.
4. Klik **Reset** untuk mengembalikan gambar/frame ke kondisi asli dan menonaktifkan operasi pemrosesan saat ini.
5. Klik **Save Image** untuk menyimpan hasil saat ini ke PNG atau JPEG. Saat kamera aktif, yang disimpan adalah frame yang sedang tampil.
6. Klik **Stop Camera** untuk menghentikan kamera. Kamera juga dilepas saat aplikasi ditutup atau gambar baru berhasil dibuka.

Jika kamera tidak bisa dibuka, periksa izin kamera untuk aplikasi desktop, tutup aplikasi lain yang sedang menggunakan kamera, lalu coba lagi.

## 4. Fitur dan dasar pengolahannya

Semua operasi memproses salinan dari gambar/frame asli, bukan menumpuk perubahan pada hasil sebelumnya. Pengecualian alur antarmuka adalah kamera: operasi yang dipilih diterapkan pada setiap frame baru sampai memilih operasi lain atau menekan **Reset**.

### Grayscale

Mengubah gambar BGR menjadi intensitas abu-abu. OpenCV menggunakan pembobotan kanal warna:

```text
Y = 0.114 B + 0.587 G + 0.299 R
```

**Kegunaan:** menyederhanakan gambar untuk analisis intensitas, threshold, atau deteksi tepi.

### Blur

Menghaluskan gambar menggunakan Gaussian blur dengan kernel 15 × 15. Secara umum, setiap piksel hasil merupakan rata-rata berbobot piksel di sekitarnya:

```text
G(x, y) = ΣΣ K(i, j) · I(x - i, y - j)
```

`I` adalah gambar masukan dan `K` adalah kernel Gaussian yang memberi bobot lebih besar pada piksel dekat pusat.

**Kegunaan:** mengurangi noise atau detail kecil sebelum analisis. Blur juga dapat membuat tepi terlihat kurang tajam.

### Threshold

Gambar diubah ke grayscale, lalu setiap piksel dibandingkan dengan ambang 128:

```text
T(x, y) = 255, jika Y(x, y) > 128
          0,   jika Y(x, y) ≤ 128
```

**Kegunaan:** membuat mask atau pemisahan sederhana antara area terang dan gelap.

### Edge Detection

Menerapkan algoritma Canny pada gambar grayscale dengan ambang 100 dan 200. Canny mencari perubahan intensitas/gradien, menipiskan respons tepi, lalu menghubungkan tepi dengan hysteresis thresholding.

**Kegunaan:** menonjolkan batas objek dan kontur. Hasilnya sensitif terhadap noise dan pemilihan ambang.

### Brightness

Menambahkan nilai `a` yang dimasukkan pengguna ke setiap kanal, lalu membatasi nilai ke rentang 0–255:

```text
I'(x, y) = clip(I(x, y) + a, 0, 255)
```

Nilai `a` negatif menggelapkan gambar; nilai positif mencerahkannya.

### Negative

Membalik intensitas setiap kanal:

```text
I'(x, y) = 255 - I(x, y)
```

**Kegunaan:** membuat efek negatif/inversi warna atau menonjolkan informasi yang kurang terlihat pada citra asli.

### Sharpening

Mempertajam detail dengan konvolusi kernel berikut:

```text
 0  -1   0
-1   5  -1
 0  -1   0
```

Secara intuitif, nilai pusat diperkuat dan tetangga dikurangi. **Kegunaan:** menonjolkan detail/tepi; noise juga dapat ikut terlihat lebih kuat.

### Mirror Horizontal dan Mirror Vertical

- **Mirror Horizontal** membalik susunan kolom piksel kiri ke kanan.
- **Mirror Vertical** membalik susunan baris piksel atas ke bawah.

**Kegunaan:** membuat refleksi gambar atau mengoreksi arah gambar.

### Sketch

Membuat efek seperti sketsa pensil melalui grayscale, inversi, Gaussian blur pada citra invers, lalu color dodge:

```text
invers(x, y) = 255 - Y(x, y)
sketsa(x, y) = clip(Y(x, y) × 255 / max(255 - blur(invers)(x, y), 1), 0, 255)
```

**Kegunaan:** menghasilkan efek visual sketsa. Ini adalah efek artistik, bukan metode untuk menggambar kontur secara akurat.

### Histogram RGB otomatis

Untuk masing-masing kanal merah, hijau, dan biru, histogram menghitung jumlah piksel dengan intensitas `k`:

```text
h_c(k) = jumlah piksel pada kanal c yang memiliki intensitas k
         untuk k = 0, 1, ..., 255
```

Sumbu horizontal menunjukkan intensitas; sumbu vertikal menunjukkan jumlah piksel. Grafik diperbarui setelah gambar dibuka, operasi diterapkan, kamera menghasilkan frame, atau gambar di-reset.

**Kegunaan:** mengamati sebaran intensitas dan kanal warna. Histogram tidak menunjukkan lokasi spasial piksel di dalam gambar.

### Histogram Equalization

Mengubah gambar ke ruang warna YCrCb, meratakan histogram kanal luminans `Y` menggunakan distribusi kumulatif, lalu mengubahnya kembali ke BGR. Secara umum, transformasinya:

```text
s(k) = round((L - 1) × CDF(k))
```

`CDF(k)` adalah distribusi kumulatif intensitas sampai `k`, dan `L = 256` untuk citra 8-bit. Kanal warna `Cr` dan `Cb` tidak disamakan.

**Kegunaan:** meningkatkan kontras luminans, terutama ketika intensitas gambar terkumpul pada rentang yang sempit. Hasil warna dapat berubah jika dibandingkan dengan gambar asli.

## 5. Struktur proyek

```text
projek citra/
├── mini_image_processing.py   # Aplikasi desktop dan logika pengolahan gambar
├── requirements.txt           # Daftar dependensi Python
└── README.md                  # Panduan instalasi dan penggunaan
```

