import streamlit as st
import streamlit.components.v1 as components
import subprocess
import os
import re
import time
import json
import random
import socket
import urllib.request
from pathlib import Path

# ===== CONFIG =====
st.set_page_config(
    page_title="BloodHound CE Manager",
    page_icon="🩸",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = "/bhce-instances"
VERSION = "v1.1"
GITHUB_REPO = "B3XAL/BHManager"

# ===== CSS =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;500;600;700&display=swap');

* { font-family: 'Rajdhani', sans-serif; }
code, pre, .mono { font-family: 'Share Tech Mono', monospace !important; }
html, body, [class*="css"] { background-color: #0a0c10; color: #c9d1d9; }
.stApp { background: #0a0c10; }

section[data-testid="stSidebar"] {
    background: #0d1117 !important;
    border-right: 1px solid #21262d;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #8b949e !important;
    font-size: 1rem; font-weight: 600;
    letter-spacing: 0.05em; text-transform: uppercase;
}

.bhce-card {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 6px; padding: 1.2rem 1.5rem;
    margin-bottom: 1rem; transition: border-color 0.2s;
}
.bhce-card:hover { border-color: #ff4d4d55; }
.bhce-card.running { border-left: 3px solid #3fb950; }
.bhce-card.stopped { border-left: 3px solid #f85149; }

.badge-running {
    background: #1a3a2a; color: #3fb950; border: 1px solid #3fb950;
    padding: 2px 10px; border-radius: 12px; font-size: 0.75rem;
    font-family: 'Share Tech Mono', monospace; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
}
.badge-stopped {
    background: #3a1a1a; color: #f85149; border: 1px solid #f85149;
    padding: 2px 10px; border-radius: 12px; font-size: 0.75rem;
    font-family: 'Share Tech Mono', monospace; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
}

.page-title {
    font-size: 2.2rem; font-weight: 700; color: #ff4d4d;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.2rem;
}
.page-subtitle {
    font-size: 0.9rem; color: #8b949e;
    font-family: 'Share Tech Mono', monospace; margin-bottom: 1.5rem;
}

.inst-name { font-size: 1.25rem; font-weight: 700; color: #e6edf3; letter-spacing: 0.05em; }
.inst-url { font-family: 'Share Tech Mono', monospace; color: #58a6ff; font-size: 0.85rem; }
.inst-label { color: #8b949e; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }
.inst-value { font-family: 'Share Tech Mono', monospace; color: #c9d1d9; font-size: 0.9rem; }

.stButton > button {
    background: transparent; border: 1px solid #30363d; color: #c9d1d9;
    font-family: 'Rajdhani', sans-serif; font-weight: 600;
    letter-spacing: 0.05em; text-transform: uppercase;
    font-size: 0.8rem; border-radius: 4px; transition: all 0.2s;
}
.stButton > button:hover { border-color: #ff4d4d; color: #ff4d4d; background: #ff4d4d11; }

.terminal {
    background: #0d1117; border: 1px solid #21262d; border-radius: 4px;
    padding: 1rem; font-family: 'Share Tech Mono', monospace;
    font-size: 0.82rem; color: #3fb950; white-space: pre-wrap;
    max-height: 400px; overflow-y: auto; line-height: 1.5;
}

.stTextInput > div > div > input {
    background: #161b22 !important; border: 1px solid #30363d !important;
    color: #c9d1d9 !important; font-family: 'Share Tech Mono', monospace !important;
    border-radius: 4px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #ff4d4d !important; box-shadow: 0 0 0 2px #ff4d4d22 !important;
}

hr { border-color: #21262d !important; }
.stSelectbox > div > div {
    background: #161b22 !important; border-color: #30363d !important; color: #c9d1d9 !important;
}

.logo-area {
    text-align: center; padding: 1.5rem 0 1rem 0;
    border-bottom: 1px solid #21262d; margin-bottom: 1rem;
}
.logo-icon { font-size: 2.5rem; line-height: 1; }
.logo-text { font-size: 1.1rem; font-weight: 700; color: #ff4d4d; letter-spacing: 0.15em; text-transform: uppercase; }
.logo-sub { font-size: 0.7rem; color: #8b949e; font-family: 'Share Tech Mono', monospace; letter-spacing: 0.05em; }

.update-badge {
    background: #3a1a00; color: #d29922; border: 1px solid #d29922;
    border-radius: 4px; padding: 6px 10px; font-size: 0.75rem;
    font-family: 'Share Tech Mono', monospace; font-weight: 700;
    text-align: center; margin-top: 0.5rem; cursor: pointer;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)


# ===== HELPERS =====
def sanitize_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^a-z0-9_-]', '_', name)
    name = re.sub(r'^[^a-z0-9]*', '', name)
    return name


def is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def get_free_port(min_port: int = 10000, max_port: int = 60000) -> int:
    for _ in range(100):
        port = random.randint(min_port, max_port)
        if is_port_free(port):
            return port
    raise RuntimeError("Could not find a free port after 100 attempts.")


@st.cache_data(ttl=21600)
def check_latest_version() -> str | None:
    """Check GitHub for the latest release tag. Returns tag string or None on failure."""
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "BHManager"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("tag_name")
    except Exception:
        return None


def card_with_password(card_html: str, password: str, uid: str, height: int = 130) -> None:
    eye_open = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>"""
    eye_closed = """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8b949e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>"""

    html = f"""<!DOCTYPE html><html><head>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');
      * {{ margin:0; padding:0; box-sizing:border-box; }}
      body {{ background: transparent; font-family: 'Rajdhani', sans-serif; }}
      .bhce-card {{ background:#161b22; border:1px solid #21262d; border-radius:6px; padding:1rem 1.2rem; }}
      .bhce-card.running {{ border-left:3px solid #3fb950; }}
      .bhce-card.stopped {{ border-left:3px solid #f85149; }}
      .inst-label {{ color:#8b949e; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:3px; }}
      .inst-value {{ font-family:'Share Tech Mono',monospace; color:#c9d1d9; font-size:0.88rem; }}
      .inst-value.highlight {{ color:#ff4d4d; }}
      .inst-name {{ font-size:1.1rem; font-weight:700; color:#e6edf3; letter-spacing:0.05em; }}
      .inst-url {{ font-family:'Share Tech Mono',monospace; color:#58a6ff; font-size:0.82rem; text-decoration:none; }}
      .inst-url:hover {{ text-decoration:underline; }}
      .badge-running {{ background:#1a3a2a; color:#3fb950; border:1px solid #3fb950; padding:1px 8px; border-radius:10px; font-size:0.7rem; font-family:'Share Tech Mono',monospace; font-weight:700; }}
      .badge-stopped {{ background:#3a1a1a; color:#f85149; border:1px solid #f85149; padding:1px 8px; border-radius:10px; font-size:0.7rem; font-family:'Share Tech Mono',monospace; font-weight:700; }}
      .pass-wrap {{ display:flex; align-items:center; gap:5px; }}
      .eye-btn {{ background:none; border:none; cursor:pointer; padding:0; display:flex; align-items:center; opacity:0.7; }}
      .eye-btn:hover {{ opacity:1; }}
      .header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:0.8rem; }}
      .grid {{ display:grid; gap:0.8rem; }}
    </style></head><body>
      {card_html.replace("__PASS_FIELD__", f'''
        <div class="pass-wrap">
          <span class="inst-value highlight" id="{uid}">••••••••••••••</span>
          <button class="eye-btn" id="{uid}-btn" onclick="togglePass()" title="Show password">{eye_open}</button>
        </div>''')}
    <script>
      var shown = false;
      var real = {json.dumps(password)};
      var eyeOpen = {json.dumps(eye_open)};
      var eyeClosed = {json.dumps(eye_closed)};
      function togglePass() {{
        shown = !shown;
        document.getElementById('{uid}').textContent = shown ? real : '••••••••••••••';
        document.getElementById('{uid}-btn').innerHTML = shown ? eyeClosed : eyeOpen;
      }}
    </script></body></html>"""
    components.html(html, height=height, scrolling=False)


@st.cache_data(ttl=5)
def get_instances() -> list[dict]:
    instances = []
    base = Path(BASE_DIR)
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
        return instances

    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        meta_file = d / ".bhce_meta"
        if not meta_file.exists():
            continue
        meta = {}
        for line in meta_file.read_text().splitlines():
            if '=' in line:
                k, v = line.split('=', 1)
                meta[k.strip()] = v.strip()

        result = subprocess.run(["docker", "ps", "--format", "{{.Names}}"], capture_output=True, text=True)
        running = f"bhce_{d.name}-" in result.stdout or any(
            n.startswith(f"bhce_{d.name}") for n in result.stdout.splitlines()
        )

        instances.append({
            "name": d.name,
            "path": str(d),
            "port": meta.get("BLOODHOUND_PORT", "N/A"),
            "neo4j_http": meta.get("NEO4J_HTTP_PORT", "N/A"),
            "neo4j_bolt": meta.get("NEO4J_BOLT_PORT", "N/A"),
            "password": meta.get("PASSWORD", "N/A"),
            "email": meta.get("EMAIL", "N/A"),
            "running": running,
            "meta": meta
        })
    return instances


def run_docker_compose(project: str, instance_path: str, *args) -> tuple[str, int]:
    cmd = ["docker", "compose", "-p", f"bhce_{project}"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=instance_path)
    return result.stdout + result.stderr, result.returncode


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("""
    <div class="logo-area">
        <div class="logo-icon">🩸</div>
        <div class="logo-text">BloodHound CE</div>
        <div class="logo-sub">instance manager """ + VERSION + """</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["Dashboard", "New Instance", "Manage", "Logs", "Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    instances = get_instances()
    running_count = sum(1 for i in instances if i["running"])
    total_count = len(instances)

    st.markdown(f"""
    <div style="padding: 0.5rem 0;">
        <div style="color:#8b949e; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;">System Status</div>
        <div style="display:flex; gap:1rem;">
            <div>
                <div style="color:#3fb950; font-size:1.5rem; font-weight:700;">{running_count}</div>
                <div style="color:#8b949e; font-size:0.7rem; text-transform:uppercase;">Running</div>
            </div>
            <div>
                <div style="color:#f85149; font-size:1.5rem; font-weight:700;">{total_count - running_count}</div>
                <div style="color:#8b949e; font-size:0.7rem; text-transform:uppercase;">Stopped</div>
            </div>
            <div>
                <div style="color:#58a6ff; font-size:1.5rem; font-weight:700;">{total_count}</div>
                <div style="color:#8b949e; font-size:0.7rem; text-transform:uppercase;">Total</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ---- UPDATE BADGE ----
    latest = check_latest_version()
    if latest and latest != VERSION:
        st.markdown("---")
        st.markdown(f"""
        <div class="update-badge">
            ⬆ Update available: {latest}<br>
            <span style="color:#8b949e; font-size:0.7rem;">Go to Settings to update</span>
        </div>
        """, unsafe_allow_html=True)


# ===== PAGES =====

# ---- DASHBOARD ----
if page == "Dashboard":
    st.markdown('<div class="page-title">🩸 Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">// bloodhound community edition — instance overview</div>', unsafe_allow_html=True)

    instances = get_instances()

    if not instances:
        st.markdown("""
        <div class="bhce-card" style="text-align:center; padding:3rem;">
            <div style="font-size:3rem;">🦮</div>
            <div style="color:#8b949e; margin-top:1rem; font-size:1.1rem;">No instances found.</div>
            <div style="color:#30363d; font-size:0.85rem; margin-top:0.5rem;">Go to <strong style="color:#ff4d4d;">New Instance</strong> to create your first one.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, inst in enumerate(instances):
            badge = "running" if inst["running"] else "stopped"
            badge_html = f'<span class="badge-{badge}">● {"RUNNING" if inst["running"] else "STOPPED"}</span>'
            url = f"http://localhost:{inst['port']}"
            email_display = inst['email'] if inst['email'] != "N/A" else "spam@example.com"

            card_html = f"""
            <div class="bhce-card {badge}">
              <div class="header">
                <div><span class="inst-name">{inst['name']}</span>&nbsp;&nbsp;{badge_html}</div>
                <a href="{url}" target="_blank" class="inst-url">↗ {url}</a>
              </div>
              <div class="grid" style="grid-template-columns:repeat(3,1fr);">
                <div><div class="inst-label">BH Port</div><div class="inst-value">{inst['port']}</div></div>
                <div><div class="inst-label">Password</div>__PASS_FIELD__</div>
                <div><div class="inst-label">User</div><div class="inst-value">{email_display}</div></div>
              </div>
            </div>"""
            card_with_password(card_html, inst['password'], f"pass-dash-{i}", height=140)

        st.markdown("---")
        st.markdown("**Quick Actions**")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("▶ Start All", use_container_width=True):
                for inst in instances:
                    if not inst["running"]:
                        run_docker_compose(inst["name"], inst["path"], "up", "-d")
                st.success("All instances started")
                st.rerun()
        with col2:
            if st.button("⏹ Stop All", use_container_width=True):
                for inst in instances:
                    if inst["running"]:
                        run_docker_compose(inst["name"], inst["path"], "stop")
                st.warning("All instances stopped")
                st.rerun()
        with col3:
            if st.button("↺ Refresh", use_container_width=True):
                st.rerun()


# ---- NEW INSTANCE ----
elif page == "New Instance":
    st.markdown('<div class="page-title">⚡ New Instance</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">// deploy a new bloodhound ce environment</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("""<div class="bhce-card">
            <div style="color:#ff4d4d; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:1rem;">Instance Configuration</div>
        """, unsafe_allow_html=True)
        client_name = st.text_input("Client / Instance Name", placeholder="e.g. acme_corp")
        bh_port = st.number_input("BloodHound Port (0 = random)", min_value=0, max_value=65535, value=0)
        neo4j_http = st.number_input("Neo4j HTTP Port (0 = random)", min_value=0, max_value=65535, value=0)
        neo4j_bolt = st.number_input("Neo4j Bolt Port (0 = random)", min_value=0, max_value=65535, value=0)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("""<div class="bhce-card" style="height:100%;">
            <div style="color:#ff4d4d; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:1rem;">What will happen</div>
            <div style="color:#8b949e; font-size:0.9rem; line-height:2;">
                1. Sanitize & validate name<br>2. Download docker-compose.yml from SpecterOps<br>
                3. Download bloodhound.config.json<br>4. Assign ports (random or specified)<br>
                5. Patch docker-compose with ports<br>6. Patch bloodhound.config.json<br>
                7. Start containers<br>8. Wait for initial password & email<br>9. Save metadata
            </div></div>""", unsafe_allow_html=True)

    st.markdown("")

    if st.button("🚀 Create Instance", use_container_width=True):
        if not client_name.strip():
            st.error("Instance name is required.")
        else:
            sanitized = sanitize_name(client_name.strip())
            if not sanitized:
                st.error("Invalid name after sanitization.")
            else:
                inst_path = Path(BASE_DIR) / sanitized
                if inst_path.exists():
                    st.error(f"Instance '{sanitized}' already exists.")
                else:
                    log_placeholder = st.empty()
                    output_lines = []

                    def update_log(msg, color="#c9d1d9"):
                        output_lines.append(f'<span style="color:{color};">{msg}</span>')
                        log_placeholder.markdown(
                            f'<div class="terminal">{"<br>".join(output_lines)}</div>',
                            unsafe_allow_html=True
                        )

                    with st.spinner("Creating instance..."):
                        inst_path.mkdir(parents=True)
                        update_log(f"[+] Created directory: {inst_path}", "#3fb950")

                        update_log("[+] Downloading docker-compose.yml...", "#58a6ff")
                        r = subprocess.run(["wget", "-q", "-O", str(inst_path / "docker-compose.yml"),
                            "https://raw.githubusercontent.com/SpecterOps/BloodHound/refs/heads/main/examples/docker-compose/docker-compose.yml"],
                            capture_output=True, text=True)
                        if r.returncode != 0:
                            update_log(f"[!] Error: {r.stderr}", "#f85149")
                        else:
                            update_log("[✔] docker-compose.yml downloaded", "#3fb950")

                        update_log("[+] Downloading bloodhound.config.json...", "#58a6ff")
                        r = subprocess.run(["wget", "-q", "-O", str(inst_path / "bloodhound.config.json"),
                            "https://raw.githubusercontent.com/SpecterOps/BloodHound/refs/heads/main/examples/docker-compose/bloodhound.config.json"],
                            capture_output=True, text=True)
                        if r.returncode == 0:
                            update_log("[✔] bloodhound.config.json downloaded", "#3fb950")

                        p_bh = bh_port if bh_port > 0 else get_free_port()
                        p_neo4j_http = neo4j_http if neo4j_http > 0 else get_free_port()
                        p_neo4j_bolt = neo4j_bolt if neo4j_bolt > 0 else get_free_port()
                        update_log(f"[+] Ports → BH:{p_bh} / Neo4j-HTTP:{p_neo4j_http} / Neo4j-Bolt:{p_neo4j_bolt}", "#d29922")

                        subprocess.run(["yq", "-i", "-y", "del(.services[].ports)", str(inst_path / "docker-compose.yml")])
                        subprocess.run(["yq", "-i", "-y",
                            f'.services["graph-db"].ports = ["127.0.0.1:{p_neo4j_http}:7474", "127.0.0.1:{p_neo4j_bolt}:7687"]',
                            str(inst_path / "docker-compose.yml")])
                        subprocess.run(["yq", "-i", "-y",
                            f'.services["bloodhound"].ports = ["127.0.0.1:{p_bh}:8080"]',
                            str(inst_path / "docker-compose.yml")])
                        update_log("[✔] docker-compose.yml patched", "#3fb950")

                        config_path = inst_path / "bloodhound.config.json"
                        try:
                            cfg = json.loads(config_path.read_text())
                            cfg["bind_addr"] = f"0.0.0.0:{p_bh}"
                            cfg["root_url"] = f"http://127.0.0.1:{p_bh}/"
                            config_path.write_text(json.dumps(cfg, indent=2))
                            update_log("[✔] bloodhound.config.json patched", "#3fb950")
                        except Exception as e:
                            update_log(f"[!] Config patch warning: {e}", "#d29922")

                        (inst_path / ".bhce_meta").write_text(
                            f"BLOODHOUND_PORT={p_bh}\nNEO4J_HTTP_PORT={p_neo4j_http}\nNEO4J_BOLT_PORT={p_neo4j_bolt}\n"
                        )
                        update_log("[✔] Metadata saved", "#3fb950")

                        update_log("[+] Starting containers...", "#58a6ff")
                        r = subprocess.run(
                            ["docker", "compose", "-p", f"bhce_{sanitized}", "up", "-d"],
                            capture_output=True, text=True, cwd=str(inst_path)
                        )
                        update_log(r.stdout.strip() or r.stderr.strip(), "#c9d1d9")

                        update_log("[+] Waiting for initial credentials...", "#58a6ff")
                        password = None
                        email = None
                        for attempt in range(60):
                            time.sleep(3)
                            logs_r = subprocess.run(
                                ["docker", "compose", "-p", f"bhce_{sanitized}", "logs", "bloodhound"],
                                capture_output=True, text=True, cwd=str(inst_path)
                            )
                            all_logs = logs_r.stdout + logs_r.stderr
                            if "Initial Password Set To:" in all_logs:
                                match_pass = re.search(r'Initial Password Set To:\s*([A-Za-z0-9_\-]{10,})', all_logs)
                                match_email = re.search(r'Initial User\s*(?:Set To|:)\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', all_logs)
                                if match_pass:
                                    password = match_pass.group(1)
                                if match_email:
                                    email = match_email.group(1)
                                break
                            update_log(f"[...] Attempt {attempt+1}/60 - waiting...", "#8b949e")

                        if password:
                            with open(str(inst_path / ".bhce_meta"), "a") as f:
                                f.write(f"PASSWORD={password}\n")
                                if email:
                                    f.write(f"EMAIL={email}\n")
                            update_log("[✔] Credentials captured!", "#3fb950")
                            email_display = email if email else "spam@example.com"
                            st.success(f"✅ Instance **{sanitized}** created successfully!")
                            card_html = f"""
                            <div class="bhce-card running">
                              <div style="color:#3fb950; font-weight:700; margin-bottom:0.8rem; font-size:1rem;">🎉 Instance Ready</div>
                              <div class="grid" style="grid-template-columns:repeat(2,1fr);">
                                <div><div class="inst-label">URL</div><a href="http://localhost:{p_bh}" target="_blank" class="inst-url">http://localhost:{p_bh}</a></div>
                                <div><div class="inst-label">User</div><div class="inst-value">{email_display}</div></div>
                                <div><div class="inst-label">Password</div>__PASS_FIELD__</div>
                                <div><div class="inst-label">SharpHound</div><a href="https://github.com/SpecterOps/SharpHound/releases" target="_blank" class="inst-url">Download ↗</a></div>
                              </div>
                            </div>"""
                            card_with_password(card_html, password, "pass-new", height=150)
                        else:
                            update_log("[!] Password not found in time. Check logs manually.", "#f85149")
                            st.warning("Instance started but password not captured. Check logs.")


# ---- MANAGE ----
elif page == "Manage":
    st.markdown('<div class="page-title">⚙ Manage</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">// start, stop, delete and reset instances</div>', unsafe_allow_html=True)

    instances = get_instances()

    if not instances:
        st.info("No instances available. Create one first.")
    else:
        inst_names = [i["name"] for i in instances]
        selected_name = st.selectbox("Select Instance", inst_names)
        inst = next(i for i in instances if i["name"] == selected_name)

        badge = "running" if inst["running"] else "stopped"
        badge_html = f'<span class="badge-{badge}">● {"RUNNING" if inst["running"] else "STOPPED"}</span>'

        card_html = f"""
        <div class="bhce-card {badge}">
          <div class="header"><span class="inst-name">{inst['name']}</span>{badge_html}</div>
          <div class="grid" style="grid-template-columns:repeat(4,1fr);">
            <div><div class="inst-label">BH Port</div><div class="inst-value">{inst['port']}</div></div>
            <div><div class="inst-label">Password</div>__PASS_FIELD__</div>
            <div><div class="inst-label">Neo4j HTTP</div><div class="inst-value">{inst['neo4j_http']}</div></div>
            <div><div class="inst-label">Neo4j Bolt</div><div class="inst-value">{inst['neo4j_bolt']}</div></div>
          </div>
        </div>"""
        card_with_password(card_html, inst['password'], "pass-manage", height=130)

        st.markdown("---")
        st.markdown("**Instance Actions**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("▶ Start", use_container_width=True, disabled=inst["running"]):
                with st.spinner("Starting..."):
                    out, code = run_docker_compose(inst["name"], inst["path"], "up", "-d")
                    st.success("Instance started") if code == 0 else st.error(f"Error: {out}")
                st.rerun()

        with col2:
            if st.button("⏹ Stop", use_container_width=True, disabled=not inst["running"]):
                with st.spinner("Stopping..."):
                    out, code = run_docker_compose(inst["name"], inst["path"], "stop")
                    st.warning("Instance stopped") if code == 0 else st.error(f"Error: {out}")
                st.rerun()

        with col3:
            if st.button("↺ Restart", use_container_width=True):
                with st.spinner("Restarting..."):
                    run_docker_compose(inst["name"], inst["path"], "stop")
                    time.sleep(2)
                    run_docker_compose(inst["name"], inst["path"], "up", "-d")
                    st.success("Instance restarted")
                st.rerun()

        with col4:
            if st.button("🔑 Reset Password", use_container_width=True):
                st.session_state["reset_confirm"] = inst["name"]

        if st.session_state.get("reset_confirm") == inst["name"]:
            st.warning("⚠️ This will restart the instance and generate a new password.")
            col_ok, col_cancel = st.columns(2)
            with col_ok:
                if st.button("✔ Confirm Reset", use_container_width=True):
                    with st.spinner("Resetting password..."):
                        run_docker_compose(inst["name"], inst["path"], "stop")
                        time.sleep(2)
                        subprocess.run(["yq", "-i", "-y",
                            '.services.bloodhound.environment += ["bhe_recreate_default_admin=true"]',
                            str(Path(inst["path"]) / "docker-compose.yml")])
                        run_docker_compose(inst["name"], inst["path"], "up", "-d")

                        new_pass = None
                        new_email = None
                        for _ in range(60):
                            time.sleep(3)
                            logs_r = subprocess.run(
                                ["docker", "compose", "-p", f"bhce_{inst['name']}", "logs", "bloodhound"],
                                capture_output=True, text=True, cwd=inst["path"]
                            )
                            all_logs = logs_r.stdout + logs_r.stderr
                            if "Initial Password Set To:" in all_logs:
                                match_pass = re.search(r'Initial Password Set To:\s*([A-Za-z0-9_\-]{10,})', all_logs)
                                match_email = re.search(r'Initial User\s*(?:Set To|:)\s*([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})', all_logs)
                                if match_pass:
                                    new_pass = match_pass.group(1)
                                if match_email:
                                    new_email = match_email.group(1)
                                break

                        if new_pass:
                            subprocess.run(["yq", "-i", "-y",
                                'del(.services.bloodhound.environment[] | select(. == "bhe_recreate_default_admin=true"))',
                                str(Path(inst["path"]) / "docker-compose.yml")])
                            meta_path = Path(inst["path"]) / ".bhce_meta"
                            content = meta_path.read_text()
                            content = re.sub(r'^PASSWORD=.*\n?', '', content, flags=re.MULTILINE)
                            if new_email:
                                content = re.sub(r'^EMAIL=.*\n?', '', content, flags=re.MULTILINE)
                            content += f"PASSWORD={new_pass}\n"
                            if new_email:
                                content += f"EMAIL={new_email}\n"
                            meta_path.write_text(content)
                            run_docker_compose(inst["name"], inst["path"], "up", "-d")
                            st.success(f"New password: **{new_pass}**")
                        else:
                            st.error("Could not retrieve new password. Check logs.")
                    st.session_state.pop("reset_confirm", None)
                    st.rerun()

            with col_cancel:
                if st.button("✘ Cancel", use_container_width=True):
                    st.session_state.pop("reset_confirm", None)
                    st.rerun()

        st.markdown("---")
        st.markdown("**Update saved password**")
        st.caption("Use this after changing your password inside BloodHound to keep it in sync.")
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            new_manual_pass = st.text_input(
                "New password", type="password",
                placeholder="Enter the new password you set in BloodHound",
                key=f"manual_pass_{inst['name']}"
            )
        with col_btn:
            st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
            if st.button("💾 Save", use_container_width=True):
                if new_manual_pass.strip():
                    meta_path = Path(inst["path"]) / ".bhce_meta"
                    content = meta_path.read_text()
                    content = re.sub(r'^PASSWORD=.*\n?', '', content, flags=re.MULTILINE)
                    content += f"PASSWORD={new_manual_pass.strip()}\n"
                    meta_path.write_text(content)
                    st.cache_data.clear()
                    st.success("Password updated.")
                    st.rerun()
                else:
                    st.error("Password cannot be empty.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<span style="color:#f85149; font-weight:700; text-transform:uppercase; letter-spacing:0.1em;">⚠ Danger Zone</span>', unsafe_allow_html=True)

        if st.button("🗑 Delete Instance Permanently", use_container_width=True):
            st.session_state["delete_confirm"] = inst["name"]

        if st.session_state.get("delete_confirm") == inst["name"]:
            st.error(f"⚠️ This will permanently delete **{inst['name']}** and all its data. This cannot be undone.")
            col_del, col_cancel = st.columns(2)
            with col_del:
                if st.button("💀 YES, DELETE EVERYTHING", use_container_width=True):
                    with st.spinner("Deleting..."):
                        subprocess.run(
                            ["docker", "compose", "-p", f"bhce_{inst['name']}", "down", "-v", "--remove-orphans"],
                            capture_output=True, cwd=inst["path"]
                        )
                        vols = subprocess.run(
                            ["docker", "volume", "ls", "-q", "--filter", f"name=bhce_{inst['name']}"],
                            capture_output=True, text=True
                        ).stdout.split()
                        for v in vols:
                            subprocess.run(["docker", "volume", "rm", v], capture_output=True)
                        for net in [f"bhce_{inst['name']}_default", f"bhce_{inst['name']}_net"]:
                            subprocess.run(["docker", "network", "rm", net], capture_output=True)
                        import shutil
                        shutil.rmtree(inst["path"], ignore_errors=True)
                        st.success(f"Instance {inst['name']} deleted.")
                    st.session_state.pop("delete_confirm", None)
                    st.rerun()
            with col_cancel:
                if st.button("Cancel Delete", use_container_width=True):
                    st.session_state.pop("delete_confirm", None)
                    st.rerun()


# ---- LOGS ----
elif page == "Logs":
    st.markdown('<div class="page-title">📋 Logs</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">// real-time container output viewer</div>', unsafe_allow_html=True)

    instances = get_instances()
    if not instances:
        st.info("No instances available.")
    else:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            selected_name = st.selectbox("Instance", [i["name"] for i in instances])
        with col2:
            service = st.selectbox("Service", ["bloodhound", "graph-db", "app-db"])
        with col3:
            lines = st.number_input("Lines", min_value=10, max_value=500, value=100)

        inst = next(i for i in instances if i["name"] == selected_name)
        auto_refresh = st.checkbox("Auto-refresh (5s)")

        result = subprocess.run(
            ["docker", "compose", "-p", f"bhce_{inst['name']}", "logs", "--tail", str(lines), service],
            capture_output=True, text=True, cwd=inst["path"]
        )
        log_output = result.stdout + result.stderr

        def colorize(text):
            lines_out = []
            for line in text.splitlines():
                if "ERROR" in line or "error" in line:
                    line = f'<span style="color:#f85149;">{line}</span>'
                elif "WARN" in line or "warn" in line:
                    line = f'<span style="color:#d29922;">{line}</span>'
                elif "Initial Password" in line or "Initial User" in line:
                    line = f'<span style="color:#ff4d4d; font-weight:bold;">{line}</span>'
                elif "INFO" in line:
                    line = f'<span style="color:#58a6ff;">{line}</span>'
                else:
                    line = f'<span style="color:#8b949e;">{line}</span>'
                lines_out.append(line)
            return "<br>".join(lines_out)

        st.markdown(f'<div class="terminal">{colorize(log_output)}</div>', unsafe_allow_html=True)
        if auto_refresh:
            time.sleep(5)
            st.rerun()


# ---- SETTINGS ----
elif page == "Settings":
    st.markdown('<div class="page-title">🔧 Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">// system configuration and diagnostics</div>', unsafe_allow_html=True)

    # ---- VERSION & UPDATE ----
    st.markdown("**Version**")
    latest = check_latest_version()
    col_ver, col_btn = st.columns([3, 1])
    with col_ver:
        if latest and latest != VERSION:
            st.markdown(f"Current: `{VERSION}` — Latest: `{latest}` ⬆ update available")
        elif latest:
            st.markdown(f"Current: `{VERSION}` ✅ up to date")
        else:
            st.markdown(f"Current: `{VERSION}` — could not reach GitHub")

    with col_btn:
        if latest and latest != VERSION:
            if st.button("⬆ Update now", use_container_width=True):
                with st.spinner("Updating..."):
                    result = subprocess.run(
                        ["bash", "/app/update.sh"],
                        capture_output=True, text=True
                    )
                    output = result.stdout + result.stderr
                if result.returncode == 0:
                    st.success("Update complete — reloading in a moment.")
                    st.code(output)
                    check_latest_version.clear()
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error("Update failed.")
                    st.code(output)

    st.markdown("---")
    st.markdown("**System Diagnostics**")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="bhce-card">', unsafe_allow_html=True)
        tools = {"docker": "Docker", "docker compose": "Docker Compose", "yq": "yq", "jq": "jq", "wget": "wget"}
        for cmd, label in tools.items():
            r = subprocess.run(cmd.split() + ["--version"], capture_output=True, text=True)
            ok = r.returncode == 0
            icon = "✅" if ok else "❌"
            version = r.stdout.split('\n')[0][:50] if ok else "Not found"
            st.markdown(f"`{icon} {label}`: {version}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="bhce-card">', unsafe_allow_html=True)
        st.markdown("**Docker Info**")
        r = subprocess.run(["docker", "info", "--format", "{{json .}}"], capture_output=True, text=True)
        if r.returncode == 0:
            try:
                info = json.loads(r.stdout)
                st.markdown(f"Containers running: `{info.get('ContainersRunning', 'N/A')}`")
                st.markdown(f"Containers stopped: `{info.get('ContainersStopped', 'N/A')}`")
                st.markdown(f"Images: `{info.get('Images', 'N/A')}`")
                st.markdown(f"Server version: `{info.get('ServerVersion', 'N/A')}`")
            except:
                st.code(r.stdout[:300])
        else:
            st.error("Docker not accessible. Make sure the socket is mounted.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Instance Storage**")
    base = Path(BASE_DIR)
    st.markdown(f"Instances directory: `{BASE_DIR}`")
    r = subprocess.run(["du", "-sh", str(base)], capture_output=True, text=True)
    if r.returncode == 0:
        st.markdown(f"Total disk usage: `{r.stdout.split()[0]}`")

    st.markdown("---")
    st.markdown("**Useful Links**")
    st.markdown("""
    - [BloodHound CE GitHub](https://github.com/SpecterOps/BloodHound)
    - [SharpHound Releases](https://github.com/SpecterOps/SharpHound/releases)
    - [BloodHound Docs](https://support.bloodhoundenterprise.io)
    """)
