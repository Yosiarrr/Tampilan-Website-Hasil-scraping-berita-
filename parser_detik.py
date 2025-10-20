# parser_detik.py (Optimized)
from datetime import datetime, date as date_cls
import pandas as pd
from bs4 import BeautifulSoup
import time

def _ensure_date(dt):
    """Helper untuk memastikan format tanggal yang konsisten."""
    if dt is None:
        return None
    if isinstance(dt, date_cls):
        return dt
    if isinstance(dt, datetime):
        return dt.date()
    if isinstance(dt, str):
        s = dt.strip()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(s, fmt).date()
            except:
                continue
        try:
            return datetime.fromisoformat(s).date()
        except:
            raise ValueError(f"Format tanggal tidak didukung: {s}")
    raise TypeError(f"Tipe tanggal tidak didukung: {type(dt)}")

def _safe_get(driver, url, retries=2, delay=1):
    """Helper untuk mengambil halaman dengan retry."""
    for i in range(retries):
        try:
            driver.get(url)
            return True
        except Exception as e:
            if i < retries - 1:  # jangan sleep di percobaan terakhir
                time.sleep(delay)
    return False

def parse_detik_lampung(driver, start_date=None, end_date=None, max_pages=2, max_articles=50, simpan=False, output_file="hasil_detik_lampung.xlsx"):
    """Parser untuk Detik Lampung yang dioptimasi."""
    print("[INFO] Memulai parse Detik Lampung...")
    start_time = time.time()
    
    start_date_obj = _ensure_date(start_date)
    end_date_obj = _ensure_date(end_date)
    
    base_url = "https://www.detik.com/tag/lampung/?sortby=time&page={}"
    results = []
    total_found = 0
    
    for p in range(1, max_pages + 1):
        if total_found >= max_articles:
            break
            
        url = base_url.format(p)
        print(f"🔄 Halaman {p}: {url}")
        
        if not _safe_get(driver, url):
            print(f"❌ Gagal mengakses halaman {p}")
            continue
            
        time.sleep(0.5)  # delay minimal
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Kumpulkan semua link artikel
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "/news/" in href or "detik.com" in href:
                title = a.get_text(strip=True)
                if href not in [l[1] for l in links]:
                    links.append((title, href))
        
        # Proses setiap artikel
        for title, link in links:
            if total_found >= max_articles:
                break
                
            try:
                if not _safe_get(driver, link, retries=1):
                    continue
                    
                time.sleep(0.3)  # delay minimal untuk artikel
                art_soup = BeautifulSoup(driver.page_source, "html.parser")
                
                # Ekstraksi tanggal dengan berbagai metode
                tanggal = None
                time_tag = art_soup.find("time")
                if time_tag and time_tag.has_attr("datetime"):
                    try:
                        tanggal = datetime.fromisoformat(time_tag["datetime"]).date()
                    except:
                        pass
                
                if not tanggal:
                    ttxt = art_soup.find(class_="date") or art_soup.find(class_="time")
                    if ttxt:
                        txt = ttxt.get_text(strip=True)
                        for fmt in ("%A, %d %b %Y %H:%M", "%d %b %Y %H:%M", "%Y-%m-%d %H:%M"):
                            try:
                                tanggal = datetime.strptime(txt.split(" WIB")[0], fmt).date()
                                break
                            except:
                                continue
                
                if not tanggal:
                    tanggal = datetime.now().date()
                
                # Filter berdasarkan tanggal
                if (start_date_obj and tanggal < start_date_obj) or \
                   (end_date_obj and tanggal > end_date_obj):
                    continue
                
                # Ekstraksi isi artikel
                paras = art_soup.find_all('p')
                isi = " ".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))
                
                if not isi:  # Skip artikel kosong
                    continue
                    
                results.append({
                    "judul": title.strip(),
                    "link": link,
                    "tanggal": tanggal,
                    "isi": isi
                })
                total_found += 1
                print(f"✅ Artikel {total_found}/{max_articles}: {title[:50]}...")
                
            except Exception as e:
                print(f"❌ Gagal parse artikel: {link}, error: {str(e)[:100]}")
                continue

    duration = time.time() - start_time
    print(f"[INFO] Parse Detik Lampung selesai dalam {duration:.2f} detik")
    print(f"Total artikel berhasil: {len(results)}")
    
    df = pd.DataFrame(results)
    if simpan and not df.empty:
        df.to_excel(output_file, index=False)
    return df