import os

css = """
/* Modal Styles */
.modal-overlay {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(5px);
    display: flex; justify-content: center; align-items: center;
    z-index: 9999; opacity: 0; visibility: hidden; transition: all 0.3s ease;
}
.modal-overlay.active { opacity: 1; visibility: visible; }
.modal-content {
    background: var(--card-bg); border: 1px solid var(--border-color);
    border-radius: 12px; width: 90%; max-width: 800px; padding: 25px;
    position: relative; transform: translateY(20px); transition: all 0.3s ease;
    box-shadow: 0 15px 30px rgba(0,0,0,0.5);
}
.modal-overlay.active .modal-content { transform: translateY(0); }
.modal-close {
    position: absolute; top: 15px; right: 20px;
    color: var(--text-muted); font-size: 24px; cursor: pointer; transition: color 0.2s;
}
.modal-close:hover { color: var(--accent-red); }
.modal-header { margin-bottom: 20px; font-family: 'Orbitron', sans-serif; font-size: 1.5rem; color: var(--accent-cyan); }
.sparkline-container { cursor: pointer; transition: opacity 0.2s; }
.sparkline-container:hover { opacity: 0.8; filter: drop-shadow(0 0 4px var(--accent-cyan)); }
"""

with open(r"c:\Users\samsung\proj\stockRecommend\app\static\style.css", "a", encoding="utf-8") as f:
    f.write(css)
