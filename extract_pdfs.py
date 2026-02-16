import PyPDF2
import os
import sys

# Paths to the PDFs
pdf1_path = r'c:\Users\juan luis\Downloads\petrofisica_app\geomind_saas\Nodal Analysis and Multiphase Flow in Petroleum Production Engineering - NotebookLM.pdf'
pdf2_path = r'c:\Users\juan luis\Downloads\petrofisica_app\geomind_saas\Nodal Analysis and Multiphase Flow in Petroleum Production Engineering -2 NotebookLM.pdf'

def extract_text(path, label):
    print(f"\n{'='*20} START {label} {'='*20}")
    if not os.path.exists(path):
        print(f"Error: File not found: {path}")
        return
    
    try:
        reader = PyPDF2.PdfReader(path)
        print(f"Pages: {len(reader.pages)}")
        for i, page in enumerate(reader.pages):
            print(f"\n--- Page {i+1} ---")
            print(page.extract_text())
    except Exception as e:
        print(f"Error reading {label}: {e}")
    print(f"\n{'='*20} END {label} {'='*20}")

extract_text(pdf1_path, "PDF 1 (Guía Técnica)")
extract_text(pdf2_path, "PDF 2 (Guía Maestra)")
