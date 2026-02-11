"""Centralized LLM interface using Ollama."""
import requests
from .config import Config


def call_llm(
    prompt: str,
    system_prompt: str = "",
    model: str = None,
    temperature: float = None,
    stream: bool = False
) -> str:
    """
    Generic LLM caller for Ollama.
    Returns ONLY the model text response.
    
    Args:
        prompt: The user prompt
        system_prompt: Optional system prompt
        model: Model name (defaults to Config.DEFAULT_MODEL)
        temperature: Temperature setting (defaults to Config.DEFAULT_TEMPERATURE)
        stream: Whether to stream response
        
    Returns:
        The model's text response
    """
    model = model or Config.DEFAULT_MODEL
    temperature = temperature if temperature is not None else Config.DEFAULT_TEMPERATURE

    payload = {
        "model": model,
        "stream": stream,
        "messages": [],
        "options": {
            "temperature": temperature
        }
    }

    if system_prompt:
        payload["messages"].append({
            "role": "system",
            "content": system_prompt
        })

    payload["messages"].append({
        "role": "user",
        "content": prompt
    })

    response = requests.post(
        Config.OLLAMA_URL, 
        json=payload, 
        timeout=Config.LLM_TIMEOUT
    )
    response.raise_for_status()

    data = response.json()

    if "message" not in data:
        raise RuntimeError(f"Unexpected Ollama response: {data}")

    return data["message"]["content"].strip()
