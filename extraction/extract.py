from pdfminer.high_level import extract_text


if __name__ == '__main__':
    pdf_path = '61.pdf'
    text = extract_text(pdf_path)
    print(text)
    with open('61.txt', 'w') as f:
        f.write(text)
    

class PDFParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path

    def parse(self):
        text = extract_text(self.pdf_path)
        return text
    
    def save_text(self, text):
        with open('61.txt', 'w') as f:
            f.write(text)

