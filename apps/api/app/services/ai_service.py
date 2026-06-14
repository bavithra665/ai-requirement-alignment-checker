import os
from groq import AsyncGroq

class AIService:
    def __init__(self):
        # Initialize groq client dynamically
        api_key = os.getenv("GROQ_API_KEY", "")
        self.client = AsyncGroq(api_key=api_key) if api_key else None

    async def generate_summary(self, requirements: list[str]) -> str:
        """
        Takes raw extracted requirements and generates a Business Summary 
        and Key Features using LLaMA 3.
        """
        if not self.client:
            return "AI Summary is disabled. Please provide GROQ_API_KEY in the environment."
            
        prompt = "You are an expert business analyst. Summarize the following software requirements into a concise 'Business Summary' and a 'Key Features Overview'. Format the output in Markdown.\n\n"
        prompt += "\n".join(requirements)
        
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model="llama3-70b-8192",
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Failed to generate summary: {str(e)}"

ai_service = AIService()
