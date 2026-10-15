import sqlite3


def veritabani_kur():
    # 'taki_magaza.db' adında bir veritabanı dosyası oluşturur
    baglanti = sqlite3.connect("taki_magaza.db")
    cursor = baglanti.cursor()

    # Ürünler tablosunu oluşturuyoruz
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT NOT NULL,
            fiyat REAL NOT NULL,
            aciklama TEXT,
            resim TEXT
        )
    """
    )

    # Örnek birkaç takı verisi ekleyelim (Eğer tablo boşsa)
    cursor.execute("SELECT COUNT(*) FROM urunler")
    if cursor.fetchone()[0] == 0:
        ornek_urunler = [
            (
                "Altın Kaplama Zarif Kolye",
                750.0,
                "925 ayar gümüş üzerine altın kaplama, zirkon taşlı zarif kolye.",
                "kolye.jpg",
            ),
            (
                "Göz Alıcı Safir Yüzük",
                1250.0,
                "Özel tasarım mavi safir detaylı parıltılı lüks yüzük.",
                "yuzuk.jpg",
            ),
            (
                "Minimalist Halka Küpe",
                450.0,
                "Günlük kullanıma uygun, hafif ve şık halka küpe seti.",
                "kupe.jpg",
            ),
        ]
        cursor.executemany(
            "INSERT INTO urunler (ad, fiyat, aciklama, resim) VALUES (?, ?, ?, ?)",
            ornek_urunler,
        )
        baglanti.commit()
        print("Örnek ürünler veritabanına eklendi!")

    baglanti.close()


if __name__ == "__main__":
    veritabani_kur()