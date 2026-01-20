import json
import os
import re

def clean_html(text):
    if not text: return ""
    # Gereksiz etiketleri temizle, hiyerarşiyi korur
    text = re.sub(r'<(?!/?(h1|h2|h3|h4|table|tr|td|li|b|i)).*?>', '', text)
    return " ".join(text.split()).strip()

def extract_blocks(blocks, valid_types):
    """Blokları derinlemesine (recursive) tarar ve metin içerenleri döndürür."""
    extracted = []
    for block in blocks:
        b_type = block.get('block_type')
        
        # Eğer bu blok metin içeren bir yaprak bloksa (Text, ListItem vb.)
        if b_type in valid_types:
            content = clean_html(block.get('html', ''))
            if not content and block.get('text'):
                content = block.get('text').strip()
            
            if content:
                extracted.append((b_type, content))
        
        # EĞER BLOĞUN KENDİ ÇOCUKLARI VARSA (ListGroup gibi), ONLARI DA TARA!
        if block.get('children'):
            extracted.extend(extract_blocks(block['children'], valid_types))
            
    return extracted

def process_all_drugs(base_data_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    valid_types = ["SectionHeader", "Text", "Table", "ListItem", "Span", "Line"]

    for drug_folder in os.listdir(base_data_path):
        folder_path = os.path.join(base_data_path, drug_folder)
        json_file = os.path.join(folder_path, f"{drug_folder}.json")
        
        if os.path.isdir(folder_path) and os.path.exists(json_file):
            print(f"🔄 Derin Tarama Başladı: {drug_folder}...")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tonl_lines = [f"DRUG[{drug_folder}]"]
            for page in data.get('children', []):
                page_parts = page.get('id', '').split('/')
                page_id = page_parts[2] if len(page_parts) > 2 else "unknown"
                tonl_lines.append(f"  P[{page_id}]:")
                
                # RECURSIVE FONKSİYONU ÇAĞIR (ListGroup içindekileri bulur)
                blocks = extract_blocks(page.get('children', []), valid_types)
                for b_type, content in blocks:
                    tonl_lines.append(f"    <{b_type}>: {content}")

            with open(os.path.join(output_dir, f"{drug_folder}.tonl"), 'w', encoding='utf-8') as f:
                f.write("\n".join(tonl_lines))
            print(f"✅ Başarılı: {drug_folder}.tonl (Tüm katmanlar işlendi)")

if __name__ == "__main__":
    current_path = os.getcwd()
    process_all_drugs(os.path.join(current_path, "data"), os.path.join(current_path, "data", "processed_tonl"))