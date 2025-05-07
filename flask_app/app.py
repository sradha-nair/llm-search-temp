from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import requests
from openai import OpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(_name_)

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "running"}), 200

@app.route("/api/search", methods=["POST"])
def search():
    try:
        data = request.get_json()
        query = data.get("query", "")

        search_results = perform_search(query)
        combined = concatenate_content(search_results)
        response = generate_response(query, combined)

        return jsonify({
            "response": response,
            "sources": search_results
        })

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Internal Server Error"}), 500

def perform_search(query):
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json={"q": query})
    response.raise_for_status()
    data = response.json()
    return [item["link"] for item in data.get("organic", [])]

def concatenate_content(urls):
    return "\n".join([f"Content from {url}" for url in urls])

def generate_response(query, context):
    prompt = f"Answer the following question based on the provided context:\n\nContext: {context}\n\nQuestion: {query}\nAnswer:"
    completion = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )
    return completion.choices[0].message.content.strip()

if _name_ == "_main_":
    app.run(host="0.0.0.0", port=5000)
