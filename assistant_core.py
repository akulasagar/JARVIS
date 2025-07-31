# --- assistant_core.py ---

import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import os, time, datetime, pyautogui, json
import action_handler
import fitz
import docx

# --- CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyDSk4ejEc1hP4w6ToYWtpw5nzt6Ej_FsiM"
gemini_flash_model = None
gemini_pro_vision_model = None

# --- INITIALIZATION ---
def initialize():
    """Initializes the Gemini models."""
    global gemini_flash_model, gemini_pro_vision_model
    if not (GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE"):
        print(">>> WARNING: The Gemini API key is not set.")
        return False
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_flash_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        gemini_pro_vision_model = genai.GenerativeModel('gemini-1.5-pro-latest')
        print(">>> SUCCESS: Both Gemini models Initialized.")
        return True
    except Exception as e:
        print(f">>> ERROR: Model initialization failed. Exception: {e}")
        return False

# --- AI-POWERED "PLANNER" FOR NON-VISUAL TASKS ---
def _plan_simple_actions(objective):
    """Uses a fast LLM to parse an objective into a structured plan."""
    if not gemini_flash_model: return None
    vision_keywords = ['click', 'find', 'select', 'button', 'icon', 'menu', 'drag']
    if any(keyword in objective.lower() for keyword in vision_keywords): return None
    system_prompt = f"""
You are a task planner. Convert a user's command into a JSON list of known functions.
Your functions: `open_app(app_name)` [options: {list(action_handler.KNOWN_APPLICATIONS.keys())}], `type_text(text)`, `clear_text()`.
If the command requires vision (e.g., 'click'), you MUST return `{{"actions": null}}`.
Example for 'open notpad and type hello': `{{"actions": [{{"function": "open_app", "args": {{"app_name": "notepad"}}}}, {{"function": "type_text", "args": {{"text": "hello"}}}}]}}`
User command: "{objective}"
Your JSON response:
"""
    try:
        print("CORE: Asking planner AI to create a simple action plan...")
        response = gemini_flash_model.generate_content(system_prompt)
        plan = json.loads(response.text.strip().lstrip("```json").rstrip("```"))
        actions = plan.get("actions"); return actions if isinstance(actions, list) else None
    except Exception as e:
        print(f"CORE_PLANNER_ERROR: Could not get a valid plan. {e}"); return None

# --- VISION AGENT: FOR COMPLEX, VISUAL TASKS ---
def _ask_ai_for_next_action(objective, previous_steps, gridded_screenshot):
    """Asks the Vision AI what to do next based on the screen."""
    if not gemini_pro_vision_model: return {"error": "Vision model not configured."}
    print("CORE: Asking Vision AI for on-screen action...")
    history_string = "\n".join(f"- {step}" for step in previous_steps) if previous_steps else "None."
    system_prompt = f"""
You are a precise Windows automation agent. Objective: "{objective}". Prior steps: {history_string}.
Based on the grid, determine the single next action: CLICK(x, y), TYPE(text), or FINISH(reason).
Respond with ONLY a valid JSON object. Example: `{{"action": "CLICK", "args": {{"x": 250, "y": 50}}}}`
"""
    try:
        response = gemini_pro_vision_model.generate_content([system_prompt, gridded_screenshot])
        return json.loads(response.text.strip().lstrip("```json").rstrip("```"))
    except Exception as e:
        error_message = "Vision model connection failed."
        if "quota" in str(e).lower(): error_message = "API usage limits exceeded."
        return {"error": error_message}

# --- MAIN EXECUTION ORCHESTRATOR ---
def execute_on_screen_task(objective):
    """Tries the Planner first, then falls back to the Vision Agent."""
    action_plan = _plan_simple_actions(objective)
    if action_plan:
        print(f"CORE: Executing simple plan: {action_plan}")
        for task in action_plan:
            func_name, args = task.get("function"), task.get("args", {})
            if func_name == "open_app": action_handler.run_local_application(**args)
            elif func_name == "type_text": action_handler.type_text(**args)
            elif func_name == "clear_text": action_handler.clear_text(**args)
        return "I have completed your request."
    print("CORE: Command requires vision. Initializing Vision Agent.")
    max_steps, current_step = 8, 0; steps_history = []
    while current_step < max_steps:
        current_step += 1; print(f"\n--- Vision Agent Step {current_step} ---")
        screenshot_path = action_handler.take_screenshot()
        if not screenshot_path: return "I couldn't see the screen."
        try:
            ai_decision = _ask_ai_for_next_action(objective, steps_history, Image.open(screenshot_path))
            if "error" in ai_decision: return ai_decision["error"]
            action, args = ai_decision.get("action", "").upper(), ai_decision.get("args", {})
            if action == "CLICK": action_handler.click_at_coordinates(**args); time.sleep(3)
            elif action == "TYPE": action_handler.type_text(**args); pyautogui.press('enter'); time.sleep(3)
            elif action == "FINISH": return f"Task complete: {args.get('reason', '')}"
            else: return "AI gave an invalid command. Stopping."
        finally:
            if screenshot_path and os.path.exists(screenshot_path): os.remove(screenshot_path)
    return "Max steps reached. Stopping task."

# --- Helper function for document parsing ---
def _get_doc_text(file_path):
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext == '.pdf':
        with fitz.open(file_path) as doc: return "".join(page.get_text() for page in doc)
    elif file_ext == '.docx':
        doc = docx.Document(file_path); return "\n".join([p.text for p in doc.paragraphs])
    elif file_ext == '.txt':
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: return f.read()
    return None

# --- Standard Chat and File Processing Functions ---
def stream_simple_command(history, command):
    if "what time is it" in command.lower(): yield f"The time is {datetime.datetime.now().strftime('%I:%M %p')}."; return
    if "what's the date" in command.lower(): yield f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."; return
    yield from ask_ai_simple_chat_stream(history, command)

def process_file_command(history, command, file_path):
    try:
        print(f"CORE: Processing file command for '{file_path}'")
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.png', '.jpg', '.jpeg', '.webp']:
            print("CORE: Detected image file.")
            yield from ask_ai_simple_chat_stream(history, command, image=Image.open(file_path))
            return
        doc_text = _get_doc_text(file_path)
        if doc_text is not None:
            print("CORE: Detected document file. Generating response.")
            prompt = f"Based on this document, answer: '{command}'.\n\n{doc_text}"
            if not command or "summarize" in command.lower(): prompt = f"Summary:\n{doc_text}"
            yield from ask_ai_simple_chat_stream(history, prompt)
        else: yield f"I can't read '{os.path.basename(file_path)}' files."; 
    except Exception as e: print(f"CORE_ERROR in process_file_command: {e}"); yield "Error processing file."

def ask_ai_simple_chat_stream(history, new_prompt, image=None):
    model_to_use = gemini_pro_vision_model if image else gemini_flash_model
    if not model_to_use: yield "AI model not configured."; return
    try:
        chat_session = model_to_use.start_chat(history=history)
        content = [new_prompt] if new_prompt else []
        if image:
            content.insert(0, image)
            content.append(new_prompt or "Describe this image.")
        print(f"CORE: Sending content to Gemini model '{model_to_use.model_name}'")
        response_stream = chat_session.send_message(content, stream=True)
        for chunk in response_stream: yield chunk.text
    # --- THIS IS THE FIX ---
    except Exception as e:
        print(f"CORE_ERROR in ask_ai_simple_chat_stream: {e}")
        # Provide a more specific error message to the user.
        error_message = "AI connection error."
        if "quota" in str(e).lower():
            error_message = "I'm sorry, I can't process that right now. It seems I've exceeded my API usage limits for vision tasks."
        yield error_message
    # --- END OF FIX ---