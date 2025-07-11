import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.client import InferenceClient # Keep this import for your version

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

# --- Initialize Inference Client ---
inference_client = InferenceClient(client)

# --- Define chat messages ---
messages_payload = [
    {"role": "user", "content": "What is Elastic?"}
]

print(f"\nSending chat completion request to inference ID: {INFERENCE_ID}\n")
print("Streaming response:")

# --- Perform chat completion inference ---
# CORRECTED: Use inference_client.inference_stream() for chat_completion
try:
    for chunk in inference_client.inference_stream( # <-- KEY CHANGE HERE
        inference_id=INFERENCE_ID,
        task_type="chat_completion",
        body={
            "model": "gpt-4o", # Specify the model if your deployed inference service requires it
            "messages": messages_payload
        }
        # No 'stream=True' needed here, as inference_stream() inherently streams
    ):
        # Process each chunk of the streaming response
        if chunk and 'choices' in chunk and len(chunk['choices']) > 0:
            choice = chunk['choices'][0]
            # Check for 'delta' for ongoing streams or 'content' for final/complete chunks
            if 'delta' in choice and 'content' in choice['delta']:
                print(choice['delta']['content'], end='')
            elif 'content' in choice:
                print(choice['content'], end='')
        # Handle cases where the chunk might be an event/status update, not directly text
        elif chunk and 'event' in chunk:
            # print(f"\n[INFO: Received event: {chunk['event']}]\n", end='')
            pass # Or handle event messages as needed

    print("\n\nStreaming complete.")

except Exception as e:
    print(f"\nError during chat completion: {e}")
