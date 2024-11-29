import requests
import json

class OllamaAPI:
    def __init__(self, base_url="http://localhost:11434"):
        """Initialize Ollama API client.
        
        Args:
            base_url (str): Base URL for Ollama API (default: http://localhost:11434)
        """
        self.base_url = base_url.rstrip('/')
        
    def generate(self, model="llama2", prompt="", system="", options=None):
        """Generate a response using the specified model.
        
        Args:
            model (str): Name of the model to use
            prompt (str): The prompt to send to the model
            system (str): System prompt to prepend
            options (dict): Additional model parameters like temperature
            
        Returns:
            dict: JSON response from the API
        """
        endpoint = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "system": system,
        }
        
        if options:
            payload.update(options)
        
        response = requests.post(endpoint, json=payload)

        reply = ''
        for data in response.content.split(b'\n'):
            print(data)
            message = json.loads(data)
            if message['done']:
                break

            reply += message['response']
            
        return reply
    
    def list_models(self):
        """List all available models.
        
        Returns:
            dict: JSON response containing available models
        """
        endpoint = f"{self.base_url}/api/tags"
        response = requests.get(endpoint)
        return response.json()
    
    def pull_model(self, model="llama2"):
        """Pull a model from Ollama's registry.
        
        Args:
            model (str): Name of the model to pull
            
        Returns:
            dict: JSON response indicating pull status
        """
        endpoint = f"{self.base_url}/api/pull"
        payload = {"name": model}
        response = requests.post(endpoint, json=payload)
        return response.json()

# Example usage
if __name__ == "__main__":
    ollama = OllamaAPI()
    
    # List available models
    models = ollama.list_models()
    print("Available models:", models)
    
    # Generate text
    response = ollama.generate(
        model="llama3.2:latest",
        prompt="Write a short poem about coding",
        system="You are a helpful AI assistant",
        options={
            "temperature": 0.7,
            "max_tokens": 100
        }
    )
    print("\nGenerated response:", response)