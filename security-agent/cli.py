#!/usr/bin/env python3
"""
Agentic AI Security Scanner — CLI untuk Termux / Terminal
Gunakan langsung tanpa server: python cli.py scan --url https://target.com
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path


# ── ANSI Colors ──────────────────────────────────────────────────────────────

class C:
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    GREEN   = "\033[92m"
    BLUE    = "\033[94m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"


def banner():
    print(f"""{C.CYAN}{C.BOLD}
╔══════════════════════════════════════════════╗
║     Agentic AI Security Scanner  v3          ║
║     Powered by Claude AI (Anthropic)         ║
║     Berjalan di Termux / Android / Linux     ║
╚══════════════════════════════════════════════╝
{C.RESET}""")


def sev_color(sev: str) -> str:
    return {
        "CRITICAL": C.RED + C.BOLD,
        "HIGH":     C.RED,
        "MEDIUM":   C.YELLOW,
        "LOW":      C.BLUE,
        "INFO":     C.DIM,
    }.get(sev, "")


def spin(msg: str, done: asyncio.Event):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    while not done.is_set():
        print(f"\r{C.CYAN}{frames[i % len(frames)]}{C.RESET} {msg}", end="", flush=True)
        time.sleep(0.1)
        i += 1
    print(f"\r{C.GREEN}✓{C.RESET} {msg}")


def print_finding(f: dict, idx: int):
    sev = f.get("severity", "INFO")
    sc  = sev_color(sev)
    print(f"\n  {C.BOLD}[{idx}]{C.RESET} {sc}{sev}{C.RESET}  {C.BOLD}{f.get('title','')}{C.RESET}")
    print(f"       OWASP: {f.get('owasp_category','—')}  CVSS: {f.get('cvss_score', 0):.1f}")
    desc = f.get("description", "")
    if desc:
        print(f"       {C.DIM}{desc[:120]}{'...' if len(desc)>120 else ''}{C.RESET}")
    ev = f.get("evidence", "")
    if ev:
        print(f"       {C.YELLOW}Evidence:{C.RESET} {ev[:100]}")
    rem = f.get("remediation", "")
    if rem:
        print(f"       {C.GREEN}Fix:{C.RESET} {rem[:120]}")


def print_report(report: dict, target: str):
    findings = report.get("findings", [])
    dist     = report.get("severity_distribution", {})
    score    = report.get("risk_score", 0)
    summary  = report.get("executive_summary", "")
    recs     = report.get("recommendations", [])

    color = C.RED if score >= 7 else (C.YELLOW if score >= 4 else C.GREEN)
    print(f"\n{C.BOLD}{'─'*50}{C.RESET}")
    print(f"{C.BOLD}HASIL SCAN: {target}{C.RESET}")
    print(f"{'─'*50}")
    print(f"Risk Score  : {color}{C.BOLD}{score:.1f}/10{C.RESET}")
    print(f"Findings    : {C.RED}{dist.get('CRITICAL',0)} CRITICAL{C.RESET}  "
          f"{C.RED}{dist.get('HIGH',0)} HIGH{C.RESET}  "
          f"{C.YELLOW}{dist.get('MEDIUM',0)} MEDIUM{C.RESET}  "
          f"{C.BLUE}{dist.get('LOW',0)} LOW{C.RESET}")
    if summary:
        print(f"\nRingkasan: {summary[:200]}")

    if findings:
        print(f"\n{C.BOLD}── Temuan Kerentanan ──{C.RESET}")
        for i, f in enumerate(findings, 1):
            print_finding(f, i)

    if recs:
        print(f"\n{C.BOLD}── Rekomendasi ──{C.RESET}")
        for i, r in enumerate(recs[:5], 1):
            print(f"  {i}. {r}")

    print(f"\n{'─'*50}\n")


def save_report(report: dict, target: str, mode: str) -> str:
    out_dir = Path.home() / "security-reports"
    out_dir.mkdir(exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = target.replace("https://", "").replace("http://", "").replace("/", "_")[:30]
    base = out_dir / f"{mode}_{slug}_{ts}"

    base_str = str(base)
    Path(base_str + ".json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    human = report.get("human_readable", "")
    if not human:
        lines  = [f"# Security Report — {target}", f"Risk Score: {report.get('risk_score',0)}/10", ""]
        for f in report.get("findings", []):
            lines += [f"## [{f.get('severity')}] {f.get('title')}",
                      f.get("description",""), f"Fix: {f.get('remediation','')}", ""]
        human = "\n".join(lines)
    Path(base_str + ".md").write_text(human, encoding="utf-8")

    return base_str


# ── Async runners ─────────────────────────────────────────────────────────────

async def _run(coro, label: str) -> dict:
    done = asyncio.Event()
    loop = asyncio.get_event_loop()
    thread = loop.run_in_executor(None, spin, label, done)
    try:
        result = await coro
    finally:
        done.set()
    await thread
    return result.model_dump() if hasattr(result, "model_dump") else result


async def cmd_scan(args):
    from core.orchestrator import Orchestrator
    from core.models import ScanRequest

    orc = Orchestrator()
    target = args.url or args.file

    if args.file:
        content = Path(args.file).read_text(encoding="utf-8", errors="replace")
        req = ScanRequest(target_type="file", target_content=content,
                          filename=Path(args.file).name, scan_profile=args.profile)
    else:
        req = ScanRequest(target_type="url", target_url=args.url, scan_profile=args.profile)

    report = await _run(orc.run_scan(req), f"Scanning {target} ...")
    print_report(report, target)
    path = save_report(report, target, "scan")
    print(f"{C.GREEN}Laporan disimpan:{C.RESET} {path}.json  &  {path}.md\n")


async def cmd_monitor(args):
    from core.orchestrator import Orchestrator
    from core.models import MonitorRequest

    orc = Orchestrator()
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8", errors="replace")
    else:
        print(f"{C.YELLOW}Masukkan konten log (tekan Ctrl+D selesai):{C.RESET}")
        content = sys.stdin.read()

    req = MonitorRequest(log_content=content, log_format=args.format)
    report = await _run(orc.run_monitor(req), "Menganalisis log ...")
    print_report(report, args.file or "log input")
    path = save_report(report, args.file or "log", "monitor")
    print(f"{C.GREEN}Laporan disimpan:{C.RESET} {path}.json\n")


async def cmd_pentest(args):
    from core.orchestrator import Orchestrator
    from core.models import PentestRequest

    orc = Orchestrator()
    scope = args.scope or [args.url]
    req   = PentestRequest(target_url=args.url, scope=scope)
    report = await _run(orc.run_pentest(req), f"Penetration testing {args.url} ...")
    print_report(report, args.url)
    path = save_report(report, args.url, "pentest")
    print(f"{C.GREEN}Laporan disimpan:{C.RESET} {path}.json\n")


async def cmd_deepscan(args):
    from core.orchestrator import Orchestrator
    from core.models import DeepScanRequest

    orc = Orchestrator()
    target = args.url or args.file

    if args.file:
        content = Path(args.file).read_text(encoding="utf-8", errors="replace")
        req = DeepScanRequest(target_content=content, filename=Path(args.file).name,
                              stop_on_critical=not args.no_stop, max_rounds=args.rounds)
    else:
        req = DeepScanRequest(target_url=args.url,
                              scope=args.scope or [args.url],
                              stop_on_critical=not args.no_stop,
                              max_rounds=args.rounds)

    print(f"{C.CYAN}Deep scan: hingga {args.rounds} ronde, berhenti saat CRITICAL={not args.no_stop}{C.RESET}")
    report = await _run(orc.run_deep_scan(req), f"Deep scanning {target} ...")
    print_report(report, target)
    path = save_report(report, target, "deepscan")
    print(f"{C.GREEN}Laporan disimpan:{C.RESET} {path}.json\n")


async def cmd_adaptive(args):
    from core.orchestrator import Orchestrator
    from core.models import AdaptiveScanRequest

    orc = Orchestrator()
    target = args.url or args.file

    if args.file:
        content = Path(args.file).read_text(encoding="utf-8", errors="replace")
        req = AdaptiveScanRequest(target_content=content, filename=Path(args.file).name,
                                  stop_on_critical=not args.no_stop, max_rounds=args.rounds)
    else:
        req = AdaptiveScanRequest(target_url=args.url,
                                  scope=args.scope or [args.url],
                                  stop_on_critical=not args.no_stop,
                                  max_rounds=args.rounds)

    print(f"{C.MAGENTA}Adaptive scan: agent akan membuat tools & skills sendiri{C.RESET}")
    report = await _run(orc.run_adaptive_scan(req), f"Adaptive scanning {target} ...")
    print_report(report, target)
    path = save_report(report, target, "adaptive")
    print(f"{C.GREEN}Laporan disimpan:{C.RESET} {path}.json\n")


async def cmd_audit(args):
    from core.orchestrator import Orchestrator
    from core.models import AuditRequest

    orc = Orchestrator()
    log_content = ""
    if args.log:
        log_content = Path(args.log).read_text(encoding="utf-8", errors="replace")

    req = AuditRequest(
        target_type="full",
        target_url=args.url or "",
        target_content=Path(args.file).read_text(encoding="utf-8", errors="replace") if args.file else "",
        filename=Path(args.file).name if args.file else "",
        log_content=log_content,
        scan_profile=args.profile,
        scope=args.scope or ([args.url] if args.url else []),
    )
    target = args.url or args.file or "target"
    report = await _run(orc.run_full_audit(req), f"Full audit {target} ...")
    print_report(report, target)
    path = save_report(report, target, "audit")
    print(f"{C.GREEN}Laporan disimpan:{C.RESET} {path}.json\n")


# ── Argument Parser ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python cli.py",
        description="Agentic AI Security Scanner — CLI untuk Termux/Android/Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  python cli.py scan --url https://target.com
  python cli.py scan --file login.php --profile full
  python cli.py monitor --file /var/log/nginx/access.log
  python cli.py pentest --url https://target.com --scope https://target.com/*
  python cli.py deepscan --url https://target.com --rounds 3
  python cli.py adaptive --url https://target.com --rounds 5
  python cli.py audit --url https://target.com --file app.php --log access.log
  python cli.py server  # Jalankan REST API di port 8000
        """,
    )
    p.add_argument("--key", metavar="API_KEY", help="Anthropic API key (override .env)")

    sub = p.add_subparsers(dest="command", required=True)

    # ── scan ──
    sc = sub.add_parser("scan", help="Scan kode/URL untuk kerentanan OWASP Top 10")
    g = sc.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="URL website target")
    g.add_argument("--file", help="Path file kode (.php, .py, .js, dll)")
    sc.add_argument("--profile", choices=["quick","standard","full"], default="standard")

    # ── monitor ──
    mo = sub.add_parser("monitor", help="Analisis log Apache/Nginx untuk deteksi serangan")
    mo.add_argument("--file", help="Path file log (opsional, default: stdin)")
    mo.add_argument("--format", choices=["apache","nginx","json","auto"], default="auto")

    # ── pentest ──
    pt = sub.add_parser("pentest", help="Penetration testing terhadap URL target")
    pt.add_argument("--url", required=True)
    pt.add_argument("--scope", nargs="+", metavar="SCOPE", help="URL yang boleh di-test")

    # ── deepscan ──
    ds = sub.add_parser("deepscan", help="Deep scan multi-ronde hingga CRITICAL ditemukan")
    g2 = ds.add_mutually_exclusive_group(required=True)
    g2.add_argument("--url")
    g2.add_argument("--file")
    ds.add_argument("--scope", nargs="+")
    ds.add_argument("--rounds", type=int, default=5, metavar="N", help="Maksimum ronde (1-10)")
    ds.add_argument("--no-stop", action="store_true", help="Lanjutkan walau CRITICAL sudah ditemukan")

    # ── adaptive ──
    ad = sub.add_parser("adaptive", help="Adaptive scan — agent tulis tools & skill sendiri")
    g3 = ad.add_mutually_exclusive_group(required=True)
    g3.add_argument("--url")
    g3.add_argument("--file")
    ad.add_argument("--scope", nargs="+")
    ad.add_argument("--rounds", type=int, default=5)
    ad.add_argument("--no-stop", action="store_true")

    # ── audit ──
    au = sub.add_parser("audit", help="Full audit: scan + monitor + pentest sekaligus")
    au.add_argument("--url")
    au.add_argument("--file", help="File kode untuk di-scan")
    au.add_argument("--log", help="File log untuk di-analisis")
    au.add_argument("--scope", nargs="+")
    au.add_argument("--profile", choices=["quick","standard","full"], default="standard")

    # ── server ──
    sub.add_parser("server", help="Jalankan REST API server di port 8000")

    return p


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args   = parser.parse_args()

    banner()

    # Override API key jika diberikan via CLI
    if args.key:
        os.environ["ANTHROPIC_API_KEY"] = args.key

    # Pastikan API key tersedia
    if args.command != "server" and not os.environ.get("ANTHROPIC_API_KEY"):
        from pathlib import Path
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip()
                    break
    if args.command != "server" and not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"{C.RED}ERROR: ANTHROPIC_API_KEY tidak ditemukan.{C.RESET}")
        print(f"Gunakan: python cli.py --key sk-ant-xxx {args.command} ...")
        print(f"Atau isi di file .env: ANTHROPIC_API_KEY=sk-ant-xxx")
        sys.exit(1)

    COMMANDS = {
        "scan":      cmd_scan,
        "monitor":   cmd_monitor,
        "pentest":   cmd_pentest,
        "deepscan":  cmd_deepscan,
        "adaptive":  cmd_adaptive,
        "audit":     cmd_audit,
    }

    if args.command == "server":
        import uvicorn
        print(f"{C.GREEN}Menjalankan REST API di http://0.0.0.0:8000{C.RESET}")
        print(f"Docs: http://localhost:8000/docs\n")
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
    else:
        try:
            asyncio.run(COMMANDS[args.command](args))
        except KeyboardInterrupt:
            print(f"\n{C.YELLOW}Dibatalkan oleh pengguna.{C.RESET}")
        except Exception as e:
            print(f"\n{C.RED}Error: {e}{C.RESET}")
            sys.exit(1)


if __name__ == "__main__":
    main()
