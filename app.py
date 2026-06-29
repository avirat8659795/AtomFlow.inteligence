from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from google import genai
import os
import time

app = FastAPI()

# Initialize the Gemini Client 
# It automatically looks for the GEMINI_API_KEY environment variable on Render
ai_client = genai.Client()

class ChatRequest(BaseModel):
    message: str

# Your custom ATOM-FLOW UI HTML Code
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ATOM-FLOW AI</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0b0f17; }
        ::-webkit-scrollbar-thumb { background: #1f293d; border-radius: 9999px; }
        ::-webkit-scrollbar-thumb:hover { background: #10b981; }
    </style>
</head>
<body class="bg-[#0b0f19] text-[#e2e8f0] font-sans antialiased h-screen flex overflow-hidden">
    <aside id="sidebar" class="w-[260px] bg-[#070a10] h-full flex flex-col justify-between border-r border-[#1e293b]/40 shrink-0">
        <div class="p-3.5 flex flex-col h-full overflow-y-auto">
            <button class="flex items-center justify-between w-full px-4 py-2.5 text-sm font-semibold bg-[#0f172a] border-2 border-[#10b981] text-white shadow-[0_0_15px_rgba(16,185,129,0.15)] mb-6">
                <div class="flex items-center gap-2.5"><span class="text-base text-[#10b981]">⚛️</span> New chat</div>
                <span class="text-xs text-[#64748b]">Ctrl N</span>
            </button>
            <div class="space-y-1">
                <p class="px-3 text-xs font-bold text-[#475569] uppercase tracking-wider mb-2.5">Recent Logs</p>
                <a href="#" class="block px-3 py-2 text-sm text-white rounded-lg bg-[#0f172a]/80 border border-[#1e293b]/30 truncate font-medium">Atom-Flow Core Active</a>
            </div>
        </div>
        <div class="p-4 border-t border-[#1e293b]/30 flex flex-col gap-2 bg-[#05070b]">
            <div class="flex items-center gap-3 p-2 rounded-xl bg-[#0f172a]/40 border border-[#1e293b]/20">
                <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center"><span class="text-xs">⚛️</span></div>
                <div class="flex flex-col">
                    <span class="text-sm font-bold text-white tracking-wide">ATOM-FLOW</span>
                    <span class="text-[10px] text-[#10b981] font-mono tracking-widest">ONLINE</span>
                </div>
            </div>
        </div>
    </aside>

    <main class="flex-1 flex flex-col h-full bg-[#0b0f19] relative overflow-hidden">
        <div class="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.04] z-0 select-none">
            <svg width="450" height="450" viewBox="0 0 1024 1024" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="512" cy="512" r="70" fill="#10b981" />
                <ellipse cx="512" cy="512" rx="140" ry="380" stroke="#10b981" stroke-width="32" />
                <ellipse cx="512" cy="512" rx="140" ry="380" stroke="#10b981" stroke-width="32" transform="rotate(60 512 512)" />
                <ellipse cx="512" cy="512" rx="140" ry="380" stroke="#10b981" stroke-width="32" transform="rotate(120 512 512)" />
            </svg>
        </div>
        
        <header class="h-14 flex items-center px-5 justify-between border-b border-[#1e293b]/30 z-10 bg-[#0b0f19]/80 backdrop-blur-md">
            <div class="text-sm font-medium text-[#94a3b8]">Model: <span class="text-white font-bold tracking-wide">ATOM-FLOW 3.5-Core</span></div>
        </header>

        <div id="chatFeed" class="flex-1 overflow-y-auto px-4 py-8 space-y-6 max-w-3xl w-full mx-auto flex flex-col z-10">
            <div class="flex gap-4 items-start text-base">
                <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0">⚛️</div>
                <div class="space-y-1.5 flex-1 pt-0.5 leading-relaxed">
                    <p class="font-bold text-white text-sm tracking-wide">ATOM-FLOW Core</p>
                    <p class="text-[#cbd5e1] text-[15px]">System online. Paste any website link, and I will scrape its text data using Selenium before responding with Gemini. Try it out!</p>
                </div>
            </div>
        </div>

        <footer class="p-4 bg-gradient-to-t from-[#0b0f19] via-[#0b0f19] to-transparent z-10">
            <div class="max-w-3xl w-full mx-auto relative flex flex-col items-center">
                <div class="w-full relative flex items-center bg-[#0f172a] rounded-2xl border border-[#1e293b]/60 shadow-2xl group">
                    <textarea id="messageInput" rows="1" placeholder="Message Atom-Flow..." class="w-full bg-transparent text-white placeholder-[#475569] pl-4 pr-14 py-4 resize-none focus:outline-none text-[15px] max-h-52 overflow-y-auto leading-relaxed" oninput="autoGrow(this)" onkeydown="handleKeyDown(event)"></textarea>
                    <button onclick="commitMessageToSend()" class="absolute right-3.5 p-2 bg-[#070a10] border border-[#1e293b]/40 hover:bg-white text-white hover:text-black rounded-xl transition-all duration-200 shadow-md">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>
                    </button>
                </div>
                <p class="text-xs text-[#475569] font-medium mt-3 text-center tracking-wide">ATOM-FLOW can mistake structural facts. Verify essential infrastructure parameters directly.</p>
            </div>
        </footer>
    </main>

    <script>
        function autoGrow(element) { element.style.height = "auto"; element.style.height = (element.scrollHeight) + "px"; }
        
        function handleKeyDown(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); commitMessageToSend(); } }

        function appendMessage(text, isUser) {
            const feed = document.getElementById('chatFeed');
            let block = '';
            if(isUser) {
                block = `<div class="flex gap-4 items-start text-base self-end justify-end w-full max-w-xl ml-auto">
                            <div class="bg-[#1e293b]/60 border border-[#334155]/40 rounded-2xl px-4 py-3 text-white text-[15px] leading-relaxed shadow-md backdrop-blur-sm">${text.replace(/\\n/g, '<br>')}</div>
                         </div>`;
            } else {
                block = `<div class="flex gap-4 items-start text-base">
                            <div class="w-8 h-8 rounded-full bg-[#070a10] border border-[#10b981] flex items-center justify-center text-xs shrink-0 shadow-md">⚛️</div>
                            <div class="space-y-1.5 flex-1 pt-0.5 leading-relaxed">
                                <p class="font-bold text-white text-sm tracking-wide">ATOM-FLOW Core</p>
                                <p class="text-[#cbd5e1] text-[15px]">${text.replace(/\\n/g, '<br>')}</p>
                            </div>
                         </div>`;
            }
            feed.insertAdjacentHTML('beforeend', block);
            feed.scrollTop = feed.scrollHeight;
        }

        function commitMessageToSend() {
            const input = document.getElementById('messageInput');
            const messageText = input.value.trim();
            if (!messageText) return;

            appendMessage(messageText, true);
            input.value = '';
            input.style.height = 'auto';

            fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText })
            })
            .then(res => res.json())
            .then(data => {
                appendMessage(data.reply, false);
            })
            .catch(err => {
                appendMessage("System core transmission error. Verify backend environment status logs.", false);
            });
        }
    </script>
</body>
</html>
"""

def scrape_with_selenium(url: str) -> str:
    """Safely runs a headless Chrome scraper session inside Render's Linux container"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Initialize the background browser
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        time.sleep(3) # Let JavaScript elements render completely
        body_text = driver.find_element("tag name", "body").text
        driver.quit()
        return body_text[:4000] # Cap text length for prompt efficiency
    except Exception as e:
        driver.quit()
        return f"Scraping error encountered: {str(e)}"

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    return HTML_UI

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    user_prompt = request.message
    scraped_context = ""
    
    # Detect if user pasted a web link
    if "http://" in user_prompt or "https://" in user_prompt:
        words = user_prompt.split()
        target_url = next((w for w in words if w.startswith("http")), None)
        if target_url:
            scraped_context = scrape_with_selenium(target_url)

    system_instruction = "You are ATOM-FLOW, an advanced AI system core running a premium minimalist design interface. Be helpful, technical, and accurate."
    
    final_prompt = user_prompt
    if scraped_context:
        final_prompt = f"Scraped Data from webpage:\n\"\"\"\n{scraped_context}\n\"\"\"\n\nUser Question: {user_prompt}"

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=final_prompt,
            config={'system_instruction': system_instruction}
        )
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
