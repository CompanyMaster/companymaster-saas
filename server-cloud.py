#!/usr/bin/env python3
"""
MicroSaaS MVP — Versão Cloud-Ready para Railway/Render.
Usa APENAS Python built-in (http.server + urllib + json + sqlite3).
Mudanças do original:
  - BASE_DIR usa Path(__file__).parent (relativo ao script)
  - PORT usa variável de ambiente (Railway/Render injetam automaticamente)
  - DATA_DIR dentro do diretório do projeto (persiste no volume Railway)
"""

import json
import sqlite3
import hashlib
import secrets
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ─── CONFIG ───────────────────────────────────────────────
# ★ MUDANÇA 1: Caminho relativo ao script (funciona em qualquer lugar)
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "saas.db"

# ★ MUDANÇA 2: Porta via variável de ambiente (Railway/Render injetam PORT)
PORT = int(os.environ.get("PORT", 8080))

# ─── DATABASE ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            email TEXT,
            plan TEXT DEFAULT 'free',
            credits INTEGER DEFAULT 100,
            created_at TEXT DEFAULT (datetime('now')),
            last_used TEXT
        );
        CREATE TABLE IF NOT EXISTS api_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            endpoint TEXT,
            timestamp TEXT DEFAULT (datetime('now')),
            status INTEGER,
            credits_used INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS revenue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT DEFAULT (datetime('now')),
            source TEXT,
            amount_usd REAL,
            user_api_key TEXT
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            plan TEXT,
            status TEXT DEFAULT 'active',
            started_at TEXT DEFAULT (datetime('now')),
            amount_usd REAL
        );
        CREATE TABLE IF NOT EXISTS url_shortener (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            api_key TEXT,
            clicks INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

def generate_api_key():
    return "cm_" + secrets.token_hex(16)

def create_user(conn, email=None, plan="free", initial_credits=100):
    api_key = generate_api_key()
    conn.execute(
        "INSERT INTO users (api_key, email, plan, credits) VALUES (?,?,?,?)",
        (api_key, email, plan, initial_credits)
    )
    conn.commit()
    return api_key

# ─── SAAS: URL Shortener ─────────────────────────────────
class URLShortener:
    def __init__(self, conn):
        self.conn = conn
    
    def shorten(self, original_url, api_key=None):
        code = secrets.token_hex(4)
        self.conn.execute(
            "INSERT INTO url_shortener (short_code, original_url, api_key) VALUES (?,?,?)",
            (code, original_url, api_key)
        )
        self.conn.commit()
        return {
            "short_code": code,
            "short_url": f"http://localhost:{PORT}/s/{code}",
            "original_url": original_url
        }
    
    def lookup(self, code):
        cur = self.conn.execute(
            "SELECT original_url, clicks FROM url_shortener WHERE short_code = ?",
            (code,)
        )
        row = cur.fetchone()
        if row:
            self.conn.execute(
                "UPDATE url_shortener SET clicks = clicks + 1 WHERE short_code = ?",
                (code,)
            )
            self.conn.commit()
            return row[0]
        return None
    
    def stats(self, code):
        cur = self.conn.execute(
            "SELECT short_code, original_url, clicks, created_at FROM url_shortener WHERE short_code = ?",
            (code,)
        )
        row = cur.fetchone()
        if row:
            return {
                "short_code": row[0],
                "original_url": row[1],
                "clicks": row[2],
                "created_at": row[3]
            }
        return None

# ─── SAAS: QR Code Generator ──────────────────────────────
def generate_qr(text, size=200):
    import urllib.parse
    encoded = urllib.parse.quote(text.encode('utf-8'))
    return f"https://chart.googleapis.com/chart?chs={size}x{size}&cht=qr&chl={encoded}&choe=UTF-8"

# ─── SAAS: Text Tools ─────────────────────────────────────
class TextTools:
    @staticmethod
    def word_count(text):
        return {"words": len(text.split()), "chars": len(text), "lines": text.count('\n') + 1}
    
    @staticmethod
    def markdown_to_html(text):
        import re
        html = text
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)
        html = re.sub(r'\n\n', '</p><p>', html)
        html = '<p>' + html + '</p>'
        return {"html": html}
    
    @staticmethod
    def slugify(text):
        import re, unicodedata
        slug = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
        slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        return {"slug": slug}

# ─── HTTP SERVER ──────────────────────────────────────────
class SaaSHandler(BaseHTTPRequestHandler):
    conn = None
    url_shortener = None
    
    def log_message(self, format, *args):
        # Log mínimo para debug
        print(f"[{datetime.now().isoformat()}] {self.command} {self.path}")
    
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _check_api_key(self):
        api_key = self.headers.get('X-API-Key', '')
        if not api_key:
            parsed = urlparse(self.path)
            api_key = parse_qs(parsed.query).get('api_key', [''])[0]
        if not api_key:
            return None
        
        cur = self.conn.execute(
            "SELECT api_key, plan, credits FROM users WHERE api_key = ?",
            (api_key,)
        )
        return cur.fetchone()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        
        if path in ('', '/') or path == '/health':
            self._send_json({
                "service": "CompanyMaster SaaS",
                "version": "0.1.0",
                "status": "running",
                "endpoints": ["/shorten", "/qr", "/tools/wordcount", "/tools/md2html", "/tools/slugify"]
            })
            return
        
        if path.startswith('/s/'):
            code = path[3:]
            original = self.url_shortener.lookup(code)
            if original:
                self.send_response(302)
                self.send_header('Location', original)
                self.end_headers()
            else:
                self._send_json({"error": "Short URL not found"}, 404)
            return
        
        if path == '/shorten':
            params = parse_qs(parsed.query)
            url = params.get('url', [''])[0]
            if not url:
                self._send_json({"error": "Missing 'url' parameter"}, 400)
                return
            result = self.url_shortener.shorten(url)
            self._send_json(result)
            return
        
        if path == '/qr':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            size = int(params.get('size', ['200'])[0])
            if not text:
                self._send_json({"error": "Missing 'text' parameter"}, 400)
                return
            qr_url = generate_qr(text, size)
            self._send_json({"qr_url": qr_url, "text": text, "size": size})
            return
        
        if path == '/tools/wordcount':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            result = TextTools.word_count(text)
            self._send_json(result)
            return
        
        if path == '/tools/md2html':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            result = TextTools.markdown_to_html(text)
            self._send_json(result)
            return
        
        if path == '/tools/slugify':
            params = parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            result = TextTools.slugify(text)
            self._send_json(result)
            return
        
        if path.startswith('/stats/'):
            code = path[7:]
            stats = self.url_shortener.stats(code)
            if stats:
                self._send_json(stats)
            else:
                self._send_json({"error": "Not found"}, 404)
            return
        
        self._send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length else '{}'
        
        try:
            data = json.loads(body)
        except:
            data = {}
        
        parsed = urlparse(self.path)
        path = parsed.path.rstrip('/')
        
        if path == '/register':
            email = data.get('email', '')
            plan = data.get('plan', 'free')
            api_key = create_user(self.conn, email, plan)
            self._send_json({
                "api_key": api_key,
                "plan": plan,
                "message": "Save this API key! It won't be shown again."
            }, 201)
            return
        
        if path == '/shorten':
            url = data.get('url', '')
            if not url:
                self._send_json({"error": "Missing 'url'"}, 400)
                return
            api_key = data.get('api_key', '')
            result = self.url_shortener.shorten(url, api_key if api_key else None)
            self._send_json(result, 201)
            return
        
        self._send_json({"error": "Not found"}, 404)

def run_server(port=None):
    if port is None:
        port = PORT
    
    conn = init_db()
    
    cur = conn.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        demo_key = create_user(conn, "demo@companymaster.ai", "demo", 9999)
        print(f"\n🔑 Demo API Key: {demo_key}")
    
    SaaSHandler.conn = conn
    SaaSHandler.url_shortener = URLShortener(conn)
    
    server = HTTPServer(('0.0.0.0', port), SaaSHandler)
    print(f"\n🚀 CompanyMaster SaaS running on http://0.0.0.0:{port}")
    print(f"📂 DB Path: {DB_PATH}")
    print(f"📋 Endpoints:")
    print(f"   GET  /health            — Health check")
    print(f"   POST /register          — Create API key")
    print(f"   GET  /shorten?url=...   — Shorten URL")
    print(f"   GET  /s/{{code}}          — Redirect to original URL")
    print(f"   GET  /qr?text=...       — Generate QR code")
    print(f"   GET  /tools/wordcount   — Count words")
    print(f"   GET  /tools/md2html     — Markdown to HTML")
    print(f"   GET  /tools/slugify     — URL slug generator")
    print(f"\n💰 Monetization-ready: API key system, usage tracking, subscription plans")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        server.shutdown()
        conn.close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)
