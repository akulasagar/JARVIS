# --- assistant_core.py (The Final, Transplanted Version) ---

# CHANGE: We now import our local brain handler instead of Gemini.
import local_llm_handler

import os
import time
import datetime
import json
import re
import action_handler

# --- Configuration & Initialization ---

# CHANGE: This function now initializes our local models.
def initialize():
    """Initializes the connection to the local LLMs."""
    return local_llm_handler.initialize_models()

# CHANGE: This function now gets conversational responses from our local chat model.
def stream_simple_command(history, command):
    """Handles simple, conversational commands using the local chat model."""
    print(f"Sending simple chat command to Local LLM: '{command}'")
    try:
        # The new handler will yield the response chunks
        yield from local_llm_handler.stream_chat_response(history, command)
    except Exception as e:
        print(f"CORE_ERROR in stream_simple_command: {e}")
        yield "Sorry, I'm having trouble with my local AI brain right now."

def process_agentic_task(objective: str) -> str:
    """Uses a local agent model for reasoning and a dedicated local toolkit."""
    thought_history = [f"OBJECTIVE: {objective}\n"]
    max_steps = 20
    
    for i in range(max_steps):
        print(f"\n--- Agent Execution Step {i+1}/{max_steps} ---")
        
        # NOTE: The system prompt remains the same, as our handler is designed to parse it.
        system_prompt = f"""
You are the reasoning core of a general-purpose PC control assistant. Your task is to analyze the user's objective and the history of actions to decide the single next logical step.

**USER'S OBJECTIVE:** {objective}
**ACTION HISTORY & OBSERVATIONS:**
{''.join(thought_history)}

--- TOOLKIT & CRITICAL RULES ---
**RULE 1: You MUST ONLY use the exact action names from the TOOLKIT below. Do NOT invent actions like 'send' or 'type_text'.**
**RULE 2: To send a message or submit a search after typing, you MUST use the `PRESS_KEY` action with the `key` parameter set to `'enter'`.**

**TOOLKIT (The ONLY allowed actions):**
- `search_and_open_app(app_name: str)`: Use for local apps like 'WhatsApp', 'Notepad'.
- `open_url(url: str)`: Use for websites like 'https://www.google.com'.
- `LIST_OPEN_WINDOWS()`: Gets the titles of all open windows.
- `GET_WINDOW_ELEMENTS(window_title: str)`: Inspects a window to see its controls.
- `INTERACT_WITH_ELEMENT(window_title: str, action: str, element_title: str = None, control_type: str = None, value: str = "")`: Use this to 'click' or 'type'.
- `PRESS_KEY(window_title: str, key: str)`: Use this for single keys like 'enter'.
- `FINISH(reason: str)`: Use this when the entire objective is complete.

--- MASTER STRATEGY ---
1.  **Opening:** First, decide if the target is a website or a local app, and use the correct tool (`open_url` or `search_and_open_app`).
2.  **Re-evaluating:** After any major `click` or `PRESS_KEY` action, use `GET_WINDOW_ELEMENTS` to see the new screen state.

Based on this strategy and the critical rules, what is the single best action from the TOOLKIT to take NEXT? Respond with only a valid JSON object.
"""
        
        # --- THIS IS THE BRAIN TRANSPLANT ---
        # The old try/except block that called Gemini is replaced with this new one.
        try:
            print("ACTION: Sending request to Local Agent for next logical action...")
            # CHANGE: This is the key line. We call our local handler instead of Gemini.
            response_text = local_llm_handler.get_agentic_action_json(system_prompt)

            # The rest of the parsing logic is the same, as it's designed to find JSON.
            json_match = re.search(r"```json\s*(\{.*?\})\s*```|(\{.*?\})", response_text, re.DOTALL | re.S)
            if not json_match: raise ValueError(f"No JSON object found in response: {response_text}")
            json_string = json_match.group(1) if json_match.group(1) else json_match.group(2)
            decision_json = json.loads(json_string)
            
            def lower_keys(x):
                if isinstance(x, dict): return {k.lower(): lower_keys(v) for k, v in x.items()}
                return x
            
            decision_json_lower = lower_keys(decision_json)
            action = decision_json_lower.pop("action", None)
            if not action: raise ValueError("AI response JSON missing 'action' key.")
            action = action.strip().replace("()", "")

            args = {}
            if 'args' in decision_json_lower and isinstance(decision_json_lower.get('args'), dict):
                args.update(decision_json_lower['args'])
            else:
                args.update(decision_json_lower)
            
            print(f"AI Response:\n{response_text}")
            print(f"Parsed Decision: Action='{action}', Args='{args}'")

        except Exception as e:
            # CHANGE: The error message now reflects a problem with the local model.
            print(f"AGENT_ERROR: Could not get decision from local model. Error: {e}")
            thought_history.append(f"Observation: AI reasoning failed with error: {e}\n")
            time.sleep(3); continue
        
        # --- END OF BRAIN TRANSPLANT ---
        
        observation = ""
        action_upper = action.upper()
        
        # The action execution logic remains unchanged.
        try:
            if action_upper == "SEARCH_AND_OPEN_APP":
                observation = action_handler.search_and_open_app(**args)
            elif action_upper == "OPEN_URL":
                observation = action_handler.open_url(**args)
            elif action_upper == "LIST_OPEN_WINDOWS":
                observation = action_handler.list_open_windows(**args)
            elif action_upper == "GET_WINDOW_ELEMENTS":
                observation = action_handler.get_window_elements(**args)
            elif action_upper == "INTERACT_WITH_ELEMENT":
                observation = action_handler.interact_with_element(**args)
            elif action_upper == "PRESS_KEY":
                 observation = action_handler.press_key(**args)
            elif action_upper == "FINISH":
                print("AGENT: Master plan complete.")
                return args.get("reason", "Objective complete.")
            else:
                observation = f"Attempted an unknown action: '{action}'."
        except Exception as e:
            observation = f"Error executing action {action_upper}: {e}"
            
        print(f"Action Result: {observation}")
        thought_history.append(f"Action: {action.upper()} with args {args}. Result:\n---\n{observation}\n---\n")

        if "Error" not in observation:
            time.sleep(2)
        else:
            time.sleep(3) 

    return "Task failed: reached maximum number of steps."