import sqlite3

baglanti = sqlite3.connect("taki_magaza.db")
cursor = baglanti.cursor()

# Tabloya kategori sütunu ekleyelim (Eğer daha önce yoksa)
try:
    cursor.execute("ALTER TABLE urunler ADD COLUMN kategori TEXT DEFAULT 'Genel'")
    print("Kategori sütunu başarıyla eklendi!")
except sqlite3.OperationalError:
    print("Kategori sütunu zaten mevcut.")

# Örnek ürünlerimize kategori bilgisi güncelleyelim
cursor.execute(
    "UPDATE urunler SET kategori = 'Kolye' WHERE id = 1"
)  # Altın Kaplama Kolye
cursor.execute(
    "UPDATE urunler SET kategori = 'Yüzük' WHERE id = 2"
)  # Safir Yüzük
cursor.execute(
    "UPDATE urunler SET kategori = 'Küpe' WHERE id = 3"
)  # Halka Küpe

baglanti.commit()
baglanti.close()
print("Ürün kategorileri güncellendi.")