import os
import sqlite3
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "gizli_anahtar_kelime"

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ADMIN_SIFRE = "12345a"


def dosya_uzantisi_uygun_mu(dosya_adi):
    return (
        "." in dosya_adi
        and dosya_adi.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def urunleri_getir(kategori=None, arama=None, siralama=None):
    baglanti = sqlite3.connect("taki_magaza.db")
    baglanti.row_factory = sqlite3.Row
    cursor = baglanti.cursor()

    sorgu = "SELECT * FROM urunler WHERE 1=1"
    parametreler = []

    if kategori and kategori != "Tümü":
        sorgu += " AND kategori = ?"
        parametreler.append(kategori)

    if arama:
        sorgu += " AND (ad LIKE ? OR aciklama LIKE ?)"
        parametreler.append(f"%{arama}%")
        parametreler.append(f"%{arama}%")

    if siralama == "artan":
        sorgu += " ORDER BY fiyat ASC"
    elif siralama == "azalan":
        sorgu += " ORDER BY fiyat DESC"
    elif siralama == "yeni":
        sorgu += " ORDER BY id DESC"

    cursor.execute(sorgu, parametreler)
    urunler = cursor.fetchall()
    baglanti.close()
    return urunler


@app.route("/")
def ana_sayfa():
    baglanti = sqlite3.connect("taki_magaza.db")
    baglanti.row_factory = sqlite3.Row
    cursor = baglanti.cursor()
    cursor.execute("SELECT * FROM urunler LIMIT 3")
    one_cikanlar = cursor.fetchall()
    baglanti.close()

    sepet = session.get("sepet", [])
    return render_template(
        "index.html", urunler=one_cikanlar, toplam_urun=len(sepet)
    )


@app.route("/urunler")
def urunler_sayfasi():
    secilen_kategori = request.args.get("kategori", "Tümü")
    arama_metni = request.args.get("q", "")
    siralama_turu = request.args.get("sirala", "yeni")

    liste = urunleri_getir(
        kategori=secilen_kategori, arama=arama_metni, siralama=siralama_turu
    )

    baglanti = sqlite3.connect("taki_magaza.db")
    cursor = baglanti.cursor()
    cursor.execute("SELECT DISTINCT kategori FROM urunler")
    kategoriler = [row[0] for row in cursor.fetchall() if row[0]]
    baglanti.close()

    sepet = session.get("sepet", [])
    return render_template(
        "urunler.html",
        urunler=liste,
        kategoriler=kategoriler,
        secilen_kategori=secilen_kategori,
        arama_metni=arama_metni,
        siralama_turu=siralama_turu,
        toplam_urun=len(sepet),
    )


@app.route("/urun/<int:urun_id>")
def urun_detay(urun_id):
    baglanti = sqlite3.connect("taki_magaza.db")
    baglanti.row_factory = sqlite3.Row
    cursor = baglanti.cursor()
    cursor.execute("SELECT * FROM urunler WHERE id = ?", (urun_id,))
    urun = cursor.fetchone()
    baglanti.close()

    if not urun:
        return redirect(url_for("urunler_sayfasi"))

    sepet = session.get("sepet", [])
    return render_template("urun_detay.html", urun=urun, toplam_urun=len(sepet))


@app.route("/hakkimizda")
def hakkimizda():
    sepet = session.get("sepet", [])
    return render_template("hakkimizda.html", toplam_urun=len(sepet))


@app.route("/iletisim")
def iletisim():
    sepet = session.get("sepet", [])
    return render_template("iletisim.html", toplam_urun=len(sepet))


@app.route("/yonetici-giris", methods=["GET", "POST"])
def yonetici_giris():
    hata = None
    if request.method == "POST":
        girilen_sifre = request.form.get("sifre")
        if girilen_sifre == ADMIN_SIFRE:
            session["admin_giris"] = True
            return redirect(url_for("admin_paneli"))
        else:
            hata = "Hatalı şifre! Lütfen tekrar deneyin."

    sepet = session.get("sepet", [])
    return render_template("admin_giris.html", hata=hata, toplam_urun=len(sepet))


@app.route("/admin-cikis")
def admin_cikis():
    session.pop("admin_giris", None)
    return redirect(url_for("yonetici_giris"))


@app.route("/admin")
def admin_paneli():
    if not session.get("admin_giris"):
        return redirect(url_for("yonetici_giris"))

    baglanti = sqlite3.connect("taki_magaza.db")
    baglanti.row_factory = sqlite3.Row
    cursor = baglanti.cursor()
    cursor.execute("SELECT * FROM urunler")
    urunler = cursor.fetchall()
    baglanti.close()

    sepet = session.get("sepet", [])
    return render_template("admin.html", urunler=urunler, toplam_urun=len(sepet))


@app.route("/admin/urun-ekle", methods=["POST"])
def admin_urun_ekle():
    if not session.get("admin_giris"):
        return redirect(url_for("yonetici_giris"))

    ad = request.form.get("ad")
    fiyat = request.form.get("fiyat")
    aciklama = request.form.get("aciklama")
    kategori = request.form.get("kategori")
    dosya = request.files.get("resim")

    resim_adi = "varsayilan.jpg"
    if dosya and dosya.filename != "" and dosya_uzantisi_uygun_mu(dosya.filename):
        guvenli_isim = secure_filename(dosya.filename)
        dosya.save(os.path.join(app.config["UPLOAD_FOLDER"], guvenli_isim))
        resim_adi = guvenli_isim

    if ad and fiyat and kategori:
        baglanti = sqlite3.connect("taki_magaza.db")
        cursor = baglanti.cursor()
        try:
            cursor.execute(
                "INSERT INTO urunler (ad, fiyat, aciklama, kategori, resim) VALUES (?, ?, ?, ?, ?)",
                (ad, float(fiyat), aciklama, kategori, resim_adi),
            )
        except sqlite3.OperationalError:
            cursor.execute(
                "INSERT INTO urunler (ad, fiyat, aciklama, kategori) VALUES (?, ?, ?, ?)",
                (ad, float(fiyat), aciklama, kategori),
            )
        baglanti.commit()
        baglanti.close()

    return redirect(url_for("admin_paneli"))


@app.route("/admin/urun-sil/<int:urun_id>")
def admin_urun_sil(urun_id):
    if not session.get("admin_giris"):
        return redirect(url_for("yonetici_giris"))

    baglanti = sqlite3.connect("taki_magaza.db")
    cursor = baglanti.cursor()
    cursor.execute("DELETE FROM urunler WHERE id = ?", (urun_id,))
    baglanti.commit()
    baglanti.close()

    return redirect(url_for("admin_paneli"))


@app.route("/admin/urun-duzenle/<int:urun_id>", methods=["GET", "POST"])
def admin_urun_duzenle(urun_id):
    if not session.get("admin_giris"):
        return redirect(url_for("yonetici_giris"))

    baglanti = sqlite3.connect("taki_magaza.db")
    baglanti.row_factory = sqlite3.Row
    cursor = baglanti.cursor()

    if request.method == "POST":
        ad = request.form.get("ad")
        fiyat = request.form.get("fiyat")
        aciklama = request.form.get("aciklama")
        kategori = request.form.get("kategori")
        dosya = request.files.get("resim")

        if (
            dosya
            and dosya.filename != ""
            and dosya_uzantisi_uygun_mu(dosya.filename)
        ):
            guvenli_isim = secure_filename(dosya.filename)
            dosya.save(os.path.join(app.config["UPLOAD_FOLDER"], guvenli_isim))

            try:
                cursor.execute(
                    "UPDATE urunler SET ad = ?, fiyat = ?, aciklama = ?, kategori = ?, resim = ? WHERE id = ?",
                    (ad, float(fiyat), aciklama, kategori, guvenli_isim, urun_id),
                )
            except sqlite3.OperationalError:
                cursor.execute(
                    "UPDATE urunler SET ad = ?, fiyat = ?, aciklama = ?, kategori = ? WHERE id = ?",
                    (ad, float(fiyat), aciklama, kategori, urun_id),
                )
        else:
            cursor.execute(
                "UPDATE urunler SET ad = ?, fiyat = ?, aciklama = ?, kategori = ? WHERE id = ?",
                (ad, float(fiyat), aciklama, kategori, urun_id),
            )

        baglanti.commit()
        baglanti.close()
        return redirect(url_for("admin_paneli"))

    cursor.execute("SELECT * FROM urunler WHERE id = ?", (urun_id,))
    urun = cursor.fetchone()
    baglanti.close()

    sepet = session.get("sepet", [])
    return render_template(
        "admin_duzenle.html", urun=urun, toplam_urun=len(sepet)
    )


@app.route("/sepete-ekle/<int:urun_id>")
def sepete_ekle(urun_id):
    if "sepet" not in session:
        session["sepet"] = []
    session["sepet"].append(urun_id)
    session.modified = True
    return redirect(request.referrer or url_for("ana_sayfa"))


@app.route("/sepetten-cikar/<int:urun_id>")
def sepetten_cikar(urun_id):
    if "sepet" in session:
        sepet = session["sepet"]
        if urun_id in sepet:
            sepet.remove(urun_id)
        session.modified = True
    return redirect(url_for("sepet_sayfasi"))


@app.route("/sepet")
def sepet_sayfasi():
    sepet_ids = session.get("sepet", [])
    if not sepet_ids:
        return render_template(
            "sepet.html", sepet_urunler=[], toplam_fiyat=0, toplam_urun=0
        )

    baglanti = sqlite3.connect("taki_magaza.db")
    baglanti.row_factory = sqlite3.Row
    cursor = baglanti.cursor()

    placeholders = ",".join("?" * len(set(sepet_ids)))
    cursor.execute(
        f"SELECT * FROM urunler WHERE id IN ({placeholders})", list(set(sepet_ids))
    )
    urun_verileri = cursor.fetchall()

    sepet_urunler = []
    toplam_fiyat = 0

    for urun in urun_verileri:
        adet = sepet_ids.count(urun["id"])
        ara_toplam = urun["fiyat"] * adet
        toplam_fiyat += ara_toplam
        sepet_urunler.append(
            {
                "id": urun["id"],
                "ad": urun["ad"],
                "aciklama": urun["aciklama"],
                "fiyat": urun["fiyat"],
                "adet": adet,
                "ara_toplam": ara_toplam,
            }
        )

    baglanti.close()
    return render_template(
        "sepet.html",
        sepet_urunler=sepet_urunler,
        toplam_fiyat=toplam_fiyat,
        toplam_urun=len(sepet_ids),
    )


@app.route("/sepeti-bosalt")
def sepeti_bosalt():
    session.pop("sepet", None)
    return redirect(url_for("sepet_sayfasi"))


@app.route("/odeme", methods=["GET", "POST"])
def odeme_sayfasi():
    sepet_ids = session.get("sepet", [])
    if not sepet_ids:
        return redirect(url_for("sepet_sayfasi"))

    if request.method == "POST":
        ad_soyad = request.form.get("ad_soyad")
        telefon = request.form.get("telefon")
        adres = request.form.get("adres")
        odeme_tipi = request.form.get("odeme_tipi")

        if ad_soyad and telefon and adres and odeme_tipi:
            session.pop("sepet", None)
            return render_template(
                "siparis_basarili.html",
                ad_soyad=ad_soyad,
                odeme_tipi=odeme_tipi,
                toplam_urun=0,
            )

    baglanti = sqlite3.connect("taki_magaza.db")
    baglanti.row_factory = sqlite3.Row
    cursor = baglanti.cursor()
    placeholders = ",".join("?" * len(set(sepet_ids)))
    cursor.execute(
        f"SELECT * FROM urunler WHERE id IN ({placeholders})", list(set(sepet_ids))
    )
    urun_verileri = cursor.fetchall()

    toplam_fiyat = 0
    for urun in urun_verileri:
        adet = sepet_ids.count(urun["id"])
        toplam_fiyat += urun["fiyat"] * adet
    baglanti.close()

    return render_template(
        "odeme.html", toplam_fiyat=toplam_fiyat, toplam_urun=len(sepet_ids)
    )


if __name__ == "__main__":
    app.run(debug=True)