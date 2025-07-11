import os
import json
import aiohttp
import asyncio
import traceback
from dotenv import load_dotenv
from tool_definitions import get_tools

load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION")

async def get_chat_response_stream(prompt: str, dynamic_tools: list = None):
    """
    A unified function to handle streaming responses that could be text or tool calls.
    This makes a single call to Azure OpenAI with a dynamic list of tools.
    """
    request_body = {
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    # Add tools if provided
    if dynamic_tools:
        request_body["tools"] = dynamic_tools
        request_body["tool_choice"] = "auto"
    
    async for result in _make_openai_request(request_body):
        yield result

async def get_chat_response_stream_with_messages(messages: list, dynamic_tools: list = None):
    """
    A unified function to handle streaming responses with full conversation history.
    This makes a call to Azure OpenAI with a messages array and dynamic list of tools.
    """
    request_body = {
        "messages": messages,
        "stream": True,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    # Add tools if provided
    if dynamic_tools:
        request_body["tools"] = dynamic_tools
        request_body["tool_choice"] = "auto"
    
    async for result in _make_openai_request(request_body):
        yield result

async def _make_openai_request(request_body: dict):
    """
    Shared function to make Azure OpenAI API requests with streaming.
    """
    # Construct Azure OpenAI URL
    full_url = f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT}/chat/completions?api-version={AZURE_API_VERSION}"
    
    headers = {
        "api-key": AZURE_OPENAI_API_KEY,
        "Content-Type": "application/json",
    }

    try:
        # Create session with timeout
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print(f"--- CALLING AZURE OPENAI API ---: {full_url}")
            print(f"--- REQUEST BODY ---: {json.dumps(request_body, indent=2)}")
            
            async with session.post(url=full_url, headers=headers, json=request_body) as response:
                print(f"--- RESPONSE STATUS ---: {response.status}")
                print(f"--- RESPONSE HEADERS ---: {dict(response.headers)}")
                
                if response.status != 200:
                    error_text = await response.text()
                    print(f"--- ERROR RESPONSE ---: {error_text}")
                    yield {"error": f"Azure OpenAI API error {response.status}: {error_text}"}
                    return
                
                response.raise_for_status()

                buffer = b""
                async for chunk in response.content.iter_chunked(1024):
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        line = line.strip()
                        if line.startswith(b"data: "):
                            data_str = line[len(b"data: "):].strip()
                            if data_str == b"[DONE]":
                                print("--- STREAM COMPLETED ---")
                                return
                            if data_str:  # Skip empty data lines
                                try:
                                    parsed_data = json.loads(data_str)
                                    # Log content and tool calls
                                    choices = parsed_data.get("choices", [])
                                    if choices:
                                        delta = choices[0].get("delta", {})
                                        content = delta.get("content")
                                        tool_calls = delta.get("tool_calls")
                                        
                                        if content:
                                            print(f"--- BACKEND PARSED CONTENT ---: '{content}'")
                                        if tool_calls:
                                            print(f"--- BACKEND PARSED TOOL CALLS ---: {tool_calls}")
                                    
                                    yield parsed_data
                                except json.JSONDecodeError as json_err:
                                    print(f"--- JSON DECODE ERROR ---: {json_err} for data: {data_str}")
                                    continue
    except aiohttp.ClientError as e:
        print(f"--- AIOHTTP CLIENT ERROR ---: {e}")
        traceback.print_exc()
        yield {"error": f"Connection error: {e}"}
    except Exception as e:
        print(f"--- UNEXPECTED ERROR ---: {e}")
        traceback.print_exc()
        yield {"error": "Sorry, an error occurred while processing your request."}

async def perform_semantic_search(query: str, index: str, field_with_semantic_text: str):
    """Performs a semantic search using ELSER."""
    from es_client import es_client
    
    if not es_client:
        raise Exception("Elasticsearch client not configured")
    
    resp = await es_client.search(
        index=index,
        query={
            "text_expansion": {
                field_with_semantic_text: {
                    "model_id": "elser-adaptive-endpoint",
                    "model_text": query
                }
            }
        }
    )
    return [
        {"id": hit["_id"], "score": hit["_score"], **hit["_source"]}
        for hit in resp["hits"]["hits"]
    ]
