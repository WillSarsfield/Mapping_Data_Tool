import requests

def get_insight(visualisation, topic, data_dict):

    OLLAMA_URL = "http://localhost:11434/api/generate"

    payload = {
        "model": "deepseek-r1",
        "prompt": f"give brief insights into the following data: {data_dict}, in the context of a paragraph that is situated beneath a {visualisation} titled {topic} that uses this data",
        "stream": False,
        "temparature": 0.1
    }

    response = requests.post(OLLAMA_URL, json=payload)
    full_text = response.json()["response"]

    # Remove prior reasoning
    cleaned_text = full_text.split("</think>")[-1].strip()
    return cleaned_text