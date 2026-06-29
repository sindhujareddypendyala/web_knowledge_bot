from pdf.pdf_processor import extract_text_from_pdf

pdf_path = "uploads/sample.pdf"

text = extract_text_from_pdf(pdf_path)

print("=" * 50)
print(text[:2000])      # Print first 2000 characters
print("=" * 50)
print(f"\nTotal Characters: {len(text)}")