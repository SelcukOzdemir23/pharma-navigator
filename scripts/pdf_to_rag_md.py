"""
PDF to High-Quality Markdown Converter for RAG Systems
Processes Turkish drug prospectuses with RAG-optimized structure.

Features:
- Hierarchical heading structure (H1 → H2 → H3)
- Section categorization (Yan Etkiler, Endikasyonlar, etc.)
- Page number removal (1/10, 2/10, etc.)
- Line wrapping cleanup
- Frequency-based subheadings for side effects
"""

import os
import re
from pathlib import Path
from typing import Optional, List
import argparse

import pdfplumber


def extract_drug_metadata(text: str) -> dict:
    """Extract drug metadata from prospectus text."""
    metadata = {}
    
    # Extract drug name (first significant heading)
    name_match = re.search(r'^#\s*([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s®]+)', text, re.MULTILINE)
    if name_match:
        metadata['drug_name'] = name_match.group(1).strip()
    
    # Extract dosage form
    dosage_match = re.search(r'(\d+\s*mg[^\.]*(?:tablet|kapsül|enjeksiyonluk|damla|şurup))', text, re.IGNORECASE)
    if dosage_match:
        metadata['dosage_form'] = dosage_match.group(1)
    
    # Extract active ingredient
    ingredient_match = re.search(r'Etkin madde[:\s]+([^\n]+)', text, re.IGNORECASE)
    if ingredient_match:
        metadata['active_ingredient'] = ingredient_match.group(1).strip()
    
    return metadata


def clean_raw_text(text: str) -> str:
    """Clean raw PDF text before processing."""
    
    # Remove page numbers (1/10, 2/10, etc.)
    text = re.sub(r'\n?\d+/\d+\s*\n?', '', text)
    
    # Remove repeated KULLANMA TALİMATI headers
    text = re.sub(r'KULLANMA TALİMATI\s*\n+', '', text, flags=re.IGNORECASE)
    
    # Fix broken lines (text wrapped mid-word)
    # Join lines that don't end with punctuation
    lines = text.split('\n')
    cleaned_lines = []
    i = 0
    while i < len(lines):
        current = lines[i].rstrip()
        
        # If line doesn't end with punctuation and next line doesn't start with bullet/number
        if current and i + 1 < len(lines):
            next_line = lines[i + 1].lstrip()
            if (not current[-1] in '.!?:;,)' and 
                not next_line.startswith(('-', '•', '*', '1', '2', '3', '4', '5'))):
                # Join with next line (remove hyphenation if exists)
                if current.endswith('-'):
                    current = current[:-1] + next_line
                else:
                    current = current + ' ' + next_line
                i += 2
                cleaned_lines.append(current)
                continue
        
        cleaned_lines.append(current)
        i += 1
    
    text = '\n'.join(cleaned_lines)
    
    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def create_hierarchical_structure(text: str) -> str:
    """Convert flat structure to hierarchical markdown."""
    
    lines = text.split('\n')
    processed_lines = []
    current_h1_section = None
    in_side_effects = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            processed_lines.append('')
            continue
        
        # Detect main numbered sections (1. ARVELES nedir → ## 1. ARVELES nedir)
        main_section_match = re.match(r'^(\d+)\.\s+([A-ZÇĞİÖŞÜ].+)', line)
        if main_section_match:
            num = main_section_match.group(1)
            title = main_section_match.group(2)
            processed_lines.append(f"## {num}. {title}")
            current_h1_section = title.lower()
            in_side_effects = 'yan etki' in current_h1_section
            continue
        
        # Detect side effect frequency categories
        if in_side_effects:
            # "Çok yaygın:", "Yaygın:", "Yaygın olmayan:", "Seyrek:", "Çok seyrek:"
            freq_match = re.match(r'^(Çok\s+)?([Yy]aygın|[Ss]eyrek|[Bb]ilinmiyor)(\s+olmayan)?[:\s]*$', line, re.IGNORECASE)
            if freq_match:
                processed_lines.append(f"### {line.rstrip(':')}")
                continue
            
            # Alternative patterns: "Yaygın olmayan" as separate line
            if re.match(r'^(Çok yaygın|Yaygın olmayan|Seyrek|Çok seyrek|Bilinmiyor)\s*$', line, re.IGNORECASE):
                processed_lines.append(f"### {line}")
                continue
        
        # Detect other important subsections (dikkat edilmesi gerekenler, KULLANMAYINIZ, etc.)
        subsection_patterns = [
            r'KULLANMAYINIZ',
            r'DİKKATLİ KULLANINIZ',
            r'dikkat edilmesi gerekenler',
            r'nasıl kullanılır',
            r'Saklanması',
            r'Hamilelik',
            r'Emzirme',
            r'Araç ve makine kullanımı',
            r'Enfeksiyonlar',
            r'Çocuklar ve ergenler'
        ]
        
        for pattern in subsection_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                # Check if it's all caps or bold-styled
                if line.isupper() or re.match(r'^\*\*.+\*\*$', line):
                    processed_lines.append(f"### {line.replace('*', '').strip()}")
                    continue
        
        # Regular line
        processed_lines.append(line)
    
    return '\n'.join(processed_lines)


def add_yaml_frontmatter(text: str, metadata: dict) -> str:
    """Add YAML frontmatter for better metadata extraction."""
    
    frontmatter_lines = ["---"]
    if metadata.get('drug_name'):
        frontmatter_lines.append(f"drug_name: {metadata['drug_name']}")
    if metadata.get('dosage_form'):
        frontmatter_lines.append(f"dosage_form: {metadata['dosage_form']}")
    if metadata.get('active_ingredient'):
        frontmatter_lines.append(f"active_ingredient: {metadata['active_ingredient']}")
    frontmatter_lines.append("---")
    frontmatter_lines.append("")
    
    return '\n'.join(frontmatter_lines) + '\n' + text


def process_single_pdf(pdf_path: Path, output_dir: Path, use_frontmatter: bool = True) -> bool:
    """Process a single PDF to RAG-optimized markdown."""
    
    drug_name = pdf_path.stem
    output_path = output_dir / f"{drug_name}.md"
    
    print(f"\n🔄 Processing: {drug_name}")
    
    try:
        # Extract text with pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            raw_text = "\n\n".join(pages)
        
        print(f"   ✅ Extracted {len(raw_text)} characters from {len(pages)} pages")
        
        # Clean raw text
        cleaned_text = clean_raw_text(raw_text)
        
        # Convert to basic markdown (heading detection)
        # Convert numbered sections to H1
        md_text = re.sub(r'^(\d+)\.\s+([A-ZÇĞİÖŞÜ].+)$', r'# \1. \2', cleaned_text, flags=re.MULTILINE)
        
        # Create hierarchical structure
        hierarchical_text = create_hierarchical_structure(md_text)
        
        # Extract metadata
        metadata = extract_drug_metadata(hierarchical_text)
        
        # Add frontmatter if requested
        if use_frontmatter and metadata:
            final_text = add_yaml_frontmatter(hierarchical_text, metadata)
        else:
            # Just add drug name as H1
            final_text = f"# {drug_name}\n\n{hierarchical_text}"
        
        # Save
        output_path.write_text(final_text, encoding='utf-8')
        print(f"   💾 Saved to: {output_path}")
        
        # Quick stats
        h1_count = final_text.count('\n# ')
        h2_count = final_text.count('\n## ')
        h3_count = final_text.count('\n### ')
        print(f"   📊 Structure: {h1_count} H1, {h2_count} H2, {h3_count} H3")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def batch_process(input_dir: Path, output_dir: Path, use_frontmatter: bool = True):
    """Batch process all PDFs in directory."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {input_dir}")
        return
    
    print(f"\n{'='*70}")
    print(f"📚 RAG-Optimized PDF → Markdown Converter")
    print(f"📥 Input:  {input_dir}")
    print(f"📤 Output: {output_dir}")
    print(f"📝 Frontmatter: {'Yes' if use_frontmatter else 'No'}")
    print(f"📄 Files: {len(pdf_files)}")
    print(f"{'='*70}")
    
    successful = 0
    failed = 0
    
    for pdf_path in pdf_files:
        if process_single_pdf(pdf_path, output_dir, use_frontmatter):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Output: {output_dir}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Convert drug PDFs to RAG-optimized markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  python scripts/pdf_to_rag_md.py
  
  # Custom directories
  python scripts/pdf_to_rag_md.py --input-dir data/İlaçlar --output-dir data/md
  
  # Without YAML frontmatter
  python scripts/pdf_to_rag_md.py --no-frontmatter
        """
    )
    
    parser.add_argument(
        '--input-dir',
        type=Path,
        default=Path('data/İlaçlar'),
        help='Input directory containing PDFs (default: data/İlaçlar)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/md'),
        help='Output directory for markdown files (default: data/md)'
    )
    
    parser.add_argument(
        '--no-frontmatter',
        action='store_true',
        help='Disable YAML frontmatter generation'
    )
    
    args = parser.parse_args()
    
    if not args.input_dir.exists():
        print(f"❌ Input directory not found: {args.input_dir}")
        return
    
    batch_process(args.input_dir, args.output_dir, use_frontmatter=not args.no_frontmatter)


if __name__ == "__main__":
    main()
