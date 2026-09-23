import json
import re
from pathlib import Path

def build():
    orig_path = Path("graphify-out/graph_orig.html")
    if not orig_path.exists():
        orig_path = Path("graphify-out/graph.html")
    content = orig_path.read_text(encoding="utf-8")

    m_nodes = re.search(r"const RAW_NODES\s*=\s*(\[.*?\]);", content)
    m_edges = re.search(r"const RAW_EDGES\s*=\s*(\[.*?\]);", content)
    m_legend = re.search(r"const LEGEND\s*=\s*(\[.*?\]);", content)

    if not (m_nodes and m_edges and m_legend):
        print("ERROR: Could not parse RAW_NODES / RAW_EDGES / LEGEND from original graph.html")
        return

    raw_nodes_str = m_nodes.group(1)
    raw_edges_str = m_edges.group(1)
    legend_str = m_legend.group(1)

    template = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>INSPECTRA &bull; Knowledge Graph Atlas</title>
<!-- Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,500;0,600;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<!-- Vis Network -->
<script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>

<style>
  :root {
    --bg-base: #07090e;
    --bg-surface: #0d111b;
    --bg-panel: rgba(13, 17, 27, 0.78);
    --bg-elevated: rgba(22, 28, 44, 0.88);
    --bg-glass-input: rgba(8, 11, 19, 0.65);
    
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-medium: rgba(255, 255, 255, 0.14);
    --border-active: rgba(99, 102, 241, 0.45);
    
    --accent-indigo: #6366f1;
    --accent-cyan: #06b6d4;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --accent-violet: #8b5cf6;
    
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    
    --font-ui: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', "SFMono-Regular", Consolas, monospace;
    
    --shadow-glass: 0 16px 36px -8px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.08);
    --shadow-floating: 0 20px 45px -10px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.12);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  
  body {
    background: var(--bg-base);
    color: var(--text-primary);
    font-family: var(--font-ui);
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
    user-select: none;
    background-image: 
      radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 40%),
      radial-gradient(circle at 80% 80%, rgba(6, 182, 212, 0.06) 0%, transparent 45%);
  }

  /* TOP COMMAND HEADER */
  #header {
    height: 60px;
    background: rgba(10, 14, 23, 0.85);
    backdrop-filter: blur(20px) saturate(180%);
    border-bottom: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    z-index: 50;
    gap: 16px;
    flex-shrink: 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .logo-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: inherit;
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, var(--accent-indigo), var(--accent-cyan));
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 18px rgba(99, 102, 241, 0.4);
  }

  .logo-icon svg {
    width: 18px;
    height: 18px;
    color: #fff;
  }

  .logo-text {
    display: flex;
    flex-direction: column;
  }

  .logo-title {
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.05em;
    background: linear-gradient(to right, #fff, #cbd5e1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .logo-badge {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.1em;
    color: var(--accent-cyan);
    text-transform: uppercase;
  }

  .stats-strip {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.04);
    padding: 5px 12px;
    border-radius: 20px;
    border: 1px solid var(--border-subtle);
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .stats-pulse {
    width: 7px;
    height: 7px;
    background: var(--accent-emerald);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--accent-emerald);
    animation: pulse 2s infinite ease-in-out;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.85); }
  }

  .stat-chip {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: var(--font-mono);
  }

  .stat-chip b {
    color: var(--text-primary);
  }

  /* HEADER CENTER: SEARCH */
  .header-center {
    flex: 1;
    max-width: 480px;
    position: relative;
  }

  .search-container {
    position: relative;
    width: 100%;
  }

  .search-input-wrap {
    display: flex;
    align-items: center;
    background: var(--bg-glass-input);
    border: 1px solid var(--border-medium);
    border-radius: 10px;
    padding: 0 12px;
    height: 38px;
    transition: all 0.2s ease;
  }

  .search-input-wrap:focus-within {
    border-color: var(--accent-indigo);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
    background: rgba(13, 17, 28, 0.85);
  }

  .search-icon {
    width: 16px;
    height: 16px;
    color: var(--text-muted);
    margin-right: 8px;
    flex-shrink: 0;
  }

  #search {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--text-primary);
    font-size: 13px;
    font-family: var(--font-ui);
    outline: none;
  }

  #search::placeholder {
    color: var(--text-muted);
  }

  .kbd-shortcut {
    font-size: 10px;
    font-family: var(--font-mono);
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.08);
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  #search-results {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    right: 0;
    background: var(--bg-elevated);
    backdrop-filter: blur(24px);
    border: 1px solid var(--border-medium);
    border-radius: 12px;
    max-height: 340px;
    overflow-y: auto;
    box-shadow: var(--shadow-floating);
    display: none;
    z-index: 100;
    padding: 6px;
  }

  .search-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 12px;
    transition: background 0.15s ease;
  }

  .search-item:hover, .search-item.active {
    background: rgba(99, 102, 241, 0.15);
  }

  .search-item-left {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  .search-item-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .search-item-label {
    font-family: var(--font-mono);
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .search-item-sub {
    font-size: 11px;
    color: var(--text-muted);
    margin-left: 8px;
    flex-shrink: 0;
  }

  /* HEADER RIGHT */
  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .hdr-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-subtle);
    color: var(--text-secondary);
    padding: 7px 12px;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    outline: none;
  }

  .hdr-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    border-color: var(--border-medium);
  }

  .hdr-btn.active {
    background: rgba(99, 102, 241, 0.2);
    border-color: var(--accent-indigo);
    color: #a5b4fc;
  }

  .hdr-btn svg {
    width: 14px;
    height: 14px;
  }

  /* MAIN WORKSPACE */
  #workspace {
    flex: 1;
    display: flex;
    position: relative;
    overflow: hidden;
  }

  /* GRAPH CANVAS VIEWPORT */
  #graph-viewport {
    flex: 1;
    position: relative;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
    background-size: 32px 32px;
    overflow: hidden;
  }

  #graph {
    width: 100%;
    height: 100%;
  }

  /* FLOATING CANVAS HUD CONTROLS */
  #hud-controls {
    position: absolute;
    bottom: 24px;
    left: 24px;
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(14, 18, 30, 0.82);
    backdrop-filter: blur(20px) saturate(180%);
    border: 1px solid var(--border-medium);
    padding: 5px;
    border-radius: 9999px;
    box-shadow: var(--shadow-floating);
    z-index: 20;
  }

  .hud-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .hud-btn:hover {
    background: rgba(255, 255, 255, 0.12);
    color: var(--text-primary);
    transform: scale(1.05);
  }

  .hud-btn svg {
    width: 16px;
    height: 16px;
  }

  .hud-divider {
    width: 1px;
    height: 20px;
    background: var(--border-medium);
    margin: 0 2px;
  }

  /* CALIBRATION / STABILIZATION HUD SPINNER */
  #stabilization-overlay {
    position: absolute;
    top: 20px;
    left: 20px;
    background: rgba(15, 20, 32, 0.85);
    backdrop-filter: blur(20px);
    border: 1px solid var(--border-medium);
    border-radius: 12px;
    padding: 10px 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    box-shadow: var(--shadow-glass);
    z-index: 25;
    transition: opacity 0.5s ease, visibility 0.5s ease;
  }

  .spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(99, 102, 241, 0.25);
    border-top-color: var(--accent-indigo);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .stabilize-text {
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: 500;
  }

  /* SIDEBAR DRAWER */
  #sidebar {
    width: 380px;
    background: var(--bg-panel);
    backdrop-filter: blur(24px) saturate(180%);
    border-left: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    z-index: 40;
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), width 0.3s ease;
    box-shadow: -8px 0 28px rgba(0, 0, 0, 0.4);
  }

  #sidebar.collapsed {
    transform: translateX(100%);
    width: 0;
  }

  /* TABS HEADER */
  .tabs-nav {
    display: flex;
    border-bottom: 1px solid var(--border-subtle);
    background: rgba(10, 14, 23, 0.6);
    padding: 6px 10px 0;
    gap: 4px;
    flex-shrink: 0;
  }

  .tab-btn {
    flex: 1;
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--text-muted);
    padding: 9px 4px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
    cursor: pointer;
    text-transform: uppercase;
    transition: all 0.2s ease;
    border-radius: 6px 6px 0 0;
  }

  .tab-btn:hover {
    color: var(--text-secondary);
    background: rgba(255, 255, 255, 0.02);
  }

  .tab-btn.active {
    color: #fff;
    border-bottom-color: var(--accent-indigo);
    background: rgba(99, 102, 241, 0.08);
  }

  .tab-content {
    flex: 1;
    overflow-y: auto;
    display: none;
    padding: 16px;
  }

  .tab-content.active {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* TAB 1: NODE INSPECTOR */
  .inspector-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .node-title-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
  }

  .node-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--text-primary);
    font-family: var(--font-mono);
    word-break: break-all;
    line-height: 1.35;
  }

  .copy-btn {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--border-subtle);
    color: var(--text-secondary);
    padding: 4px 8px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 11px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }

  .copy-btn:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #fff;
  }

  .tags-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    border: 1px solid transparent;
  }

  .badge-type {
    background: rgba(6, 182, 212, 0.15);
    color: var(--accent-cyan);
    border-color: rgba(6, 182, 212, 0.3);
    text-transform: uppercase;
    font-family: var(--font-mono);
  }

  .badge-community {
    background: rgba(255, 255, 255, 0.08);
    color: #fff;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .metric-box {
    background: rgba(10, 14, 23, 0.5);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
  }

  .metric-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.05em;
  }

  .metric-val {
    font-size: 18px;
    font-weight: 700;
    font-family: var(--font-mono);
    color: var(--text-primary);
    margin-top: 2px;
  }

  .source-path-card {
    background: rgba(10, 14, 23, 0.5);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .source-path-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .source-path-val {
    font-family: var(--font-mono);
    font-size: 11px;
    color: #a5b4fc;
    word-break: break-all;
    line-height: 1.4;
  }

  .neighbors-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .section-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.05em;
  }

  #neighbors-list {
    max-height: 240px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding-right: 4px;
  }

  .neighbor-link {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 7px 10px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid transparent;
    border-left: 3px solid var(--accent-indigo);
    font-size: 12px;
    font-family: var(--font-mono);
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .neighbor-link:hover {
    background: rgba(99, 102, 241, 0.12);
    color: var(--text-primary);
    border-color: rgba(99, 102, 241, 0.25);
    transform: translateX(2px);
  }

  .empty-inspector {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
    gap: 12px;
  }

  .empty-inspector svg {
    width: 42px;
    height: 42px;
    color: rgba(255, 255, 255, 0.15);
  }

  .empty-inspector h4 {
    font-size: 14px;
    color: var(--text-secondary);
    font-weight: 600;
  }

  .empty-inspector p {
    font-size: 12px;
    line-height: 1.5;
  }

  /* TAB 2: COMMUNITIES LIST */
  .comm-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding-bottom: 4px;
  }

  .comm-search-input {
    width: 100%;
    background: var(--bg-glass-input);
    border: 1px solid var(--border-subtle);
    border-radius: 8px;
    padding: 6px 10px;
    color: var(--text-primary);
    font-size: 12px;
    outline: none;
    margin-bottom: 8px;
  }

  .comm-search-input:focus {
    border-color: var(--accent-indigo);
  }

  .comm-ctrl-btn {
    background: transparent;
    border: none;
    color: var(--accent-cyan);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    padding: 2px 4px;
  }

  .comm-ctrl-btn:hover {
    text-decoration: underline;
  }

  #legend {
    display: flex;
    flex-direction: column;
    gap: 4px;
    overflow-y: auto;
    padding-right: 4px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 7px 10px;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid transparent;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .legend-item:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--border-subtle);
  }

  .legend-item.dimmed {
    opacity: 0.35;
  }

  .legend-left {
    display: flex;
    align-items: center;
    gap: 9px;
    min-width: 0;
  }

  .legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .legend-label {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .legend-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .legend-count {
    font-size: 11px;
    font-family: var(--font-mono);
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.04);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .solo-btn {
    font-size: 10px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-subtle);
    color: var(--text-muted);
    padding: 2px 5px;
    border-radius: 4px;
    cursor: pointer;
    text-transform: uppercase;
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  .legend-item:hover .solo-btn {
    opacity: 1;
  }

  .solo-btn:hover {
    background: var(--accent-indigo);
    color: #fff;
    border-color: var(--accent-indigo);
  }

  /* TAB 3: GOD NODES */
  .god-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 10px 12px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .god-item:hover {
    background: rgba(99, 102, 241, 0.08);
    border-color: rgba(99, 102, 241, 0.3);
    transform: translateY(-1px);
  }

  .god-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .god-rank-label {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .god-rank {
    font-size: 10px;
    font-weight: 700;
    color: var(--accent-amber);
    background: rgba(245, 158, 11, 0.12);
    width: 20px;
    height: 20px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-mono);
  }

  .god-name {
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .god-degree {
    font-size: 11px;
    font-family: var(--font-mono);
    color: var(--accent-cyan);
    font-weight: 600;
  }

  .god-bar-wrap {
    height: 4px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 2px;
    overflow: hidden;
  }

  .god-bar {
    height: 100%;
    background: linear-gradient(to right, var(--accent-indigo), var(--accent-cyan));
    border-radius: 2px;
  }

  /* TAB 4: AUDIT & INSIGHTS */
  .audit-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .audit-hdr {
    font-size: 12px;
    font-weight: 700;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .audit-hdr svg {
    width: 14px;
    height: 14px;
    color: var(--accent-amber);
  }

  .surprise-item {
    font-size: 11px;
    color: var(--text-secondary);
    padding: 6px 8px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.2);
    border-left: 2px solid var(--accent-amber);
    line-height: 1.4;
  }

  .surprise-item b {
    color: var(--text-primary);
    font-family: var(--font-mono);
  }

  /* KEYBOARD SHORTCUTS MODAL */
  #shortcuts-modal {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(12px);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 200;
  }

  .modal-box {
    background: var(--bg-surface);
    border: 1px solid var(--border-medium);
    border-radius: 16px;
    padding: 24px;
    width: 440px;
    box-shadow: var(--shadow-floating);
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .modal-hdr {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .modal-hdr h3 {
    font-size: 16px;
    font-weight: 700;
    color: #fff;
  }

  .modal-close {
    background: transparent;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    font-size: 18px;
  }

  .shortcuts-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .shortcut-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    color: var(--text-secondary);
  }

  /* SCROLLBAR STYLING */
  ::-webkit-scrollbar {
    width: 5px;
    height: 5px;
  }
  ::-webkit-scrollbar-track {
    background: transparent;
  }
  ::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 10px;
  }
  ::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.22);
  }
</style>
</head>
<body>

<!-- TOP COMMAND HEADER -->
<header id="header">
  <div class="header-left">
    <div class="logo-wrap">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
          <polyline points="2 17 12 22 22 17"></polyline>
          <polyline points="2 12 12 17 22 12"></polyline>
        </svg>
      </div>
      <div class="logo-text">
        <span class="logo-title">INSPECTRA</span>
        <span class="logo-badge">Topology Atlas</span>
      </div>
    </div>

    <div class="stats-strip">
      <div class="stats-pulse"></div>
      <span class="stat-chip"><b id="stat-nodes">1,312</b> nodes</span>
      <span>&middot;</span>
      <span class="stat-chip"><b id="stat-edges">3,145</b> edges</span>
      <span>&middot;</span>
      <span class="stat-chip"><b id="stat-clusters">51</b> clusters</span>
    </div>
  </div>

  <div class="header-center">
    <div class="search-container">
      <div class="search-input-wrap">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input id="search" type="text" placeholder="Search functions, classes, files..." autocomplete="off">
        <span class="kbd-shortcut">/</span>
      </div>
      <div id="search-results"></div>
    </div>
  </div>

  <div class="header-right">
    <button class="hdr-btn" id="btn-fit" title="Fit to Screen (F)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="15 3 21 3 21 9"></polyline>
        <polyline points="9 21 3 21 3 15"></polyline>
        <line x1="21" y1="3" x2="14" y2="10"></line>
        <line x1="3" y1="21" x2="10" y2="14"></line>
      </svg>
      <span>Fit View</span>
    </button>

    <button class="hdr-btn" id="btn-physics" title="Toggle Layout Physics (Space)">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
      </svg>
      <span id="physics-label">Physics</span>
    </button>

    <button class="hdr-btn" id="btn-export" title="Export PNG Snapshot">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span>Snapshot</span>
    </button>

    <button class="hdr-btn" id="btn-toggle-sidebar" title="Toggle Inspector Panel">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
        <line x1="15" y1="3" x2="15" y2="21"></line>
      </svg>
    </button>
  </div>
</header>

<!-- MAIN WORKSPACE -->
<main id="workspace">
  <!-- GRAPH CANVAS VIEWPORT -->
  <div id="graph-viewport">
    <div id="graph"></div>

    <!-- CALIBRATION OVERLAY -->
    <div id="stabilization-overlay">
      <div class="spinner"></div>
      <span class="stabilize-text" id="stabilize-msg">Calibrating topology simulation...</span>
    </div>

    <!-- FLOATING HUD CONTROLS -->
    <div id="hud-controls">
      <button class="hud-btn" id="hud-zoom-in" title="Zoom In">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
      </button>
      <button class="hud-btn" id="hud-zoom-out" title="Zoom Out">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
      </button>
      <button class="hud-btn" id="hud-fit" title="Reset Camera">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
      </button>
      <div class="hud-divider"></div>
      <button class="hud-btn" id="hud-solo-toggle" title="Toggle Neighborhood Spotlight">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
      </button>
      <button class="hud-btn" id="hud-help" title="Keyboard Shortcuts (?)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
      </button>
    </div>
  </div>

  <!-- SIDEBAR DRAWER -->
  <aside id="sidebar">
    <div class="tabs-nav">
      <button class="tab-btn active" data-tab="tab-inspector">Inspector</button>
      <button class="tab-btn" data-tab="tab-communities">Clusters</button>
      <button class="tab-btn" data-tab="tab-gods">God Hubs</button>
      <button class="tab-btn" data-tab="tab-audit">Insights</button>
    </div>

    <!-- TAB 1: INSPECTOR -->
    <div class="tab-content active" id="tab-inspector">
      <div id="inspector-content">
        <div class="empty-inspector">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="m10 15 5-3-5-3v6Z"></path>
          </svg>
          <h4>No Node Selected</h4>
          <p>Click any node or symbol in the network or use search (<b>/</b>) to inspect dependencies, source location, and degree centrality.</p>
        </div>
      </div>
    </div>

    <!-- TAB 2: COMMUNITIES -->
    <div class="tab-content" id="tab-communities">
      <div class="comm-toolbar">
        <span style="font-size:12px;font-weight:700;color:var(--text-secondary);">Filter Clusters</span>
        <div>
          <button class="comm-ctrl-btn" id="comm-all-btn">Show All</button>
          <span style="color:var(--border-medium);">&middot;</span>
          <button class="comm-ctrl-btn" id="comm-none-btn">Hide All</button>
        </div>
      </div>
      <input type="text" class="comm-search-input" id="comm-filter" placeholder="Filter clusters...">
      <div id="legend"></div>
    </div>

    <!-- TAB 3: GOD NODES -->
    <div class="tab-content" id="tab-gods">
      <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;">
        Core Architectural Abstractions ranked by degree centrality:
      </div>
      <div id="gods-list" style="display:flex;flex-direction:column;gap:8px;"></div>
    </div>

    <!-- TAB 4: AUDIT -->
    <div class="tab-content" id="tab-audit">
      <div class="audit-card">
        <div class="audit-hdr">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          Surprising Inferred Connections
        </div>
        <div style="display:flex;flex-direction:column;gap:6px;">
          <div class="surprise-item"><b>measure_run()</b> &rarr; uses &rarr; <b>Camera</b><br><span style="color:var(--text-muted);">phase0/p0/pipeline.py &rarr; camera.py</span></div>
          <div class="surprise-item"><b>process_frame()</b> &rarr; uses &rarr; <b>Camera</b><br><span style="color:var(--text-muted);">phase0/p0/pipeline.py &rarr; camera.py</span></div>
          <div class="surprise-item"><b>render_burst()</b> &rarr; uses &rarr; <b>Camera</b><br><span style="color:var(--text-muted);">phase0/p0/render.py &rarr; camera.py</span></div>
          <div class="surprise-item"><b>render_frame()</b> &rarr; uses &rarr; <b>Camera</b><br><span style="color:var(--text-muted);">phase0/p0/render.py &rarr; camera.py</span></div>
          <div class="surprise-item"><b>TestMisplacedRoiAbstains</b> &rarr; uses &rarr; <b>Camera</b><br><span style="color:var(--text-muted);">tests/test_glyph_roi_map.py &rarr; camera.py</span></div>
        </div>
      </div>

      <div class="audit-card">
        <div class="audit-hdr">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 14 14"></polyline></svg>
          Corpus & Extraction Health
        </div>
        <div style="font-size:12px;color:var(--text-secondary);line-height:1.6;">
          <div>&bull; <b>153 files</b> indexed (~171,717 words)</div>
          <div>&bull; <b>99% Extracted</b> &middot; 1% Inferred</div>
          <div>&bull; <b>0 Import Cycles</b> detected</div>
          <div>&bull; <b>Engine state:</b> 352 passing tests</div>
        </div>
      </div>
    </div>
  </aside>
</main>

<!-- SHORTCUTS MODAL -->
<div id="shortcuts-modal">
  <div class="modal-box">
    <div class="modal-hdr">
      <h3>Keyboard Navigation</h3>
      <button class="modal-close" onclick="closeShortcuts()">&times;</button>
    </div>
    <div class="shortcuts-list">
      <div class="shortcut-row"><span>Focus Search</span><span class="kbd-shortcut">/ or Ctrl+K</span></div>
      <div class="shortcut-row"><span>Fit Network to Screen</span><span class="kbd-shortcut">F</span></div>
      <div class="shortcut-row"><span>Pause / Resume Physics</span><span class="kbd-shortcut">Space</span></div>
      <div class="shortcut-row"><span>Clear Selection / Close</span><span class="kbd-shortcut">Escape</span></div>
      <div class="shortcut-row"><span>Switch Tabs (1-4)</span><span class="kbd-shortcut">1 &middot; 2 &middot; 3 &middot; 4</span></div>
      <div class="shortcut-row"><span>Toggle Sidebar</span><span class="kbd-shortcut">S</span></div>
    </div>
  </div>
</div>

<script>
const RAW_NODES = ''' + raw_nodes_str + r''';
const RAW_EDGES = ''' + raw_edges_str + r''';
const LEGEND = ''' + legend_str + r''';

function esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// Map communities for quick lookup
const commColorMap = {};
const commNameMap = {};
LEGEND.forEach(c => {
  commColorMap[c.cid] = c.color;
  commNameMap[c.cid] = c.label;
});

// Build vis datasets
const nodesDS = new vis.DataSet(RAW_NODES.map(n => ({
  id: n.id, 
  label: n.label, 
  color: {
    background: n.color.background,
    border: n.color.border || n.color.background,
    highlight: {
      background: '#ffffff',
      border: n.color.border || '#6366f1'
    },
    hover: {
      background: '#ffffff',
      border: n.color.border || '#6366f1'
    }
  }, 
  size: Math.max(10, n.size * 1.05),
  font: {
    face: 'Plus Jakarta Sans, sans-serif',
    size: n.font ? n.font.size : 0,
    color: '#e2e8f0',
    strokeWidth: 2,
    strokeColor: '#07090e'
  }, 
  title: n.title,
  _origColor: n.color.background,
  _community: n.community, 
  _community_name: n.community_name || commNameMap[n.community] || ('Cluster ' + n.community),
  _source_file: n.source_file, 
  _file_type: n.file_type, 
  _degree: n.degree || 0,
})));

const edgesDS = new vis.DataSet(RAW_EDGES.map((e, i) => ({
  id: i, 
  from: e.from, 
  to: e.to,
  label: '',
  title: e.title,
  dashes: e.dashes,
  width: e.width || 1,
  color: {
    color: e.color || 'rgba(148, 163, 184, 0.25)',
    highlight: '#818cf8',
    hover: '#38bdf8',
    opacity: 0.35
  },
  arrows: { to: { enabled: true, scaleFactor: 0.45 } },
})));

const container = document.getElementById('graph');
let physicsEnabled = true;

const network = new vis.Network(container, { nodes: nodesDS, edges: edgesDS }, {
  physics: {
    enabled: true,
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {
      gravitationalConstant: -75,
      centralGravity: 0.006,
      springLength: 130,
      springConstant: 0.08,
      damping: 0.5,
      avoidOverlap: 0.85,
    },
    stabilization: { iterations: 180, fit: true },
  },
  interaction: {
    hover: true,
    tooltipDelay: 150,
    hideEdgesOnDrag: true,
    navigationButtons: false,
    keyboard: false,
  },
  nodes: { 
    shape: 'dot', 
    borderWidth: 1.5,
    shadow: {
      enabled: true,
      color: 'rgba(0,0,0,0.5)',
      size: 10,
      x: 0,
      y: 4
    }
  },
  edges: { 
    smooth: { type: 'continuous', roundness: 0.22 }, 
    selectionWidth: 2.5 
  },
});

// Stabilization events
const stabOverlay = document.getElementById('stabilization-overlay');
network.on('stabilizationProgress', params => {
  const pct = Math.round((params.iterations / params.total) * 100);
  document.getElementById('stabilize-msg').textContent = `Calibrating topology: ${pct}%`;
});

network.once('stabilizationIterationsDone', () => {
  stabOverlay.style.opacity = '0';
  setTimeout(() => { stabOverlay.style.display = 'none'; }, 500);
  physicsEnabled = false;
  network.setOptions({ physics: { enabled: false } });
  updatePhysicsBtnState();
});

// Toggle physics button
const btnPhysics = document.getElementById('btn-physics');
function updatePhysicsBtnState() {
  if (physicsEnabled) {
    btnPhysics.classList.add('active');
    document.getElementById('physics-label').textContent = 'Physics (Active)';
  } else {
    btnPhysics.classList.remove('active');
    document.getElementById('physics-label').textContent = 'Physics (Paused)';
  }
}
btnPhysics.onclick = () => {
  physicsEnabled = !physicsEnabled;
  network.setOptions({ physics: { enabled: physicsEnabled } });
  updatePhysicsBtnState();
};

// Fit view
document.getElementById('btn-fit').onclick = () => network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
document.getElementById('hud-fit').onclick = () => network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });

// Zoom controls
document.getElementById('hud-zoom-in').onclick = () => {
  network.moveTo({ scale: network.getScale() * 1.3, animation: true });
};
document.getElementById('hud-zoom-out').onclick = () => {
  network.moveTo({ scale: network.getScale() / 1.3, animation: true });
};

// Toggle Sidebar
const sidebar = document.getElementById('sidebar');
document.getElementById('btn-toggle-sidebar').onclick = () => {
  sidebar.classList.toggle('collapsed');
};

// Export PNG
document.getElementById('btn-export').onclick = () => {
  const canvas = container.querySelector('canvas');
  if (!canvas) return;
  const link = document.createElement('a');
  link.download = 'inspectra-knowledge-graph.png';
  link.href = canvas.toDataURL('image/png');
  link.click();
};

// Neighborhood Spotlight / Dimming
let soloMode = false;
let selectedNodeId = null;

function highlightNeighborhood(nodeId) {
  if (!nodeId) {
    // Reset all
    nodesDS.update(RAW_NODES.map(n => ({
      id: n.id,
      color: {
        background: n.color.background,
        border: n.color.border || n.color.background,
      },
      opacity: 1
    })));
    edgesDS.update(RAW_EDGES.map((e, idx) => ({
      id: idx,
      color: { color: e.color || 'rgba(148, 163, 184, 0.25)', opacity: 0.35 }
    })));
    return;
  }

  const neighbors = new Set(network.getConnectedNodes(nodeId));
  neighbors.add(nodeId);

  nodesDS.update(RAW_NODES.map(n => {
    if (neighbors.has(n.id)) {
      return {
        id: n.id,
        color: { background: n.color.background, border: '#ffffff' },
        opacity: 1
      };
    } else {
      return {
        id: n.id,
        color: { background: '#1e2433', border: '#2d3748' },
        opacity: 0.12
      };
    }
  }));

  const connectedEdges = new Set(network.getConnectedEdges(nodeId));
  edgesDS.update(RAW_EDGES.map((e, idx) => {
    if (connectedEdges.has(idx)) {
      return { id: idx, color: { color: '#6366f1', opacity: 0.9, highlight: '#a5b4fc' }, width: 2.2 };
    } else {
      return { id: idx, color: { color: 'rgba(255,255,255,0.02)', opacity: 0.05 }, width: 0.8 };
    }
  }));
}

document.getElementById('hud-solo-toggle').onclick = () => {
  soloMode = !soloMode;
  document.getElementById('hud-solo-toggle').style.color = soloMode ? 'var(--accent-indigo)' : 'var(--text-secondary)';
  if (selectedNodeId) {
    soloMode ? highlightNeighborhood(selectedNodeId) : highlightNeighborhood(null);
  }
};

// Node Inspector Display
function showInfo(nodeId) {
  selectedNodeId = nodeId;
  const n = nodesDS.get(nodeId);
  if (!n) return;

  if (soloMode) {
    highlightNeighborhood(nodeId);
  }

  // Switch to inspector tab automatically
  switchTab('tab-inspector');

  const neighborIds = network.getConnectedNodes(nodeId);
  const neighborItems = neighborIds.map(nid => {
    const nb = nodesDS.get(nid);
    const color = nb ? (nb._origColor || nb.color.background) : '#6366f1';
    return `<div class="neighbor-link" style="border-left-color:${esc(color)}" data-nid="${esc(nid)}">
      <span>${esc(nb ? nb.label : nid)}</span>
      <span style="font-size:10px;color:var(--text-muted);">${esc(nb ? nb._community_name : '')}</span>
    </div>`;
  }).join('');

  const clusterColor = commColorMap[n._community] || '#6366f1';
  const typeLabel = n._file_type || (n.label.endsWith('()') ? 'function' : (n.label.endsWith('.py') ? 'module' : 'symbol'));

  document.getElementById('inspector-content').innerHTML = `
    <div class="inspector-card">
      <div class="node-title-row">
        <div class="node-title">${esc(n.label)}</div>
        <button class="copy-btn" onclick="navigator.clipboard.writeText('${esc(n.label)}')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          Copy
        </button>
      </div>

      <div class="tags-row">
        <span class="badge badge-type">${esc(typeLabel)}</span>
        <span class="badge badge-community" style="background:${esc(clusterColor)}22; border-color:${esc(clusterColor)}66; color:${esc(clusterColor)}">
          <span style="width:6px;height:6px;border-radius:50%;background:${esc(clusterColor)};display:inline-block;"></span>
          ${esc(n._community_name)}
        </span>
      </div>

      <div class="metrics-grid">
        <div class="metric-box">
          <span class="metric-label">Degree Centrality</span>
          <span class="metric-val" style="color:var(--accent-cyan);">${n._degree}</span>
        </div>
        <div class="metric-box">
          <span class="metric-label">Neighbors</span>
          <span class="metric-val" style="color:var(--accent-emerald);">${neighborIds.length}</span>
        </div>
      </div>

      <div class="source-path-card">
        <span class="source-path-label">Source File Location</span>
        <span class="source-path-val">${esc(n._source_file || 'Internal')}</span>
      </div>

      <div class="neighbors-section">
        <div class="section-hdr">
          <span>Connected Entities</span>
          <span>(${neighborIds.length})</span>
        </div>
        <div id="neighbors-list">
          ${neighborItems || '<span style="font-size:12px;color:var(--text-muted);">No direct connections</span>'}
        </div>
      </div>
    </div>
  `;
}

function focusNode(nodeId) {
  network.focus(nodeId, { scale: 1.5, animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
  network.selectNodes([nodeId]);
  showInfo(nodeId);
}

// Click listener on neighbors
document.addEventListener('click', e => {
  const el = e.target.closest('.neighbor-link');
  if (el && el.dataset.nid !== undefined) focusNode(el.dataset.nid);
});

// Network interaction
network.on('click', params => {
  if (params.nodes.length > 0) {
    showInfo(params.nodes[0]);
  } else {
    selectedNodeId = null;
    highlightNeighborhood(null);
    document.getElementById('inspector-content').innerHTML = `
      <div class="empty-inspector">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"></circle>
          <path d="m10 15 5-3-5-3v6Z"></path>
        </svg>
        <h4>No Node Selected</h4>
        <p>Click any node or symbol in the network or use search (<b>/</b>) to inspect dependencies, source location, and degree centrality.</p>
      </div>
    `;
  }
});

// SEARCH AUTOCOMPLETE
const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');

searchInput.addEventListener('input', () => {
  const q = searchInput.value.toLowerCase().trim();
  searchResults.innerHTML = '';
  if (!q) { searchResults.style.display = 'none'; return; }
  
  const matches = RAW_NODES.filter(n => n.label.toLowerCase().includes(q) || (n.source_file && n.source_file.toLowerCase().includes(q))).slice(0, 25);
  if (!matches.length) { 
    searchResults.innerHTML = '<div style="padding:12px;font-size:12px;color:var(--text-muted);text-align:center;">No matching symbols found</div>';
    searchResults.style.display = 'block';
    return; 
  }
  
  searchResults.style.display = 'block';
  matches.forEach(n => {
    const el = document.createElement('div');
    el.className = 'search-item';
    const dotColor = commColorMap[n.community] || '#6366f1';
    el.innerHTML = `
      <div class="search-item-left">
        <span class="search-item-dot" style="background:${dotColor}"></span>
        <span class="search-item-label">${esc(n.label)}</span>
      </div>
      <span class="search-item-sub">${esc(n.community_name || '')}</span>
    `;
    el.onclick = () => {
      focusNode(n.id);
      searchResults.style.display = 'none';
      searchInput.value = '';
    };
    searchResults.appendChild(el);
  });
});

document.addEventListener('click', e => {
  if (!searchResults.contains(e.target) && e.target !== searchInput) {
    searchResults.style.display = 'none';
  }
});

// TABS LOGIC
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-content').forEach(c => {
    c.classList.toggle('active', c.id === tabId);
  });
}

document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.onclick = () => switchTab(btn.dataset.tab);
});

// COMMUNITIES TAB POPULATION
const hiddenCommunities = new Set();
const legendEl = document.getElementById('legend');

function renderCommunities(filterText = '') {
  legendEl.innerHTML = '';
  const filtered = LEGEND.filter(c => !filterText || c.label.toLowerCase().includes(filterText.toLowerCase()));
  
  filtered.forEach(c => {
    const item = document.createElement('div');
    item.className = 'legend-item' + (hiddenCommunities.has(c.cid) ? ' dimmed' : '');
    
    item.innerHTML = `
      <div class="legend-left">
        <span class="legend-dot" style="background:${c.color}"></span>
        <span class="legend-label">${esc(c.label)}</span>
      </div>
      <div class="legend-right">
        <button class="solo-btn" data-solo="${c.cid}">Solo</button>
        <span class="legend-count">${c.count}</span>
      </div>
    `;
    
    // Toggle community visibility
    item.onclick = (e) => {
      if (e.target.dataset.solo !== undefined) return;
      if (hiddenCommunities.has(c.cid)) {
        hiddenCommunities.delete(c.cid);
        item.classList.remove('dimmed');
      } else {
        hiddenCommunities.add(c.cid);
        item.classList.add('dimmed');
      }
      const updates = RAW_NODES
        .filter(n => n.community === c.cid)
        .map(n => ({ id: n.id, hidden: hiddenCommunities.has(c.cid) }));
      nodesDS.update(updates);
    };

    // Solo button handler
    const soloBtn = item.querySelector('.solo-btn');
    soloBtn.onclick = (e) => {
      e.stopPropagation();
      hiddenCommunities.clear();
      LEGEND.forEach(other => {
        if (other.cid !== c.cid) hiddenCommunities.add(other.cid);
      });
      document.querySelectorAll('.legend-item').forEach(li => {
        li.classList.add('dimmed');
      });
      item.classList.remove('dimmed');
      const updates = RAW_NODES.map(n => ({ id: n.id, hidden: n.community !== c.cid }));
      nodesDS.update(updates);
      network.fit({ animation: true });
    };

    legendEl.appendChild(item);
  });
}

renderCommunities();

document.getElementById('comm-filter').addEventListener('input', (e) => {
  renderCommunities(e.target.value.trim());
});

document.getElementById('comm-all-btn').onclick = () => {
  hiddenCommunities.clear();
  document.querySelectorAll('.legend-item').forEach(i => i.classList.remove('dimmed'));
  nodesDS.update(RAW_NODES.map(n => ({ id: n.id, hidden: false })));
};

document.getElementById('comm-none-btn').onclick = () => {
  LEGEND.forEach(c => hiddenCommunities.add(c.cid));
  document.querySelectorAll('.legend-item').forEach(i => i.classList.add('dimmed'));
  nodesDS.update(RAW_NODES.map(n => ({ id: n.id, hidden: true })));
};

// GOD NODES TAB POPULATION
const godsListEl = document.getElementById('gods-list');
const sortedByDegree = [...RAW_NODES].sort((a, b) => (b.degree || 0) - (a.degree || 0)).slice(0, 15);
const maxDeg = sortedByDegree[0]?.degree || 50;

sortedByDegree.forEach((n, idx) => {
  const godItem = document.createElement('div');
  godItem.className = 'god-item';
  const pct = Math.round(((n.degree || 0) / maxDeg) * 100);
  godItem.innerHTML = `
    <div class="god-header">
      <div class="god-rank-label">
        <span class="god-rank">#${idx+1}</span>
        <span class="god-name">${esc(n.label)}</span>
      </div>
      <span class="god-degree">${n.degree} edges</span>
    </div>
    <div class="god-bar-wrap">
      <div class="god-bar" style="width:${pct}%"></div>
    </div>
  `;
  godItem.onclick = () => focusNode(n.id);
  godsListEl.appendChild(godItem);
});

// KEYBOARD SHORTCUTS
document.addEventListener('keydown', e => {
  if (e.target === searchInput || e.target.tagName === 'INPUT') {
    if (e.key === 'Escape') {
      searchInput.blur();
      searchResults.style.display = 'none';
    }
    return;
  }

  if (e.key === '/' || (e.ctrlKey && e.key === 'k') || (e.metaKey && e.key === 'k')) {
    e.preventDefault();
    searchInput.focus();
  } else if (e.key === 'f' || e.key === 'F') {
    e.preventDefault();
    network.fit({ animation: true });
  } else if (e.key === ' ') {
    e.preventDefault();
    btnPhysics.click();
  } else if (e.key === 's' || e.key === 'S') {
    e.preventDefault();
    sidebar.classList.toggle('collapsed');
  } else if (e.key === '1') {
    switchTab('tab-inspector');
  } else if (e.key === '2') {
    switchTab('tab-communities');
  } else if (e.key === '3') {
    switchTab('tab-gods');
  } else if (e.key === '4') {
    switchTab('tab-audit');
  } else if (e.key === '?') {
    openShortcuts();
  } else if (e.key === 'Escape') {
    closeShortcuts();
    selectedNodeId = null;
    highlightNeighborhood(null);
  }
});

function openShortcuts() {
  document.getElementById('shortcuts-modal').style.display = 'flex';
}
function closeShortcuts() {
  document.getElementById('shortcuts-modal').style.display = 'none';
}
document.getElementById('hud-help').onclick = openShortcuts;
</script>
</body>
</html>'''

    output_path = Path("graphify-out/graph.html")
    output_path.write_text(template, encoding="utf-8")
    print(f"SUCCESS: Wrote modern graph UI to {output_path} ({len(template):,} bytes)")

if __name__ == "__main__":
    build()
