import subprocess
import sys
import os
import re
import time
import webbrowser
import urllib.request

PORT = 8082

def is_local_server_running():
    try:
        req = urllib.request.urlopen(f"http://localhost:{PORT}/api/state", timeout=2)
        return req.getcode() == 200
    except Exception:
        return False

def main():
    os.system("color 0a")
    print("=" * 70)
    print("   SALUMBER DISTRICT PANCHAYATI RAJ ELECTIONS 2026")
    print("   Automated SQLite Engine + Cloudflare Live Public Broadcast")
    print("=" * 70)
    print()

    # Step 1: Ensure local backend is running
    if not is_local_server_running():
        print(f"[*] Starting local backend server on port {PORT}...")
        subprocess.Popen([sys.executable, "app.py", str(PORT)], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        # Wait up to 10 seconds for backend to start
        for _ in range(10):
            time.sleep(1)
            if is_local_server_running():
                print(f"[OK] Backend server is responding on http://localhost:{PORT}")
                break
        else:
            print("[WARN] Backend is taking time to start, continuing...")
    else:
        print(f"[OK] Backend server already running on http://localhost:{PORT}")

    # Step 2: Start Cloudflared tunnel
    print("[*] Launching Cloudflare Tunnel to the internet...")
    cf_proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    tunnel_url = None
    url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

    while True:
        line = cf_proc.stdout.readline()
        if not line and cf_proc.poll() is not None:
            break
        if line:
            # Check for URL
            match = url_pattern.search(line)
            if match and not tunnel_url:
                tunnel_url = match.group(0)
                tv_url = f"{tunnel_url}/tv"
                entry_url = f"{tunnel_url}/entry"

                # Save to text file
                with open("PUBLIC_LIVE_LINK.txt", "w", encoding="utf-8") as f:
                    f.write(f"SALUMBER ELECTIONS 2026 - LIVE PUBLIC BROADCAST LINKS\n")
                    f.write(f"====================================================\n\n")
                    f.write(f"PUBLIC TV DISPLAY (Open on TV / Other computers / Mobiles):\n{tv_url}\n\n")
                    f.write(f"PUBLIC OPERATOR CONSOLE:\n{entry_url}\n\n")
                    f.write(f"LOCAL OPERATOR (This Computer Only):\nhttp://localhost:{PORT}/entry\n")

                # Try to copy to clipboard
                try:
                    subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{tv_url}'"], timeout=3)
                    copied_msg = " [COPIED TO CLIPBOARD! Press Ctrl+V to paste]"
                except Exception:
                    copied_msg = ""

                print()
                print("*" * 75)
                print("           SUCCESS! YOUR LIVE ELECTION SERVER IS NOW ONLINE!        ")
                print("*" * 75)
                print()
                print(f" >> LIVE TV DISPLAY LINK (Send to other computer / projector / mobile):")
                print(f"    {tv_url}{copied_msg}")
                print()
                print(f" >> LIVE OPERATOR ENTRY LINK:")
                print(f"    {entry_url}")
                print()
                print(f" >> Saved to file: PUBLIC_LIVE_LINK.txt (in this folder)")
                print("*" * 75)
                print()

                # Automatically open TV in browser
                try:
                    webbrowser.open(tv_url)
                except Exception:
                    pass

            # Optional: print tunnel heartbeat or logs lightly
            if "Registered tunnel connection" in line or "ERR" in line:
                print(line.strip())

    cf_proc.wait()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopping Cloudflare Tunnel...")
