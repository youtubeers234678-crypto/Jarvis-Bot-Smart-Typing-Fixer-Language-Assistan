import time
import threading
import json
from pynput import keyboard
from pynput.keyboard import Controller, Key
import pyperclip
import requests
import os
import re

# --- Configuration ---
API_KEYS = [
    "25d09d44ed14faa386bc4e299496bf2c", 
    " use open router api key "
]

TWITTER_CREDENTIALS = {
    "consumer_key": "mSc6m4f93IGyQuiwJdkqDUpit",
    "consumer_secret": "7lcO7J3Z9MlIl0jo36J6Naokk8sEgkYBGniPmX8q0CdNKU1FDB",
    "bearer_token": "AAAAAAAAAAAAAAAAAAAAAH%2BV9QEAAAAAcPYlJElrZ7Lj1VvSGsl6bOIMai4%3DE44OSASJiRiPka8HEoyja7Ee0MjR55NuhYUcWNOxCxVkCfkpW8"
}
MEMORY_FILE = "memory_recorder.json"
MEMORY_FILE = "memory_recorder.json" # Local storage database (No Firebase)

# Google Search API Config
GOOGLE_API_KEY = "https://cse.google.com/cse?cx=675c08b4ceeb5492" # Yahan apni asli API Key dalein
GOOGLE_SEARCH_ID = "675c08b4ceeb54928"              # Sirf ID rehne dein, URL hata dein
GOOGLE_API_KEY = "" # Yahan apni Google Cloud API Key dalein (AIza...)
GOOGLE_SEARCH_ID = "675c08b4ceeb54928"

class JarvisSmartBot:
    def __init__(self):
        self.keyboard_ctrl = Controller()
        self.last_type_time = time.time()
        self.idle_threshold = 2.5 
        self.min_text_length = 3
        self.processing = False
        self.last_processed_text = ""
        self.user_typed_new = False
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.enabled = True  # Bot status flag
        self.memory = self.load_memory()
        print("[System] Platform fully disconnected from Firebase cloud dependencies.")
        print("[System] Utilizing high-performance local JSON persistence.")

    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_to_memory(self, question, answer):
        self.memory[question.lower()] = answer
        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=4)
        except Exception as e:
            print(f"[Jarvis Memory Error] {e}")

    def google_search(self, query):
        """Fetches live information from the web."""
        if "YOUR_ACTUAL" in GOOGLE_API_KEY or len(GOOGLE_API_KEY) < 10:
            return ""
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_SEARCH_ID,
            "q": query,
            "num": 3  # Top 3 results
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            results = response.json()
            search_context = ""
            if "items" in results:
                for item in results["items"]:
                    search_context += f"Title: {item['title']}\nLink: {item['link']}\nSnippet: {item['snippet']}\n\n"
            return search_context
        except Exception as e:
            print(f"[Jarvis Search Error] {e}")
            return ""

    def get_smart_fix(self, text):
        clean_text = text.strip()
        
        # Check for translation trigger (starts with .)
        is_translation = clean_text.startswith('.')
        # Check if text contains a question in brackets like {how are you}
        is_question = ('{' in clean_text or '[' in clean_text) and ('}' in clean_text or ']' in clean_text)
        # Check if user wants a deep, long explanation
        is_full_explain = is_question and "full explain" in clean_text.lower()

        # Check if user is asking for AI's info or functions
        info_keywords = ["ai info", "apni info", "about yourself", "kaun ho", "who are you", "your functions", "kia kaam kera ho", "info batao", "intro"]
        is_info_request = any(k in clean_text.lower() for k in info_keywords)

        if clean_text.lower() in self.memory:
            return self.memory[clean_text.lower()]

        web_info = ""
        if is_question or is_full_explain:
            # Extract the query inside brackets
            match = re.search(r'[\{\[](.*?)[\}\]]', clean_text)
            query = match.group(1) if match else clean_text
            print(f"[Jarvis] Searching web for: {query}")
            web_info = self.google_search(query)

        if is_translation:
            source_text = clean_text[1:].strip()
            prompt = (f"Translate the following text into natural Roman Urdu (conversational style): '{source_text}'. "
                      f"CRITICAL: Every Single Word's First Letter Must Be Capitalized. "
                      f"Use expressive emojis. Return ONLY the translated text, no explanations.")
        elif is_full_explain:
            prompt = (f"The user is asking for a DEEP and LONG professional explanation for: '{clean_text}'. "
                      f"CONTEXT FROM WEB:\n{web_info}\n\n"
                      f"Find the question inside the brackets, ignore 'full explain', and provide a LONG, DETAILED response in the SAME LANGUAGE as the query using the web info if available. "
                      f"CRITICAL: Every Single Word's First Letter Must Be Capitalized. "
                      f"Use professional and expressive emojis. Return ONLY the long detailed answer.")
        elif is_question:
            prompt = (f"In this message: '{clean_text}', find the question inside the brackets (like {{}} or []). "
                      f"CONTEXT FROM WEB:\n{web_info}\n\n"
                      f"REPLACE that entire bracketed part with an informative and deep professional answer in the SAME LANGUAGE as the surrounding text based on web context. "
                      f"If the user needs a link, include the most relevant link from the context. "
                      f"KEEP all text outside the brackets exactly as it is. "
                      f"CRITICAL: Do NOT include the original question or the brackets in your response. "
                      f"Every Single Word's First Letter Must Be Capitalized. "
                      f"Use expressive emojis. Return ONLY the resulting merged sentence.")
        elif is_info_request:
            prompt = (f"The user is asking for information about you (the AI). "
                      f"Provide a full explanation of your identity as 'Jarvis Bot' and your functions (typo correction in any language, web search via brackets {{}} or [], translation to Roman Urdu via dot ., and detailed explanations with 'full explain'). "
                      f"Provide this explanation in the SAME LANGUAGE as the user's query: '{clean_text}'. "
                      f"CRITICAL: Every Single Word's First Letter Must Be Capitalized. "
                      f"Use professional and expressive emojis. Return ONLY the full explanation.")
        else:
            # Standard correction logic
            prompt = (f"Correct any typing or spelling mistakes in the provided text. "
                      f"Maintain the ORIGINAL LANGUAGE and a natural conversational tone. Add relevant emojis to make it expressive. "
                      f"CRITICAL: Every Single Word's First Letter Must Be Capitalized. "
                      f"Example for Roman Urdu: 'kya hal hy' -> 'Kya Haal Hai? 😊'. Example for English: 'how r u' -> 'How Are You? 😊'. "
                      f"Return ONLY the corrected text in the original language, no explanations: {clean_text}")
        
        for key in API_KEYS:
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost", 
                "X-Title": "Jarvis Bot"
            }
            data = {
                "model": "google/gemini-2.0-flash-001",
                "messages": [{"role": "user", "content": prompt}]
            }
            
            try:
                response = requests.post(self.api_url, headers=headers, json=data, timeout=15)
                response_data = response.json()

                if 'choices' in response_data:
                    result = response_data['choices'][0]['message']['content'].strip()
                    self.save_to_memory(clean_text, result)
                    return result
                else:
                    print(f"[Jarvis] API Key issue, trying next key...")
                    continue
            except Exception as e:
                print(f"[Jarvis Request Error] {e}")
                continue
        
        return clean_text

    def monitor(self):
        while True:
            time.sleep(0.5)
            if self.user_typed_new and (time.time() - self.last_type_time > self.idle_threshold) and not self.processing:
                self.process_text()

    def process_text(self):
        self.processing = True
        
        # Select all text using Ctrl+A to handle multi-line input
        with self.keyboard_ctrl.pressed(Key.ctrl):
            self.keyboard_ctrl.tap('a')
        time.sleep(0.1)
        
        time.sleep(0.3)
        pyperclip.copy("") # Clear clipboard
        with self.keyboard_ctrl.pressed(Key.ctrl):
            self.keyboard_ctrl.tap('c')
        
        time.sleep(0.5)
        input_text = pyperclip.paste().strip()

        # Handle On/Off commands
        if input_text.lower() == "on tp":
            self.enabled = True
            print("[Jarvis] System Activated: Normal working started.")
        elif input_text.lower() == "off tp":
            self.enabled = False
            print("[Jarvis] System Deactivated: Running in background (No changes).")
        elif input_text.lower() == "exit" or input_text.lower() == "stop bot":
            print("[Jarvis] System Shutting Down...")
            os._exit(0)
            return

        # Only process text if enabled and it's not a status command
        if not self.enabled:
            input_text = "" # Skip further processing

        if len(input_text) >= self.min_text_length and input_text != self.last_processed_text:
            print(f"[Jarvis] Processing: {input_text}")
            refined_text = self.get_smart_fix(input_text)
            
            if refined_text.lower() != input_text.lower():
                pyperclip.copy(refined_text)
                with self.keyboard_ctrl.pressed(Key.ctrl):
                    self.keyboard_ctrl.tap('v')
                print(f"[Jarvis] Fixed: {refined_text}")
                
                self.last_processed_text = refined_text
        
        self.user_typed_new = False
        self.processing = False

    def on_press(self, key):
        if not self.processing:
            self.last_type_time = time.time()
            self.user_typed_new = True

# --- Start ---
bot = JarvisSmartBot()
print("[Jarvis] Roman Urdu Typo-Fixer Active. Waiting for idle typing...")

threading.Thread(target=bot.monitor, daemon=True).start()

with keyboard.Listener(on_press=bot.on_press) as listener:
    listener.join() 
