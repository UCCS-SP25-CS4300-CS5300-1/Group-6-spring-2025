import os
import openai

# Set your OpenAI API key here or via an environment variable named "OPENAI_API_KEY"
openai.api_key = os.getenv("OPENAI_API_KEY", "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")

class AIModel:
    def __init__(self):
        # Additional initialization can be added here if needed.
        pass

    def get_response(self, input_text):
        """
        Given an input prompt, calls the ChatGPT API using the gpt-3.5-turbo model and returns the generated response.
        """
        print(f"Generating response for: {input_text}")
        
        messages = [
            {"role": "system", "content": "You are a helpful personal trainer."},
            {"role": "user", "content": input_text}
        ]
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300,
                n=1,
                stop=None,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            answer = f"Error generating response: {str(e)}"
        
        return answer

# Instantiate the AI model for use globally
ai_model = AIModel()


