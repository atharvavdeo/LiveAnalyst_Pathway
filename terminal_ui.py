"""
PATHWAY LIVE ANALYST - Terminal Dashboard UI
A retro-style terminal interface for real-time news analysis
"""

import os
import sys
import time
import threading
from datetime import datetime
from collections import deque
from typing import Optional
import requests
from requests_oauthlib import OAuth1
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
from rich.box import DOUBLE, ROUNDED, HEAVY
from rich import box

load_dotenv()

# ============== Configuration ==============
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
X_CONSUMER_KEY = os.getenv("X_CONSUMER_KEY")
X_CONSUMER_SECRET = os.getenv("X_CONSUMER_SECRET")

openai.api_key = OPENAI_API_KEY

console = Console()

# ============== Global State ==============
class AnalystState:
    def __init__(self):
        self.topic = "TECHNOLOGY"
        self.news_items = deque(maxlen=50)
        self.x_items = deque(maxlen=50)
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
        self.x_status = "OK"
        self.llm_status = "OK"
        
        # Rate limiting
        self.x_daily_count = 0
        self.x_daily_limit = 100
        self.last_x_request = 0

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
            title = article.get('title', '')[:50]
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

def fetch_x_posts():
    """Fetch posts from X with rate limiting"""
    try:
        # Rate limiting check
        if state.x_daily_count >= state.x_daily_limit:
            state.x_status = "LIMIT"
            return []
        
        elapsed = time.time() - state.last_x_request
        if elapsed < 60:
            return []
        
        if not X_CONSUMER_KEY or X_CONSUMER_KEY == "your_x_consumer_key":
            # Demo data
            return [
                {
                    "source": "Twitter",
                    "type": "🐦",
                    "text": "Anyone else lose power in Altamira? Whole...",
                    "url": "http://x.com",
                    "age": "12s",
                    "timestamp": time.time(),
                    "official": False
                },
                {
                    "source": "Reddit",
                    "type": "🔴",
                    "text": "Traffic lights down on Main St. Chaos.",
                    "url": "http://reddit.com",
                    "age": "40s",
                    "timestamp": time.time(),
                    "official": False
                }
            ]
        
        auth = OAuth1(X_CONSUMER_KEY, X_CONSUMER_SECRET)
        search_url = "https://api.twitter.com/2/tweets/search/recent"
        params = {
            "query": f"{state.topic} -is:retweet lang:en",
            "max_results": 10,
            "tweet.fields": "created_at,public_metrics"
        }
        
        resp = requests.get(search_url, auth=auth, params=params, timeout=30)
        state.last_x_request = time.time()
        state.x_daily_count += 1
        
        if resp.status_code != 200:
            state.x_status = f"E{resp.status_code}"
            # Return demo data on error
            return [{
                "source": "Twitter",
                "type": "🐦",
                "text": "Demo: X API unavailable. Sample data shown.",
                "url": "http://x.com",
                "age": "now",
                "timestamp": time.time(),
                "official": False
            }]
        
        data = resp.json()
        results = []
        for tweet in data.get("data", []):
            text = tweet.get("text", "")[:45]
            results.append({
                "source": "Twitter",
                "type": "🐦",
                "text": f"{text}...",
                "url": f"https://x.com/i/status/{tweet.get('id')}",
                "age": "new",
                "timestamp": time.time(),
                "official": False
            })
        state.x_status = "OK"
        return results
    except Exception as e:
        state.x_status = "ERR"
        return [{
            "source": "Twitter",
            "type": "🐦", 
            "text": "Connection error. Retrying...",
            "url": "",
            "age": "ERR",
            "timestamp": time.time(),
            "official": False
        }]

def analyze_with_llm():
    """Use OpenAI to analyze the current data and generate verdict"""
    try:
        with state.lock:
            items = list(state.all_items)[-15:]
        
        if not items:
            return
        
        # Build context
        social_texts = [i["text"] for i in items if not i.get("official")]
        news_texts = [i["text"] for i in items if i.get("official")]
        
        social_count = len(social_texts)
        news_count = len(news_texts)
        
        # Calculate basic metrics
        state.velocity = social_count * 3  # posts per min estimate
        state.official_matches = news_count
        
        # Determine truth score
        if news_count > 0 and social_count > 0:
            state.truth_score = min(90, 40 + (news_count * 10))
            state.truth_status = "VERIFIED" if state.truth_score > 70 else "VIRAL / RUMOR"
        elif social_count > 0:
            state.truth_score = max(20, 60 - (social_count * 5))
            state.truth_status = "VIRAL / RUMOR"
        else:
            state.truth_score = 50
            state.truth_status = "ANALYZING"
        
        # Use LLM for deeper analysis
        if OPENAI_API_KEY:
            context = "\n".join([f"- {i['text']}" for i in items])
            
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """You are a real-time news analyst. Analyze the data and respond with ONLY a JSON object (no markdown):
{"verdict": "One sentence summary of the situation", "mood": "PANIC|FEAR|CONCERN|NEUTRAL|POSITIVE", "mood_percent": 50, "keywords": ["#tag1", "#tag2", "#tag3"], "alert_type": "INFO|WARNING|ALERT"}"""},
                    {"role": "user", "content": f"Analyze this real-time data:\n{context}"}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            # Parse JSON
            import json
            try:
                result = json.loads(result_text)
                state.verdict = result.get("verdict", state.verdict)
                state.mood = result.get("mood", "NEUTRAL")
                state.mood_percent = result.get("mood_percent", 50)
                state.keywords = result.get("keywords", state.keywords)[:3]
                state.alert_type = result.get("alert_type", "INFO")
            except:
                pass
            
            state.llm_status = "OK"
    except Exception as e:
        state.llm_status = "ERR"

# ============== Background Fetcher ==============
def background_fetcher():
    """Background thread to fetch data"""
    while True:
        try:
            # Fetch news
            news = fetch_news()
            with state.lock:
                for item in news:
                    state.news_items.append(item)
                    state.all_items.append(item)
            
            # Fetch X/social
            social = fetch_x_posts()
            with state.lock:
                for item in social:
                    state.x_items.append(item)
                    state.all_items.append(item)
            
            # Run analysis
            analyze_with_llm()
            
        except Exception as e:
            pass
        
        time.sleep(30)  # Update every 30 seconds

# ============== UI Components ==============
def make_header() -> Panel:
    """Create the header panel"""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="center", ratio=2)
    grid.add_column(justify="right", ratio=1)
    
    title = Text("PATHWAY LIVE ANALYST", style="bold cyan")
    topic = Text(f":: TOPIC: {state.topic} ::", style="magenta")
    time_str = Text(datetime.now().strftime("%H:%M:%S"), style="cyan")
    
    grid.add_row(title, topic, time_str)
    
    return Panel(grid, style="cyan", box=box.DOUBLE)

def make_verdict() -> Panel:
    """Create THE VERDICT panel"""
    # Determine style based on alert type
    if state.alert_type == "ALERT":
        alert_style = "bold red"
        alert_icon = "☠️ ALERT:"
    elif state.alert_type == "WARNING":
        alert_style = "bold yellow"
        alert_icon = "⚠️ ALERT:"
    else:
        alert_style = "bold green"
        alert_icon = "ℹ️ STATUS:"
    
    content = Text()
    content.append(f"{alert_icon} ", style=alert_style)
    
    if state.alert_type in ["ALERT", "WARNING"]:
        content.append("UNVERIFIED MAJOR EVENT DETECTED\n\n", style=alert_style)
    else:
        content.append("MONITORING ACTIVE\n\n", style=alert_style)
    
    content.append(f'"{state.verdict}"\n', style="white")
    
    if state.official_matches == 0 and state.truth_status == "VIRAL / RUMOR":
        content.append("Official GNews/Reuters feeds are SILENT.\n", style="yellow")
        content.append("Recommendation: High probability of real event ahead of news cycle.", style="dim")
    elif state.official_matches > 0:
        content.append(f"Official sources confirm: {state.official_matches} matches found.\n", style="green")
        content.append("Recommendation: Event appears verified by official sources.", style="dim")
    
    return Panel(
        Align.center(content),
        title="[red]◈ THE VERDICT[/red]",
        border_style="red",
        box=box.ROUNDED
    )

def make_truth_meter() -> Panel:
    """Create TRUTH-O-METER panel"""
    content = Text()
    
    # Status
    status_color = "yellow" if state.truth_status == "VIRAL / RUMOR" else "green" if state.truth_status == "VERIFIED" else "cyan"
    content.append("STATUS: ", style="bold white")
    content.append(f"{state.truth_status}\n", style=f"bold {status_color}")
    
    # Score bar
    content.append("SCORE: [", style="white")
    filled = int(state.truth_score / 10)
    for i in range(10):
        if i < filled:
            content.append("|", style="green")
        else:
            content.append("≡", style="dim")
    content.append(f"] {state.truth_score}%\n", style="white")
    
    # Matches
    content.append("MATCHES: ", style="white")
    content.append(f"{state.official_matches} Official", style="cyan")
    
    return Panel(
        content,
        title="[cyan]◈ TRUTH-O-METER[/cyan]",
        border_style="cyan",
        box=box.ROUNDED
    )

def make_sentiment() -> Panel:
    """Create SENTIMENT panel"""
    content = Text()
    
    # Mood
    mood_colors = {
        "PANIC": "red",
        "FEAR": "red",
        "CONCERN": "yellow",
        "NEUTRAL": "cyan",
        "POSITIVE": "green"
    }
    mood_emojis = {
        "PANIC": "😱",
        "FEAR": "😨",
        "CONCERN": "😟",
        "NEUTRAL": "😐",
        "POSITIVE": "😊"
    }
    
    mood_color = mood_colors.get(state.mood, "cyan")
    mood_emoji = mood_emojis.get(state.mood, "😐")
    
    content.append("• MOOD: ", style="white")
    content.append(f"{mood_emoji} {state.mood} ({state.mood_percent}%)\n", style=f"bold {mood_color}")
    
    # Keywords
    content.append("• KEYWORDS: ", style="white")
    for i, kw in enumerate(state.keywords):
        content.append(kw, style="magenta")
        if i < len(state.keywords) - 1:
            content.append(", ", style="white")
    content.append("\n", style="white")
    
    # Velocity
    content.append("• VELOCITY: ", style="white")
    content.append(f"{state.velocity} posts / min", style="cyan")
    
    return Panel(
        content,
        title="[magenta]◈ SENTIMENT[/magenta]",
        border_style="magenta",
        box=box.ROUNDED
    )

def make_evidence_feed() -> Panel:
    """Create LIVE EVIDENCE FEED table"""
    table = Table(
        expand=True,
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("TYPE", style="dim", width=4)
    table.add_column("SOURCE", style="cyan", width=10)
    table.add_column("CONTENT SNIPPET (Drill-Down)", style="white", ratio=3)
    table.add_column("AGE", justify="right", style="dim", width=6)
    
    with state.lock:
        items = list(state.all_items)[-8:]  # Show last 8 items
    
    # Add demo items if empty
    if not items:
        items = [
            {"type": "🔴", "source": "Reddit (u/x)", "text": '"Anyone else lose power in Altamira? Whole..."', "age": "12s", "official": False},
            {"type": "🐦", "source": "Twitter", "text": '"Traffic lights down on Main St. Chaos."', "age": "40s", "official": False},
            {"type": "🔴", "source": "Reddit", "text": '"My wifi just cut. Using data to post..."', "age": "1m", "official": False},
            {"type": "📰", "source": "GNews", "text": "[NO MATCH FOUND FOR 'BLACKOUT']", "age": "-", "official": True},
            {"type": "📰", "source": "Reuters", "text": '(Last unrelated: "Oil prices stable...")', "age": "4h", "official": True},
        ]
    
    for item in items:
        type_icon = item.get("type", "📄")
        source = item.get("source", "Unknown")
        text = item.get("text", "")[:50]
        age = item.get("age", "?")
        is_official = item.get("official", False)
        
        # Style based on source type
        if is_official:
            text_style = "dim yellow" if "NO MATCH" in text or "unrelated" in text else "green"
        else:
            text_style = "white"
        
        table.add_row(
            type_icon,
            source,
            Text(f'"{text}"', style=text_style),
            age
        )
    
    return Panel(
        table,
        title="[yellow]◈ LIVE EVIDENCE FEED[/yellow]",
        subtitle="(Latest incoming data streams - Auto-Updating)",
        border_style="yellow",
        box=box.ROUNDED
    )

def make_status_bar() -> Panel:
    """Create bottom status bar"""
    content = Text()
    content.append("█ ", style="dim")
    content.append("SYSTEM]: ", style="dim cyan")
    
    # News status
    news_color = "green" if state.news_status == "OK" else "red"
    content.append("Polling News... ", style="dim")
    content.append(state.news_status, style=news_color)
    content.append(" | ", style="dim")
    
    # X status
    x_color = "green" if state.x_status == "OK" else "yellow" if state.x_status == "LIMIT" else "red"
    content.append("Polling X... ", style="dim")
    content.append(state.x_status, style=x_color)
    content.append(" | ", style="dim")
    
    # LLM status
    llm_color = "green" if state.llm_status == "OK" else "red"
    content.append("LLM Updating... ", style="dim")
    content.append(state.llm_status, style=llm_color)
    
    return Panel(content, style="dim", box=box.SIMPLE)

def make_layout() -> Layout:
    """Create the full dashboard layout"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="verdict", size=8),
        Layout(name="meters", size=8),
        Layout(name="feed", size=14),
        Layout(name="status", size=3)
    )
    
    # Split meters into two columns
    layout["meters"].split_row(
        Layout(name="truth"),
        Layout(name="sentiment")
    )
    
    return layout

def update_layout(layout: Layout):
    """Update all layout components"""
    layout["header"].update(make_header())
    layout["verdict"].update(make_verdict())
    layout["truth"].update(make_truth_meter())
    layout["sentiment"].update(make_sentiment())
    layout["feed"].update(make_evidence_feed())
    layout["status"].update(make_status_bar())

# ============== Main ==============
def main():
    # Print startup banner
    console.clear()
    console.print("[bold cyan]╔══════════════════════════════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║[/bold cyan]          [bold white]PATHWAY LIVE ANALYST[/bold white] - Starting Up...           [bold cyan]║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════════════════════════════╝[/bold cyan]")
    console.print()
    
    # Check configuration
    console.print(f"  [cyan]OpenAI API:[/cyan]    {'[green]✓ Configured[/green]' if OPENAI_API_KEY else '[red]✗ Missing[/red]'}")
    console.print(f"  [cyan]NewsData.io:[/cyan]  {'[green]✓ Configured[/green]' if NEWSDATA_API_KEY else '[yellow]⚠ Demo Mode[/yellow]'}")
    console.print(f"  [cyan]X API:[/cyan]         {'[green]✓ Configured[/green]' if X_CONSUMER_KEY else '[yellow]⚠ Demo Mode[/yellow]'}")
    console.print()
    console.print("[dim]Starting background data streams...[/dim]")
    time.sleep(2)
    
    # Start background fetcher
    fetcher = threading.Thread(target=background_fetcher, daemon=True)
    fetcher.start()
    
    # Create layout
    layout = make_layout()
    
    # Run live display
    console.clear()
    with Live(layout, refresh_per_second=2, screen=True) as live:
        while True:
            try:
                update_layout(layout)
                time.sleep(0.5)
            except KeyboardInterrupt:
                break
    
    console.print("\n[yellow]Shutting down PATHWAY LIVE ANALYST...[/yellow]")

if __name__ == "__main__":
    main()
