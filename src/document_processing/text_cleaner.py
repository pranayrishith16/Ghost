import re

class TextCleaner:
    def __init__(self):
        # Legal document specific patterns
        self.patterns = {
            'page_numbers': re.compile(r'\n\s*\d+\s*\n'),
            'excessive_whitespace': re.compile(r'\s{3,}'),
            'line_breaks': re.compile(r'\n{3,}'),
            'case_citations': re.compile(r'\d+\s+[A-Z][A-Za-z\s]+\d+'),  # Simple citation pattern
        }

    def clean_text(self,text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        #remove page numbers
        text = self.patterns['page_numbers'].sub('\n',text)

        #Normalize whitespace
        text = self.patterns['excessive_whitespace'].sub(' ', text)
        text = self.patterns['line_breaks'].sub('\n\n', text)

        # Remove extra spaces around punctuation
        text = re.sub(r'\s+([.,:;!?])', r'\1', text)

        # # Fix common OCR errors (basic)
        # text = text.replace('$', 'section')
        # text = text.replace('¶', 'paragraph')

        # Normalize quotes
        text = text.replace('“', '"').replace('”', '"')
        text = text.replace('‘', "'").replace('’', "'")

        return text.strip()
    
    # def preserve_legal_formatting(self, text: str) -> str:
    #     """Preserve important legal document formatting"""
    #     # Preserve section numbering
    #     text = re.sub(r'^(\d+\.\s*)', r'\n\1', text)

    #     # Preserve subsection formatting
    #     text = re.sub(r'^([a-z]\)\s*)', r'\n\1', text)

    #     return text

    # def extract_sections(self, text: str):
    #     """Extract structured sections from legal documents"""
    #     sections = []

    #     # Pattern for section headers (e.g., "I. INTRODUCTION", "II. BACKGROUND")
    #     section_pattern = re.compile(r'^([IVX]+\.\s+[A-Z\s]+)\n', re.MULTILINE)

    #     matches = list(section_pattern.finditer(text))

    #     for i, match in enumerate(matches):
    #         section_title = match.group(1).strip()
    #         start_pos = match.end()
    #         end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(text)

    #         section_content = text[start_pos:end_pos].strip()

    #         sections.append({
    #             'title': section_title,
    #             'content': section_content,
    #             'position': i + 1,
    #             'start_char': start_pos,
    #             'end_char': end_pos
    #         })

    #     return sections