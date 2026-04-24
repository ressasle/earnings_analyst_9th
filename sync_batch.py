import subprocess
import os
from pathlib import Path

# Config
TICKERS = [
    "AI.PA", "ASML.AS", "DHR.US", "ISRG.US", "LONN.SW",
    "MC.PA", "MMM.US", "NFLX.US", "RMS.PA", "SIKA.SW", "VACN.SW"
]
QUARTER = "Q1"
YEAR = "2026"
BASE_DIR = r"c:\Users\Administrator\Documents\kasonaops\invest_analysis\08_quarterly-earnings-analyst"
ARTIFACTS_DIR = os.path.join(BASE_DIR, "final_artifacts")
MANAGER_SCRIPT = os.path.join(BASE_DIR, "tools", "supabase_storage_manager.py")

def main():
    for ticker in TICKERS:
        ticker_clean = ticker.replace(".", "_")
        
        # Files mapping bucket -> filename
        files = {
            "earnings-reports-pdf": f"{ticker_clean}_report.pdf",
            "earnings-reports-audio": f"{ticker_clean}_briefing.mp3",
            "earnings-reports-html": f"{ticker_clean}_report.html"
        }
        
        for bucket, file_name in files.items():
            file_path = os.path.join(ARTIFACTS_DIR, file_name)
            if not os.path.exists(file_path):
                print(f"[SKIP] {file_name} not found at {file_path}")
                continue
                
            # The manager script handles one file at a time
            # --update-db ensures the corresponding column in quarterly_earnings is updated
            cmd = [
                "python", MANAGER_SCRIPT,
                "--file", file_path,
                "--bucket", bucket,
                "--ticker", ticker,
                "--quarter", QUARTER,
                "--year", YEAR,
                "--update-db"
            ]
            
            print(f"[*] Syncing {ticker} to {bucket}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"    [OK] {file_name} synced.")
            else:
                print(f"    [ERR] {file_name} failed: {result.stderr}")

if __name__ == "__main__":
    main()
