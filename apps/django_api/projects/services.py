import os
import re
import fitz  # PyMuPDF
import docx
from typing import List
from groq import Groq

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
        full_text = "\n".join(blocks)
        lines = full_text.split('\n')
        
        current_req = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            is_new_req = False
            # 1. Starts with Number (e.g. 1.2.3 )
            if re.match(r'^\d+(\.\d+)*\s+', line):
                is_new_req = True
            # 2. Starts with bullet
            elif line.startswith('-') or line.startswith('•'):
                is_new_req = True
            # 3. Headings or 'shall' block detection
            elif line.isupper() and len(line) > 5:
                is_new_req = True
            # 4. REQ-XXX format (e.g. "REQ-001: " or "REQ-001 ")
            elif re.match(r'^REQ-\d+(:?\s+)', line, re.IGNORECASE):
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


class AIService:
    def generate_executive_summary(self, document_text: str) -> str:
        """
        Takes the entire raw document text and generates a Single Executive Summary.
        """
        api_key = os.getenv("GROQ_API_KEY", "")
        client = Groq(api_key=api_key) if api_key else None
        
        if not client:
            return "AI Summary is disabled. Please provide GROQ_API_KEY in the environment."
            
        prompt = (
            "You are a friendly project manager explaining a new software project to a client with zero technical background. "
            "Read the following requirements and generate a single 'Executive Summary' for the entire project. "
            "The summary MUST be extremely simple, highly readable, and completely free of any technical jargon. "
            "Explain it like you would to a complete beginner. Use simple words and short, clear sentences.\n\n"
            "You MUST use exactly these four headings and nothing else:\n"
            "Project Purpose:\n"
            "Key Features:\n"
            "Benefits:\n"
            "Expected Outcome:\n\n"
            "Do not include any other text or preamble. Format it exactly as requested.\n\n"
            "Requirements:\n"
        )
        prompt += document_text[:8000] # Cap text to avoid exceeding token limits in simple test
        
        try:
            response = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Failed to generate executive summary: {str(e)}"

extraction_service = ExtractionService()
ai_service = AIService()
