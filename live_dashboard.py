"""
PATHWAY LIVE ANALYST - Retro Terminal Dashboard
Real-time news analysis with Truth-O-Meter and Sentiment tracking
"""

import os
import sys
import time
import threading
from datetime import datetime
from collections import deque
import requests
from dotenv import load_dotenv
import openai

# Rich library for terminal UI
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich import box

load_dotenv()

# ============== Configuration ==============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

openai.api_key = OPENAI_API_KEY

console = Console()

# ============== Color Scheme ==============
CYAN = "cyan"
MAGENTA = "magenta"
YELLOW = "yellow"
GREEN = "green"
RED = "red"
WHITE = "white"
DIM = "dim"

# ============== Global State ==============
class AnalystState:
    def __init__(self):
        self.topic = "TECHNOLOGY"
        self.news_items = deque(maxlen=50)
        self.hn_items = deque(maxlen=50)
        self.all_items = deque(maxlen=100)
        self.lock = threading.Lock()
        
        # Analysis state
        self.verdict = "Analyzing incoming data streams..."
        self.alert_type = "INFO"  # INFO, WARNING, ALERT
        self.truth_status = "ANALYZING"
        self.truth_score = 50
        self.official_matches = 0
        
        # Sentiment
        self.mood = "NEUTRAL"
        self.mood_percent = 50
        self.keywords = ["#AI", "#Tech", "#News"]
        self.velocity = 0
        
        # Polling status
        self.news_status = "OK"
        self.hn_status = "OK"
        self.llm_status = "OK"
        
        # Stats
        self.total_processed = 0

state = AnalystState()

# ============== Data Fetching ==============
def fetch_news():
    """Fetch news from NewsData.io"""
    try:
        if not NEWSDATA_API_KEY or NEWSDATA_API_KEY == "your_newsdata_key_here":
            # Demo data
            return [{
                "source": "GNews",
                "type": "📰",
                "text": "Government announces new AI regulation framework.",
                "url": "http://newsdata.io",
                "age": "2m",
                "timestamp": time.time(),
                "official": True
            }]
        
        url = "https://newsdata.io/api/1/latest"
        params = {"apikey": NEWSDATA_API_KEY, "language": "en", "category": "technology"}
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        
        results = []
        for article in data.get("results", [])[:10]:
            title = article.get('title', '')[:60]
            results.append({
                "source": "GNews",
                "type": "📰",
                "text": f"{title}...",
                "url": article.get("link", ""),
                "age": "new",
                "timestamp": time.time(),
                "official": True
            })
        state.news_status = "OK"
        return results
    except Exception as e:
        state.news_status = "ERR"
        return []

def fetch_hackernews():
    """Fetch top stories from Hacker News - FREE API"""
    try:
        # Get top story IDs
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        resp = requests.get(top_url, timeout=10)
        story_ids = resp.json()[:15]
        
        results = []
        for story_id in story_ids:
            item_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            item_resp = requests.get(item_url, timeout=5)
            item = item_resp.json()
            
            if item and item.get("title"):
                age_secs = int(time.time() - item.get("time", time.time()))
                if age_secs < 60:
                    age = f"{age_secs}s"
                elif age_secs < 3600:
                    age = f"{age_secs // 60}m"
                else:
                    age = f"{age_secs // 3600}h"
                
                results.append({
                    "source": "HackerNews",
                    "type": "🔶",
                    "text": item.get('title', '')[:60] + "...",
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                    "age": age,
                    "timestamp": item.get("time", time.time()),
                    "score": item.get("score", 0),
                    "official": False
                })
        
        state.hn_status = "OK"
        return results
    except Exception as e:
        state.hn_status = "ERR"
        return []

def fetch_reddit_posts():
    """Fetch from Reddit's public JSON API - NO AUTH NEEDED"""
    try:
        headers = {'User-Agent': 'LiveAnalyst/1.0'}
        url = "https://www.reddit.com/r/technology/hot.json?limit=10"
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        
        results = []
        for post in data.get("data", {}).get("children", []):
            post_data = post.get("data", {})
            title = post_data.get("title", "")[:60]
            created = post_data.get("created_utc", time.time())
            age_secs = int(time.time() - created)
            
            if age_secs < 60:
                age = f"{age_secs}s"
            elif age_secs < 3600:
                age = f"{age_secs // 60}m"
            else:
                age = f"{age_secs // 3600}h"
            
            results.append({
                "source": "Reddit",
                "type": "🔴",
                "text": f"{title}...",
                "url": f"https://reddit.com{post_data.get('permalink', '')}",
                "age": age,
                "timestamp": created,
                "score": post_data.get("score", 0),
                "official": False
            })
        
        return results
    except Exception as e:
        return []

# ============== Analysis ==============
def analyze_with_llm(items):
    """Analyze items with OpenAI"""
    if not OPENAI_API_KEY or not items:
        return
    
    try:
        state.llm_status = "..."
        
        # Build context
        texts = [item["text"] for item in items[-15:]]
        context = "\n".join(texts)
        
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": """Analyze these news/social posts and provide:
1. A one-line verdict about what's happening (max 80 chars)
2. Alert level: INFO, WARNING, or ALERT
3. Overall mood: POSITIVE, NEUTRAL, NEGATIVE, or PANIC
4. Top 3 keywords/hashtags
5. Truth score 0-100 (how verified is the info)

Respond in this exact format:
VERDICT: <your verdict>
ALERT: <INFO/WARNING/ALERT>
MOOD: <mood>
KEYWORDS: <keyword1>, <keyword2>, <keyword3>
SCORE: <number>"""},
                {"role": "user", "content": f"Analyze:\n{context}"}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        result = response.choices[0].message.content
        
        # Parse response
        for line in result.split("\n"):
            if line.startswith("VERDICT:"):
                state.verdict = line.replace("VERDICT:", "").strip()[:80]
            elif line.startswith("ALERT:"):
                alert = line.replace("ALERT:", "").strip().upper()
                if alert in ["INFO", "WARNING", "ALERT"]:
                    state.alert_type = alert
            elif line.startswith("MOOD:"):
                mood = line.replace("MOOD:", "").strip().upper()
                state.mood = mood
                if mood == "POSITIVE":
                    state.mood_percent = 75
                elif mood == "NEGATIVE":
                    state.mood_percent = 25
                elif mood == "PANIC":
                    state.mood_percent = 88
                else:
                    state.mood_percent = 50
            elif line.startswith("KEYWORDS:"):
                kws = line.replace("KEYWORDS:", "").strip()
                state.keywords = [f"#{k.strip().replace('#','')}" for k in kws.split(",")][:3]
            elif line.startswith("SCORE:"):
                try:
                    score = int(line.replace("SCORE:", "").strip())
                    state.truth_score = max(0, min(100, score))
                    if score > 70:
                        state.truth_status = "VERIFIED"
                    elif score > 40:
                        state.truth_status = "MIXED"
                    else:
                        state.truth_status = "VIRAL / RUMOR"
                except:
                    pass
        
        state.llm_status = "OK"
    except Exception as e:
        state.llm_status = "ERR"

# ============== Background Fetcher ==============
def background_fetcher():
    """Background thread to periodically fetch data"""
    while True:
        try:
            # Fetch news
            new_news = fetch_news()
            with state.lock:
                for item in new_news:
                    state.news_items.append(item)
                    state.all_items.append(item)
            
            # Fetch Hacker News
            new_hn = fetch_hackernews()
            with state.lock:
                for item in new_hn:
                    state.hn_items.append(item)
                    state.all_items.append(item)
            
            # Fetch Reddit
            new_reddit = fetch_reddit_posts()
            with state.lock:
                for item in new_reddit:
                    state.all_items.append(item)
            
            # Count official matches
            with state.lock:
                state.official_matches = sum(1 for i in state.all_items if i.get("official"))
                state.velocity = len(list(state.all_items)[-20:])
                state.total_processed = len(state.all_items)
            
            # Analyze with LLM
            with state.lock:
                items_copy = list(state.all_items)
            analyze_with_llm(items_copy)
            
        except Exception as e:
            pass
        
        time.sleep(60)

# ============== UI Components ==============
def create_header():
    """Create the header bar"""
    now = datetime.now().strftime("%H:%M:%S")
    
    header = Table.grid(expand=True)
    header.add_column(justify="left", ratio=1)
    header.add_column(justify="center", ratio=2)
    header.add_column(justify="right", ratio=1)
    
    title = Text("PATHWAY LIVE ANALYST", style=f"bold {CYAN}")
    topic = Text(f":: TOPIC: {state.topic} ::", style=f"{MAGENTA}")
    time_text = Text(now, style=f"bold {YELLOW}")
    
    header.add_row(title, topic, time_text)
    
    return Panel(header, box=box.DOUBLE, style=CYAN, padding=(0, 1))

def create_verdict():
    """Create THE VERDICT panel"""
    if state.alert_type == "ALERT":
        alert_style = f"bold {RED}"
        alert_icon = "⚠️  ALERT:"
        alert_text = "UNVERIFIED MAJOR EVENT DETECTED"
    elif state.alert_type == "WARNING":
        alert_style = f"bold {YELLOW}"
        alert_icon = "⚡"
        alert_text = "ELEVATED ACTIVITY DETECTED"
    else:
        alert_style = f"bold {GREEN}"
        alert_icon = "ℹ️ "
        alert_text = "MONITORING NORMAL"
    
    content = Text()
    content.append(f"\n{alert_icon} {alert_text}\n\n", style=alert_style)
    content.append(f'"{state.verdict}"\n', style=WHITE)
    content.append(f"\nRecommendation: ", style=DIM)
    
    if state.truth_score < 40:
        content.append("High probability of unverified content. Verify before sharing.", style=YELLOW)
    elif state.truth_score < 70:
        content.append("Mixed sources. Cross-reference with official news.", style=CYAN)
    else:
        content.append("Information appears verified from official sources.", style=GREEN)
    
    return Panel(
        Align.center(content),
        title="[bold red]◆ THE VERDICT[/bold red]",
        box=box.ROUNDED,
        style=RED,
        padding=(0, 2)
    )

def create_truth_meter():
    """Create TRUTH-O-METER panel"""
    # Build the score bar
    filled = int(state.truth_score / 10)
    bar = "[" + "|" * filled + "█" * (filled > 0) + "═" * (10 - filled) + "]"
    
    content = Text()
    content.append("STATUS: ", style=DIM)
    
    if state.truth_status == "VERIFIED":
        content.append(f"{state.truth_status}\n", style=f"bold {GREEN}")
    elif state.truth_status == "MIXED":
        content.append(f"{state.truth_status}\n", style=f"bold {YELLOW}")
    else:
        content.append(f"{state.truth_status}\n", style=f"bold {MAGENTA}")
    
    content.append("SCORE: ", style=DIM)
    content.append(f"{bar} {state.truth_score}%\n", style=CYAN)
    content.append("MATCHES: ", style=DIM)
    content.append(f"{state.official_matches} Official", style=GREEN)
    
    return Panel(
        content,
        title="[bold cyan]◆ TRUTH-O-METER[/bold cyan]",
        box=box.ROUNDED,
        style=CYAN,
        padding=(0, 1)
    )

def create_sentiment():
    """Create SENTIMENT panel"""
    content = Text()
    
    # Mood with emoji
    mood_emoji = {"POSITIVE": "😊", "NEUTRAL": "😐", "NEGATIVE": "😟", "PANIC": "😱"}.get(state.mood, "😐")
    mood_color = {"POSITIVE": GREEN, "NEUTRAL": CYAN, "NEGATIVE": YELLOW, "PANIC": MAGENTA}.get(state.mood, CYAN)
    
    content.append("• MOOD: ", style=DIM)
    content.append(f"{mood_emoji} {state.mood} ({state.mood_percent}%)\n", style=f"bold {mood_color}")
    
    content.append("• KEYWORDS: ", style=DIM)
    content.append(", ".join(state.keywords) + "\n", style=MAGENTA)
    
    content.append("• VELOCITY: ", style=DIM)
    content.append(f"{state.velocity} posts / min", style=CYAN)
    
    return Panel(
        content,
        title="[bold magenta]◆ SENTIMENT[/bold magenta]",
        box=box.ROUNDED,
        style=MAGENTA,
        padding=(0, 1)
    )

def create_feed():
    """Create LIVE EVIDENCE FEED table"""
    table = Table(
        box=box.SIMPLE,
        expand=True,
        show_header=True,
        header_style=f"bold {CYAN}",
        row_styles=["", "dim"]
    )
    
    table.add_column("TYPE", width=4, justify="center")
    table.add_column("SOURCE", width=12, style=YELLOW)
    table.add_column("CONTENT SNIPPET (Drill-Down)", ratio=3)
    table.add_column("AGE", width=6, justify="right", style=DIM)
    
    with state.lock:
        items = list(state.all_items)[-8:]  # Last 8 items
    
    for item in reversed(items):
        source = item.get("source", "Unknown")
        text = item.get("text", "")[:55]
        age = item.get("age", "?")
        
        # Color based on source
        if item.get("official"):
            type_style = GREEN
            text_display = Text(text, style=GREEN)
        else:
            type_style = YELLOW
            text_display = Text(text, style=WHITE)
        
        # Check for no match
        if "[NO MATCH" in text:
            text_display = Text(text, style=DIM)
        
        table.add_row(
            Text(item.get("type", "📄"), style=type_style),
            source,
            text_display,
            age
        )
    
    if not items:
        table.add_row("", "", Text("Loading data streams...", style=DIM), "")
    
    return Panel(
        table,
        title="[bold yellow]◆ LIVE EVIDENCE FEED[/bold yellow]",
        subtitle="[dim](Latest incoming data streams - Auto-Updating)[/dim]",
        box=box.ROUNDED,
        style=YELLOW,
        padding=(0, 1)
    )

def create_status_bar():
    """Create the bottom status bar"""
    content = Text()
    content.append("■ [SYSTEM]: ", style=DIM)
    
    # News status
    content.append("Polling News... ", style=DIM)
    if state.news_status == "OK":
        content.append("OK", style=f"bold {GREEN}")
    else:
        content.append("ERR", style=f"bold {RED}")
    
    content.append(" | Polling HN... ", style=DIM)
    if state.hn_status == "OK":
        content.append("OK", style=f"bold {GREEN}")
    else:
        content.append("ERR", style=f"bold {RED}")
    
    content.append(" | LLM Analysis... ", style=DIM)
    if state.llm_status == "OK":
        content.append("OK", style=f"bold {GREEN}")
    elif state.llm_status == "...":
        content.append("...", style=f"bold {YELLOW}")
    else:
        content.append("ERR", style=f"bold {RED}")
    
    content.append(f" | Total: {state.total_processed} items", style=DIM)
    
    return Panel(content, box=box.SQUARE, style=DIM, padding=(0, 1))

def create_layout():
    """Create the full dashboard layout"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="verdict", size=8),
        Layout(name="middle", size=7),
        Layout(name="feed", size=14),
        Layout(name="status", size=3)
    )
    
    layout["middle"].split_row(
        Layout(name="truth", ratio=1),
        Layout(name="sentiment", ratio=1)
    )
    
    return layout

def render_dashboard():
    """Render the complete dashboard"""
    layout = create_layout()
    
    layout["header"].update(create_header())
    layout["verdict"].update(create_verdict())
    layout["truth"].update(create_truth_meter())
    layout["sentiment"].update(create_sentiment())
    layout["feed"].update(create_feed())
    layout["status"].update(create_status_bar())
    
    return layout

# ============== Main ==============
def main():
    console.clear()
    
    # Print startup banner
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║     🔴 PATHWAY LIVE ANALYST - Real-Time News Dashboard 🔴     ║
    ║                                                               ║
    ║  Sources: NewsData.io + Hacker News + Reddit (FREE APIs)      ║
    ║  Analysis: OpenAI GPT-4o-mini                                 ║
    ║                                                               ║
    ║  Press Ctrl+C to exit                                         ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    time.sleep(2)
    
    # Start background fetcher
    fetcher = threading.Thread(target=background_fetcher, daemon=True)
    fetcher.start()
    
    # Initial fetch
    console.print("\n[yellow]⏳ Fetching initial data...[/yellow]")
    
    new_news = fetch_news()
    with state.lock:
        for item in new_news:
            state.news_items.append(item)
            state.all_items.append(item)
    
    new_hn = fetch_hackernews()
    with state.lock:
        for item in new_hn:
            state.hn_items.append(item)
            state.all_items.append(item)
    
    new_reddit = fetch_reddit_posts()
    with state.lock:
        for item in new_reddit:
            state.all_items.append(item)
    
    console.print(f"[green]✅ Loaded {len(state.all_items)} items[/green]\n")
    time.sleep(1)
    
    # Run initial analysis
    console.print("[yellow]🧠 Running LLM analysis...[/yellow]")
    with state.lock:
        items_copy = list(state.all_items)
    analyze_with_llm(items_copy)
    console.print("[green]✅ Analysis complete[/green]\n")
    time.sleep(1)
    
    # Live dashboard
    try:
        with Live(render_dashboard(), refresh_per_second=1, screen=True) as live:
            while True:
                live.update(render_dashboard())
                time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Shutting down...[/yellow]")

if __name__ == "__main__":
    main()
