#!/usr/bin/env python
"""
Script untuk convert HTML files ke Django template inheritance.
Menghapus sidebar dan struktur HTML, hanya keep content.
"""

import os
import re
from pathlib import Path

templates_dir = Path(r'c:\Users\Dea\OneDrive\Documents\kuliah\TA\data\ta-dea\glod_app\templates\glod_app')

files_to_convert = {
    'preprocessing_index.html': 'Persiapan Data - GLOD Community Detector',
    'string_input.html': 'Upload Data STRING - GLOD Community Detector',
    'results_index.html': 'Lihat Hasil - GLOD Community Detector',
    'process.html': 'Analisis GLOD - GLOD Community Detector',
    'result.html': 'Hasil Analisis GLOD - GLOD Community Detector',
    'index.html': 'Home - GLOD Community Detector',
    'uniprot_index.html': 'UniProt - GLOD Community Detector',
}

def extract_content_and_style(html_content):
    """Extract style dan content dari HTML file."""
    styles = []
    content = ""
    
    # Extract style tags
    style_pattern = r'<style[^>]*>(.*?)</style>'
    for match in re.finditer(style_pattern, html_content, re.DOTALL):
        styles.append(match.group(1).strip())
    
    # Remove old DOCTYPE, html, head, sidebar, container structure
    # Keep hanya content dalam main/content area
    
    # Find main content area (setelah sidebar)
    # Pattern: <main atau <div class="main"
    main_pattern = r'<main[^>]*>|<div[^>]*class="main"[^>]*>'
    main_start = html_content.find('<main')
    if main_start == -1:
        main_start = html_content.find('<div class="main"')
    
    if main_start == -1:
        # Fallback: cari div container kedua atau content pertama setelah sidebar
        main_start = 0
        # Skip sidebar
        if '<nav class="sidebar"' in html_content:
            main_start = html_content.find('</nav>')
    
    # Find closing main
    main_end = html_content.find('</main>')
    if main_end == -1:
        main_end = len(html_content) - 200  # Approximate
    
    if main_start > 0 and main_end > main_start:
        # Extract content antara main tags
        content_match = html_content[main_start:main_end]
        # Remove <main> opening tag
        content = re.sub(r'^<main[^>]*>', '', content_match)
    else:
        # Fallback: skip semua sampai menemukan content
        sidebar_end = html_content.find('</nav>')
        if sidebar_end > 0:
            content = html_content[sidebar_end+6:]
        else:
            content = html_content
    
    # Clean up closing tags
    content = re.sub(r'^\s*<div class="container">', '', content)
    content = re.sub(r'^\s*<main[^>]*>', '', content)
    
    return styles, content.strip()


for filename, title in files_to_convert.items():
    filepath = templates_dir / filename
    
    if not filepath.exists():
        print(f"⚠️  Skip: {filename} tidak ditemukan")
        continue
    
    print(f"Processing: {filename}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    styles, content = extract_content_and_style(html_content)
    
    style_block = '\n'.join(styles) if styles else ""
    
    # Build new template
    new_template = """{% extends "base.html" %}

{% block title %}""" + title + """{% endblock %}

"""
    
    if style_block:
        new_template += """{% block extra_head %}
<style>
""" + style_block + """
</style>
{% endblock %}

"""
    
    new_template += """{% block content %}
""" + content + """
{% endblock %}
"""
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_template)
    
    print(f"✅ Converted: {filename}")

print("\n✨ Semua file berhasil dikonversi!")
