import os
import re
import json
import webbrowser
import subprocess
import difflib
import shutil
import urllib.parse
import speech_recognition as sr
import pyttsx3
import pyautogui
import time
# import wikipedia


APPS_FILE = "config_apps.json"
PROJECTS_FILE = "config_projects.json"

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2)
        return default


DEFAULT_APPS = {}
DEFAULT_PROJECTS = {}

apps = load_json(APPS_FILE, DEFAULT_APPS)
projects = load_json(PROJECTS_FILE, DEFAULT_PROJECTS)


engine = pyttsx3.init()
def speak(text: str):
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass

def listen() -> str:
    r = sr.Recognizer()
    r.dynamic_energy_threshold = True
    try:
        with sr.Microphone() as source:
            print("Listening...")
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
        return r.recognize_google(audio, language="en-US")
    except sr.WaitTimeoutError:
        print("Listening timed out")
        return ""
    except Exception as e:
        print("Error listening:", e)
        return ""


# def wiki_search(query: str):
#     try:
#         summary = wikipedia.summary(query, sentences=2)
#         speak(summary)
#         print(summary)
#     except Exception:
#         speak("Sorry, I couldn't fetch from Wikipedia")



def fuzzy_get_key(user_text: str, keys):

    user_text = user_text.strip().lower()
    if user_text in keys:
        return user_text
    compact = user_text.replace(" ", "")
    for k in keys:
        if k.replace(" ", "") == compact:
            return k
    matches = difflib.get_close_matches(user_text, keys, n=1, cutoff=0.55)
    return matches[0] if matches else None

def run_cmd(target: str):
    subprocess.Popen(f'start "" {target}', shell=True)

def open_app(app_name: str):
    key = fuzzy_get_key(app_name, list(apps.keys()))
    if not key:
        speak(f"I couldn't find {app_name} in your apps list")
        print(f"[open_app] No match for: {app_name}")
        return

    entry = apps[key]
    kind = entry.get("kind","cmd")
    target = entry.get("target","")

    print(f"[open_app] Opening '{key}' via {kind}: {target}")

    try:
        if kind == "url":
            webbrowser.open(target)
        elif kind == "path":
            os.startfile(target)
        elif kind == "cmd":
            run_cmd(target)
        elif kind == "uwp":
            os.system(f'start shell:AppsFolder\\{target}')
        else:
            os.startfile(target)
        speak(f"Opening {key}")
    except Exception as e:
        speak("Failed to open")
        print("Error:", e)

def open_project(project_alias: str, in_code: bool=False):
    key = fuzzy_get_key(project_alias, list(projects.keys()))
    if not key:
        speak(f"I couldn't find project {project_alias}")
        print(f"[open_project] No match for: {project_alias}")
        return

    path = projects[key]
    print(f"[open_project] Opening project '{key}': {path}. In code: {in_code}")

    try:
        if in_code:
            if shutil.which("code"):
                subprocess.Popen(f'start "" code "{path}"', shell=True)
                speak(f"Opening {key} in VS Code")
            else:
                os.startfile(path)
                speak(f"VS Code not found on PATH. Opened {key} folder instead.")
        else:
            os.startfile(path)
            speak(f"Opening {key} folder")
    except Exception as e:
        speak("Failed to open project")
        print("Error:", e)

def google_search(query: str):
    if not query:
        speak("What should I search?")
        return
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    webbrowser.open(url)
    speak(f"Searching Google for {query}")

def handle_volume(words: str):
    if "up" in words:
        pyautogui.press("volumeup")
        speak("Volume increased")
    elif "down" in words:
        pyautogui.press("volumedown")
        speak("Volume decreased")
    elif "mute" in words:
        pyautogui.press("volumemute")
        speak("Volume muted")


def spotify_control(command: str):
    if "pause" in command or "play" in command:
        pyautogui.press("playpause")
        speak("Toggled play and pause")
    elif "next" in command:
        pyautogui.press("nexttrack")
        speak("Playing next track")
    elif "previous" in command or "back" in command:
        pyautogui.press("prevtrack")
        speak("Playing previous track")
    elif "search" in command:
        song = command.replace("spotify search", "").replace("search spotify for", "").strip()
        if not song:
            speak("Which song should I search in Spotify?")
            return
        run_cmd("spotify")
        time.sleep(3)
        pyautogui.hotkey("ctrl", "l") 
        pyautogui.typewrite(song)
        pyautogui.press("enter")
        speak(f"Searching Spotify for {song}")



speak("Jarvis dynamic mode is ready")

OPEN_APP_PAT = re.compile(r'^(?:open|launch)\s+(.+)$', re.IGNORECASE)
OPEN_PROJECT_PAT = re.compile(r'^(?:open|launch)\s+project\s+(.+?)(?:\s+in\s+code)?$', re.IGNORECASE)
OPEN_PROJECT_IN_CODE_PAT = re.compile(r'^(?:open|launch)\s+project\s+(.+?)\s+in\s+code$', re.IGNORECASE)
GOOGLE_PAT = re.compile(r'^(?:google|search\s+google\s+for)\s+(.+)$', re.IGNORECASE)
VOLUME_PAT = re.compile(r'^(?:volume|sound)\s+(up|down|mute)$', re.IGNORECASE)
SPOTIFY_SEARCH_PAT = re.compile(r'^(?:spotify\s+search|search\s+spotify\s+for)\s+(.+)$', re.IGNORECASE)
# WIKI_PAT = re.compile(r'^(?:wikipedia|search wikipedia for)\s+(.+)$', re.IGNORECASE)



while True:
    command = listen().lower().strip()
    if not command:
        continue

    print("You said:", command)

    if command in ("exit", "quit", "stop", "goodbye"):
        speak("Goodbye")
        break

    if VOLUME_PAT.match(command):
        handle_volume(command)
        continue

    if command.startswith("search google for "):
        query = command.replace("search google for ","",1).strip()
        google_search(query)
        continue

    if command.startswith("google "):
        query = command.replace("google ","",1).strip()
        google_search(query)
        continue

    if SPOTIFY_SEARCH_PAT.match(command) or "spotify" in command:
        spotify_control(command)
        continue

    if OPEN_PROJECT_IN_CODE_PAT.match(command):
        proj = OPEN_PROJECT_IN_CODE_PAT.findall(command)[0]
        open_project(proj, in_code=True)
        continue

    if OPEN_PROJECT_PAT.match(command):
        proj = OPEN_PROJECT_PAT.findall(command)[0]
        open_project(proj, in_code=False)
        continue

    m = OPEN_APP_PAT.match(command)
    if m:
        name = m.group(1).strip()
        if name.startswith("project "):
            continue
        open_app(name)
        continue

    if "spotify" in command:
        spotify_control(command)
        continue


    if "open camera" in command:
        try:
            run_cmd("microsoft.windows.camera:")
            speak("Opening Camera")
        except Exception:
            speak("Camera app not found")
        continue

    speak("Sorry, I didn't catch that command")
