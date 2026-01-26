"""
Clean and structure existing markdown files for RAG optimization.
Takes manually created MD files and applies:
- Page number removal
- Hierarchical heading structure
- Side effect categorization
- Line wrapping fixes
"""

import re
from pathlib import Path
from typing import List
import argparse


def clean_markdown_structure(text: str) -> str:
    """Clean and restructure markdown for RAG."""
    
    lines = text.split('\n')
    processed = []
    in_side_effects = False
    last_main_section = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if not stripped:
            processed.append('')
            continue
        
        # Remove page numbers
        if re.match(r'^\d+/\d+\s*$', stripped):
            continue
        
        # Detect main sections: "# **1. ARVELES nedir**" → "## 1. ARVELES nedir"
        main_section = re.match(r'^#\s+\*\*(\d+)\.\s+(.+?)\*\*$', stripped)
        if main_section:
            num = main_section.group(1)
            title = main_section.group(2)
            processed.append(f"## {num}. {title}")
            last_main_section = title.lower()
            in_side_effects = 'yan etki' in last_main_section
            continue
        
        # Detect subsections: "# **KULLANMAYINIZ**" → "### KULLANMAYINIZ"
        subsection = re.match(r'^#\s+\*\*([A-ZÇĞİÖŞÜ][^*]+)\*\*$', stripped)
        if subsection:
            title = subsection.group(1).strip()
            # Check if it's a frequency category in side effects
            if in_side_effects and re.match(r'^(Çok\s+)?(Yaygın|Seyrek|Bilinmiyor)(\s+olmayan)?$', title, re.IGNORECASE):
                processed.append(f"### {title}")
            else:
                processed.append(f"### {title}")
            continue
        
        # Detect standalone frequency categories (not in bold/heading)
        if in_side_effects:
            freq_match = re.match(r'^(Çok\s+)?(Yaygın|Seyrek|Bilinmiyor)(\s+olmayan)?[:\s]*$', stripped, re.IGNORECASE)
            if freq_match:
                processed.append(f"### {stripped.rstrip(':')}") 
                continue
        
        # Keep regular content
        processed.append(line)
    
    result = '\n'.join(processed)
    
    # Remove excessive blank lines
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    # Remove page numbers inline (e.g., "text 1/10 more text")
    result = re.sub(r'\s+\d+/\d+\s+', ' ', result)
    
    return result


def add_frontmatter_if_missing(text: str, filename: str) -> str:
    """Add YAML frontmatter if not present."""
    
    if text.startswith('---'):
        return text  # Already has frontmatter
    
    # Extract drug name from filename or first heading
    drug_name = filename.replace('.md', '')
    
    # Try to extract from content
    name_match = re.search(r'^#\s+\*?\*?([A-ZÇĞİÖŞÜ®]+[^*\n]+)', text, re.MULTILINE)
    if name_match:
        extracted_name = name_match.group(1).strip().rstrip('*')
        if extracted_name:
            drug_name = extracted_name
    
    # Extract dosage form
    dosage_match = re.search(r'(\d+\s*mg[^\.]*(?:tablet|kapsül|enjeksiyonluk|damla|şurup))', text, re.IGNORECASE)
    dosage_form = dosage_match.group(1) if dosage_match else ""
    
    # Extract active ingredient
    ingredient_match = re.search(r'Etkin madde[:\s]+([^\n]+)', text, re.IGNORECASE)
    active_ingredient = ingredient_match.group(1).strip() if ingredient_match else ""
    
    frontmatter = ["---"]
    frontmatter.append(f"drug_name: {drug_name}")
    if dosage_form:
        frontmatter.append(f"dosage_form: {dosage_form}")
    if active_ingredient:
        frontmatter.append(f"active_ingredient: {active_ingredient}")
    frontmatter.append("---")
    frontmatter.append("")
    
    return '\n'.join(frontmatter) + '\n' + text


def process_file(input_path: Path, output_path: Path, add_frontmatter: bool = True):
    """Process a single markdown file."""
    
    print(f"\n🔄 Processing: {input_path.name}")
    
    # Read original
    original_text = input_path.read_text(encoding='utf-8')
    
    # Clean and restructure
    cleaned_text = clean_markdown_structure(original_text)
    
    # Add frontmatter if requested
    if add_frontmatter:
        final_text = add_frontmatter_if_missing(cleaned_text, input_path.name)
    else:
        final_text = cleaned_text
    
    # Save
    output_path.write_text(final_text, encoding='utf-8')
    
    # Stats
    h1_count = final_text.count('\n# ')
    h2_count = final_text.count('\n## ')
    h3_count = final_text.count('\n### ')
    
    print(f"   ✅ Cleaned: {len(original_text)} → {len(final_text)} chars")
    print(f"   📊 Structure: {h1_count} H1, {h2_count} H2, {h3_count} H3")
    print(f"   💾 Saved to: {output_path}")


def batch_clean(input_dir: Path, output_dir: Path, add_frontmatter: bool = True):
    """Batch clean markdown files."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    md_files = list(input_dir.glob("*.md"))
    
    if not md_files:
        print(f"⚠️  No markdown files found in {input_dir}")
        return
    
    print(f"\n{'='*70}")
    print(f"🧹 Markdown Cleaner for RAG")
    print(f"📥 Input:  {input_dir}")
    print(f"📤 Output: {output_dir}")
    print(f"📝 Frontmatter: {'Yes' if add_frontmatter else 'No'}")
    print(f"📄 Files: {len(md_files)}")
    print(f"{'='*70}")
    
    for md_path in md_files:
        output_path = output_dir / md_path.name
        process_file(md_path, output_path, add_frontmatter)
    
    print(f"\n{'='*70}")
    print(f"✅ Cleaned {len(md_files)} files")
    print(f"📁 Output: {output_dir}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Clean manually created markdown files for RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean markdown files
  python scripts/clean_markdown.py
  
  # Custom directories
  python scripts/clean_markdown.py --input-dir data/pdfs --output-dir data/md_cleaned
  
  # No frontmatter
  python scripts/clean_markdown.py --no-frontmatter
        """
    )
    
    parser.add_argument(
        '--input-dir',
        type=Path,
        default=Path('data/pdfs'),
        help='Input directory with markdown files (default: data/pdfs)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/md_cleaned'),
        help='Output directory (default: data/md_cleaned)'
    )
    
    parser.add_argument(
        '--no-frontmatter',
        action='store_true',
        help='Skip YAML frontmatter generation'
    )
    
    args = parser.parse_args()
    
    if not args.input_dir.exists():
        print(f"❌ Input directory not found: {args.input_dir}")
        return
    
    batch_clean(args.input_dir, args.output_dir, add_frontmatter=not args.no_frontmatter)


if __name__ == "__main__":
    main()
