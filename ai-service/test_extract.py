import fitz
import sys
import re

def test_extraction(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        
        print("--- TOP 1000 CHARACTERS RAW ---")
        print(repr(text[:1000]))
        
        # Look for the specific problem headings
        print("\n--- SEARCHING FOR HEADINGS ---")
        lines = text.split('\n')
        for i, line in enumerate(lines):
            clean_line = line.strip().lower()
            if 'skill' in clean_line or 'project' in clean_line:
                print(f"Line {i}: {repr(line)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_extraction(sys.argv[1])
