# --- local_llm_handler.py (FINAL AUTH-FIXED VERSION) ---

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import json
import re

# --- Model & Tokenizer References ---
agent_model = None
agent_tokenizer = None
chat_model = None
chat_tokenizer = None

# --- Configuration ---
AGENT_MODEL_ID = "sagar078/gemma-2b-desktop-agent-v1"
CHAT_MODEL_ID = "sagar078/gemma-2b-dolly-dpo-aligned-final"

# --- PASTE YOUR HUGGING FACE "WRITE" TOKEN HERE ---
# This is the key to solving the authentication issue.
# Get your token from: https://huggingface.co/settings/tokens
YOUR_HF_TOKEN = "" # Replace hf_... with your actual token

# In local_llm_handler.py

def initialize_models():
    """Loads both the agent and chat models into memory, with offloading."""
    global agent_model, agent_tokenizer, chat_model, chat_tokenizer

    print(">>> Initializing local LLM Brain... This may take a moment.")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f">>> Using device: {device}")

    # --- PASTE YOUR TOKEN HERE ---
    YOUR_HF_TOKEN = "" # Your actual write token

    try:
        # --- Load the Agent Model (The "Doer") ---
        print(f">>> Loading Agent model: {AGENT_MODEL_ID}")
        agent_tokenizer = AutoTokenizer.from_pretrained(
            AGENT_MODEL_ID,
            token=YOUR_HF_TOKEN
        )
        agent_model = AutoModelForCausalLM.from_pretrained(
            AGENT_MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            offload_folder="./offload_agent",  # <-- Add offload folder
            token=YOUR_HF_TOKEN
        )
        print(">>> SUCCESS: Agent model loaded.")

        # --- Load the Chat Model (The "Communicator") ---
        print(f">>> Loading Chat model: {CHAT_MODEL_ID}")
        chat_tokenizer = AutoTokenizer.from_pretrained(
            CHAT_MODEL_ID,
            token=YOUR_HF_TOKEN
        )
        chat_model = AutoModelForCausalLM.from_pretrained(
            CHAT_MODEL_ID,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            offload_folder="./offload_chat",  # <-- Add offload folder
            token=YOUR_HF_TOKEN
        )
        print(">>> SUCCESS: Chat model loaded.")

        return True

    except Exception as e:
        print(f">>> CRITICAL ERROR: Failed to load models. {e}")
        return False

def get_agentic_action_json(system_prompt: str) -> str:
    """
    Takes the full system prompt and returns a single JSON object with the next action.
    This function is designed to replace the Gemini call in `process_agentic_task`.
    """
    if not agent_model or not agent_tokenizer:
        raise ConnectionError("Agent model is not initialized.")

    objective_match = re.search(r"\*\*USER'S OBJECTIVE:\*\*\s*(.*)", system_prompt)
    history_match = re.search(r"\*\*ACTION HISTORY & OBSERVATIONS:\*\*\n(.*?)--- TOOLKIT", system_prompt, re.DOTALL)

    objective = objective_match.group(1).strip() if objective_match else "No objective found."
    history = history_match.group(1).strip() if history_match else "No history."

    input_text = f"""
INSTRUCTION: You are a PC control assistant. Your goal is to achieve the following objective.
OBJECTIVE: {objective}

Given the history of actions and observations, decide the single best tool to use next.
Your response MUST be a single, valid JSON object with "action" and "args" keys.

HISTORY:
{history}

JSON_RESPONSE:
"""

    print(">>> Sending request to local AGENT model...")
    inputs = agent_tokenizer(input_text, return_tensors="pt").to(agent_model.device)

    outputs = agent_model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=False,
        pad_token_id=agent_tokenizer.eos_token_id
    )

    response_text = agent_tokenizer.decode(outputs[0], skip_special_tokens=True)
    json_part = response_text.split("JSON_RESPONSE:")[-1].strip()
    return json_part

def stream_chat_response(history, command):
    """
    Takes a conversation history and a new command, and yields the response chunks.
    This replaces `stream_simple_command`.
    """
    if not chat_model or not chat_tokenizer:
        raise ConnectionError("Chat model is not initialized.")

    chat_template_history = []
    for message in history:
        if message['parts'][0] != command:
             chat_template_history.append({"role": "model" if message['role'] == "model" else "user", "content": message['parts'][0]})

    chat_template_history.append({"role": "user", "content": command})

    prompt = chat_tokenizer.apply_chat_template(
        chat_template_history,
        tokenize=False,
        add_generation_prompt=True
    )

    print(">>> Sending request to local CHAT model...")
    inputs = chat_tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(chat_model.device)

    outputs = chat_model.generate(**inputs, max_new_tokens=512, pad_token_id=chat_tokenizer.eos_token_id)
    full_response = chat_tokenizer.decode(outputs[0], skip_special_tokens=True)

    response_only = full_response.split('[/INST]')[-1].strip()

    for word in response_only.split():
        yield word + " "