import json
import requests
from database import get_user, update_user_facts

def perform_google_search(query, api_key, engine_id):
    if not api_key or not engine_id:
        return "Search configuration missing."

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": engine_id,
        "num": 3
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("items", []):
            title = item.get("title", "No title")
            snippet = item.get("snippet", "No snippet")
            link = item.get("link", "")
            results.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}")

        return "\n\n".join(results)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Search failed: {e}"
        try:
            # Try to parse the JSON error response
            if e.response is not None:
                error_data = e.response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_msg = f"Search failed: {error_data['error']['message']}"
        except:
            pass

        # Log the full error with masked key for debugging
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "..."
        print(f"[ERROR] Google Search failed. URL: {url}?q={query}&key={masked_key}&cx={engine_id}&num=3")
        print(f"[ERROR] Response: {e.response.text if e.response is not None else 'No response'}")
        return error_msg
    except Exception as e:
        print(f"[ERROR] Search failed: {e}")
        return f"Search failed: {e}"

def extract_user_facts(message, user, config):
    prompt = f"Analyze the following message from user '{user}'. Identify if there are any permanent or semi-permanent facts about the user (e.g., location, profession, age, pets, hobbies, hardware specs, recurring problems). Ignore transient states or opinions. Return a JSON object with a key 'facts' containing a list of strings, or an empty list if no facts are found. ONLY return the JSON object, no other text. Message: {message}"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config['gemini_api_key']}"
    headers = {"Content-Type": "application/json"}
    data = {"contents":[{"parts":[{"text": prompt}]}]}

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        r.raise_for_status()
        resp = r.json()

        text_parts = []
        if "candidates" in resp:
            content = resp["candidates"][0].get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                if "text" in part:
                    text_parts.append(part["text"])

        response_text = " ".join(text_parts).strip()

        # Strip markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        response_json = json.loads(response_text.strip())
        facts = response_json.get("facts", [])
        if facts:
            update_user_facts(user, facts)
            print(f"[FACTS] Updated facts for {user}: {facts}")
    except Exception as e:
        # It's expected that many messages won't have facts or won't parse correctly, so just log debug
        print(f"[DEBUG] Fact extraction failed or no facts: {e}")

def generate_ai_response(prompt: str, user, config, context_monitor=None) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={config['gemini_api_key']}"
    headers = {
        "Content-Type": "application/json",
    }

    user_data = get_user(user)
    favouritism_score = user_data["favouritism_score"] if user_data else 0

    # Get user facts
    user_facts = []
    if user_data and user_data["facts"]:
        try:
            user_facts = json.loads(user_data["facts"])
        except:
            pass

    facts_str = ""
    if user_facts:
        facts_str = f"\nKnown facts about {user}: {', '.join(user_facts)}"

    # Get spoken context from monitor
    spoken_context = ""
    if context_monitor:
         streamer_name = config["channels"][0] if config.get("channels") else "the streamer"
         spoken_context = f"\nRecent spoken context (spoken by {streamer_name}):\n{context_monitor.get_context()}\n"

    personality_prompt = f"Respond in personality: {config['personality']}. Keep your response concise (ideally under 450 characters) so it fits in Twitch chat, unless asked otherwise."
    if "personality_traits" in config:
        likes = ", ".join(config["personality_traits"].get("likes", []))
        if likes:
            personality_prompt += f"\nLikes: {likes}"
        dislikes = ", ".join(config["personality_traits"].get("dislikes", []))
        if dislikes:
            personality_prompt += f"\nDislikes: {dislikes}"

    prompt_with_context = f"{personality_prompt}{spoken_context}\nUser '{user}' has a favouritism score of {favouritism_score}.{facts_str}\n{prompt}"
    data = {"contents":[{"parts":[{"text": prompt_with_context}]}]}

    try:
        r = requests.post(url, headers=headers, json=data, timeout=10)
        r.raise_for_status()
        resp = r.json()

        # Parse Gemini Flash response
        text_parts = []
        candidates = resp.get("candidates", [])
        if candidates:
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                if "text" in part:
                    text_parts.append(part["text"])
        text = " ".join(text_parts).strip()
        if not text:
            print("[ERROR] Gemini response empty, full JSON:", resp)
            return "Hmm… I couldn't come up with a response!"

        # Removed hard truncation to prevent cutting off sentences.
        # The bot's message sender handles chunking long messages.

        return text
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}, full response: {r.text if 'r' in locals() else 'no response'}")
        return "Hmm… I couldn't come up with a response!"
