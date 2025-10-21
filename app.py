from flask import Flask, render_template, request
from scraper_all import scrape_dan_klasifikasi
import pandas as pd

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    hasil_all = None
    hasil_ekonomi = None

    if request.method == "POST":
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        max_articles = int(request.form.get("max_articles") or 5)

        print(f"Menerima permintaan: start_date={start_date}, end_date={end_date}, max_articles={max_articles}")
        print("Memulai proses scraping dan klasifikasi...")

        try:
            df_all, df_ekonomi = scrape_dan_klasifikasi(start_date, end_date, max_articles)
            
            if df_all is not None and not df_all.empty:
                hasil_all = df_all.to_dict(orient="records")
                for item in hasil_all:
                    item['isi'] = (item['isi'][:200] + '...') if len(str(item['isi'])) > 200 else item['isi']
                print(f"Berhasil memproses {len(hasil_all)} artikel total")

            if df_ekonomi is not None and not df_ekonomi.empty:
                hasil_ekonomi = df_ekonomi.to_dict(orient="records")
                for item in hasil_ekonomi:
                    item['isi'] = (item['isi'][:200] + '...') if len(str(item['isi'])) > 200 else item['isi']
                print(f"Berhasil memproses {len(hasil_ekonomi)} artikel ekonomi")
            
        except Exception as e:
            print(f"Error saat memproses hasil: {str(e)}")
            hasil_all = []
            hasil_ekonomi = []
        
        print("Proses selesai. Mengirim hasil ke template.")

    return render_template("index.html", hasil_all=hasil_all, hasil_ekonomi=hasil_ekonomi)

if __name__ == "__main__":
    app.run(debug=True)