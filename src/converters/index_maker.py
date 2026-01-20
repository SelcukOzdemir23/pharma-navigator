import json
import os

def create_master_index(base_data_path, output_path):
    """
    Tüm _meta.json dosyalarını tarar ve merkezi bir navigasyon haritası (TONL) oluşturur.
    """
    index_lines = ["[MASTER_INDEX]"]
    
    # data/ klasöründeki her şeyi listele
    items = os.listdir(base_data_path)
    
    for folder_name in items:
        folder_path = os.path.join(base_data_path, folder_name)
        
        # Sadece klasörleri işle (pdfs ve processed_tonl klasörlerini atla)
        if os.path.isdir(folder_path) and folder_name not in ["pdfs", "processed_tonl"]:
            # Meta dosyasının tam yolunu bul: data/ILAC_ADI/ILAC_ADI_meta.json
            meta_file = os.path.join(folder_path, f"{folder_name}_meta.json")
            
            if os.path.exists(meta_file):
                print(f"📖 Endeksleniyor: {folder_name}")
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                
                # İlaç başlığını ekle (tonl dosyasıyla aynı isimde olmalı)
                index_lines.append(f"\nDRUG[{folder_name}]:")
                
                # İçindekiler tablosunu işle
                toc = meta.get('table_of_contents', [])
                if not toc:
                    index_lines.append("  - (İçindekiler bulunamadı)")
                    continue

                for item in toc:
                    title = item.get('title', '').replace('\n', ' ').strip()
                    page = item.get('page_id')
                    
                    # Boş başlıkları atla
                    if title:
                        index_lines.append(f"  - {title} (Page: {page})")
            else:
                print(f"⚠️ Uyarı: {meta_file} bulunamadı.")

    # Master Index dosyasını kaydet
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(index_lines))
    
    print(f"\n🚀 Master Index başarıyla oluşturuldu: {output_path}")

if __name__ == "__main__":
    # Senin yapına göre yollar
    current_dir = os.getcwd()
    data_folder = os.path.join(current_dir, "data")
    # Master index'i doğrudan data klasörünün içine koyuyoruz
    master_index_path = os.path.join(data_folder, "master_index.tonl")
    
    create_master_index(data_folder, master_index_path)