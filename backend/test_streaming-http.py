import os
import json
from dotenv import load_dotenv
from elasticsearch import Elasticsearch

# --- Load environment variables from .env file ---
load_dotenv()

# --- Configuration ---
ES_ENDPOINT_URL = os.getenv("ES_ENDPOINT_URL")
ES_API_KEY = os.getenv("ES_API_KEY")
INFERENCE_ID = ".rainbow-sprinkles-elastic" # Hardcoded as per your setup

# --- Validate Configuration ---
if not ES_ENDPOINT_URL:
    print("Error: ES_ENDPOINT_URL not found in .env file.")
    exit()
if not ES_API_KEY:
    print("Error: ES_API_KEY not found in .env file.")
    exit()

# --- Initialize Elasticsearch Client ---
try:
    client = Elasticsearch(
        hosts=[ES_ENDPOINT_URL],
        api_key=ES_API_KEY
    )
    if client.ping():
        print("Successfully connected to Elasticsearch!")
    else:
        print("Could not connect to Elasticsearch. Check your URL and API Key.")
        exit()

except Exception as e:
    print(f"Error connecting to Elasticsearch: {e}")
    exit()

# --- Define chat messages payload ---
messages_payload = [
    {"role": "user", "content": "Tell me a short story about a brave knight and a dragon."}
]

print(f"\nSending direct streaming request to inference ID: {INFERENCE_ID}\n")
print("Streaming response:")

# --- Prepare the request body as a dictionary ---
request_body = {
    "model": "gpt-4o", # Specify the model if your deployed inference service requires it
    "messages": messages_payload
}

# --- Define the endpoint path for streaming chat completion ---
# CORRECTED: chat_completion comes before the INFERENCE_ID
endpoint_path = f"/_inference/chat_completion/{INFERENCE_ID}/_stream"
print(endpoint_path)

# --- Make the low-level HTTP call to _stream API ---
try:
    raw_response_generator = client.transport.perform_request(
        "POST",          # Positional argument for HTTP method
        endpoint_path,   # Positional argument for the URL path
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream" # Crucial header for Server-Sent Events
        },
        body=json.dumps(request_body), # Request body needs to be a JSON string
    #    stream=True # This tells elasticsearch-py to yield raw bytes chunks
    )

    # --- Parse and process the Server-Sent Events (SSE) ---
    buffer = ""
    done_streaming = False # Flag to signal completion across loops

    for chunk_bytes in raw_response_generator:
        print(chunk_bytes)
        chunk_str = chunk_bytes.decode('utf-8')
        buffer += chunk_str

        while "\n\n" in buffer:
            event_str, buffer = buffer.split("\n\n", 1)

            lines = event_str.split("\n")
            data_lines = [line[len("data: "):] for line in lines if line.startswith("data: ")]

            for data_line in data_lines:
                if data_line.strip() == "[DONE]":
                    print("\n\nStreaming complete.")
                    done_streaming = True
                    break

                try:
                    event_data = json.loads(data_line)
                    if event_data and 'choices' in event_data and len(event_data['choices']) > 0:
                        choice = event_data['choices'][0]
                        if 'delta' in choice and 'content' in choice['delta']:
                            print(choice['delta']['content'], end='')
                        elif 'content' in choice:
                            print(choice['content'], end='')
                    elif 'event' in event_data:
                        pass

                except json.JSONDecodeError:
                    pass

            if done_streaming:
                break

        if done_streaming:
            break

except Exception as e:
    print(f"\nError during direct HTTP call for chat completion: {e}")
    raise
