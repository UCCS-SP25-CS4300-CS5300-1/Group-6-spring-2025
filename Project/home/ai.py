from transformers import GPT2Tokenizer, GPT2LMHeadModel

#AI model class, gets responses and returns it
class AIModel:
    def __init__(self):

        #Tokenizer to split the text
        self.tokenizer = GPT2Tokenizer.from_pretrained("Lukamac/PlayPart-AI-Personal-Trainer")

        #Model takes tokenized pieces and responds accordingly
        self.model = GPT2LMHeadModel.from_pretrained("Lukamac/PlayPart-AI-Personal-Trainer")

        #  Add a pad_token if missing: fill extra spaces if different length sentences
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.model.config.pad_token_id = self.tokenizer.eos_token_id

    #Takes input and responds accordingly
    def get_response(self, input_text):
        print(f"Generating response for: {input_text}")
    
        #Gives input to tokenizer, turns the input into numbers
        inputs = self.tokenizer(
            input_text,
            #Creating pytorch sensors, which is data structure for AI model
            return_tensors='pt',
            padding=True,
            truncation=False
        )


        #Generate new text based on
        output_ids = self.model.generate(
            inputs['input_ids'],
            attention_mask=inputs['attention_mask'],
            max_length=20,
            top_k=50,
            pad_token_id=self.tokenizer.pad_token_id  
        )

        #Convert the id's back into normal text!
        response = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return response


# Instantiate and ready for use globally
ai_model = AIModel()
