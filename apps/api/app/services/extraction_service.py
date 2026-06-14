import fitz  # PyMuPDF
import docx
from typing import List
import re

class ExtractionService:
    def parse_pdf(self, file_path: str) -> List[str]:
        doc = fitz.open(file_path)
        text_blocks = []
        for page in doc:
            text_blocks.append(page.get_text("text"))
        return self._extract_deterministic(text_blocks)
        
    def parse_docx(self, file_path: str) -> List[str]:
        doc = docx.Document(file_path)
        text_blocks = [p.text for p in doc.paragraphs if p.text.strip()]
        return self._extract_deterministic(text_blocks)
        
    def _extract_deterministic(self, blocks: List[str]) -> List[str]:
        requirements = []
        # Basic heuristic priority: 1. Headings, 2. Numbered Requirements, 3. Bullet points
        
        full_text = "\n".join(blocks)
        lines = full_text.split('\n')
        
        current_req = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Heuristic for new requirement starting
            is_new_req = False
            # 1. Starts with Number (e.g. 1.2.3 )
            if re.match(r'^\d+(\.\d+)*\s+', line):
                is_new_req = True
            # 2. Starts with bullet
            elif line.startswith('-') or line.startswith('•'):
                is_new_req = True
            # 3. Headings or 'shall' block detection (uppercase heuristics)
            elif line.isupper() and len(line) > 5:
                is_new_req = True
                
            if is_new_req:
                if current_req:
                    requirements.append(" ".join(current_req))
                current_req = [line]
            else:
                if current_req:
                    current_req.append(line)
        
        if current_req:
            requirements.append(" ".join(current_req))
            
        return requirements

extraction_service = ExtractionService()
