#!/usr/bin/env python3
"""
Safely reset WeChat Mac media/runtime caches after key extraction.

This script does not touch message databases, contacts, or msg/ attachments.
It only moves rebuildable network, CDN, temporary upload, and Moments image
cache directories into a timestamped backup folder, then reopens the official
WeChat app.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import time
from datetime import datetime
from pathlib import Path

WECHAT_APP = Path("/Applications/WeChat.app")
CONTAINER_DOCS = Path(
    "~/Library/Containers/com.tencent.xinWeChat/Data/Documents"
).expanduser()
XWECHAT_FILES = CONTAINER_DOCS / "xwechat_files"
CLASH_VERGE_DIR = Path(
    "~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev"
).expanduser()
DEFAULT_CLASH_CONFIG = CLASH_VERGE_DIR / "clash-verge.yaml"
CLASH_UNIX_SOCKET = Path("/tmp/verge/verge-mihomo.sock")

WECHAT_MEDIA_FAKE_IP_FILTERS = [
    "+.qpic.cn",
    "+.qlogo.cn",
    "+.qq.com",
    "+.gtimg.cn",
    "+.gtimg.com",
    "+.tdnsv6.com",
    "+.tdnsstic1.cn",
    "+.weixin.qq.com",
    "+.wechat.com",
    "*.qpic.cn",
    "*.qlogo.cn",
    "*.qq.com",
    "*.gtimg.cn",
    "*.gtimg.com",
    "*.tdnsv6.com",
    "*.tdnsstic1.cn",
    "*.weixin.qq.com",
    "*.wechat.com",
]

WECHAT_MEDIA_DIRECT_RULES = [
    "PROCESS-NAME,WeChat,DIRECT",
    "PROCESS-NAME,WeChatAppEx,DIRECT",
    "PROCESS-NAME,WeChatAppEx Helper,DIRECT",
    "PROCESS-NAME,WeChatAppEx Helper (Renderer),DIRECT",
    "PROCESS-NAME,WeChatAppEx Helper (GPU),DIRECT",
    "PROCESS-NAME,wxocr,DIRECT",
    "PROCESS-NAME,wxplayer,DIRECT",
    "PROCESS-NAME,wxutility,DIRECT",
    "DOMAIN-SUFFIX,gtimg.cn,DIRECT",
    "DOMAIN-SUFFIX,gtimg.com,DIRECT",
    "DOMAIN-SUFFIX,qpic.cn,DIRECT",
    "DOMAIN-SUFFIX,qlogo.cn,DIRECT",
    "DOMAIN-SUFFIX,tdnsv6.com,DIRECT",
    "DOMAIN-SUFFIX,tdnsstic1.cn,DIRECT",
    "DOMAIN-SUFFIX,qq.com,DIRECT",
]

WECHAT_MEDIA_HOSTS = [
    "mmbiz.qpic.cn",
    "wx.qlogo.cn",
    "thirdwx.qlogo.cn",
    "res.wx.qq.com",
]


def run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True, check=check)


def yaml_scalar(value: str) -> str:
    if value.startswith("*"):
        return f"'{value}'"
    return value


def strip_yaml_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def add_fake_ip_filters(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "fake-ip-filter:":
            continue
        indent = line[: len(line) - len(line.lstrip())]
        existing: set[str] = set()
        cursor = index + 1
        while cursor < len(lines):
            current = lines[cursor]
            stripped = current.strip()
            if stripped.startswith("- "):
                existing.add(strip_yaml_quotes(stripped[2:]))
                cursor += 1
                continue
            if stripped == "" or stripped.startswith("#"):
                cursor += 1
                continue
            current_indent = len(current) - len(current.lstrip())
            if current_indent <= len(indent):
                break
            cursor += 1

        missing = [item for item in WECHAT_MEDIA_FAKE_IP_FILTERS if item not in existing]
        if not missing:
            return text, []
        insert = [f"{indent}- {yaml_scalar(item)}" for item in missing]
        return "\n".join(lines[: index + 1] + insert + lines[index + 1 :]) + "\n", missing
    return text, []


def add_direct_rules(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines()
    existing = {line.strip()[2:] for line in lines if line.strip().startswith("- ")}
    missing = [rule for rule in WECHAT_MEDIA_DIRECT_RULES if rule not in existing]
    if not missing:
        return text, []

    for index, line in enumerate(lines):
        if line.strip() == "rules:":
            insert = [f"- {rule}" for rule in missing]
            return "\n".join(lines[: index + 1] + insert + lines[index + 1 :]) + "\n", missing
    return text, []


def reload_clash_config(config_path: Path) -> None:
    if not CLASH_UNIX_SOCKET.exists():
        print(f"[WARN] Clash Unix socket not found, skip hot reload: {CLASH_UNIX_SOCKET}")
        return
    payload = json.dumps({"path": str(config_path)}, ensure_ascii=False)
    result = run(
        [
            "curl",
            "--unix-socket",
            str(CLASH_UNIX_SOCKET),
            "-s",
            "-X",
            "PUT",
            "--max-time",
            "8",
            "-H",
            "Content-Type: application/json",
            "--data",
            payload,
            "-w",
            "\nHTTP_STATUS:%{http_code}\n",
            "http://mihomo/configs",
        ]
    )
    print(result.stdout.strip())
    if "HTTP_STATUS:204" not in result.stdout:
        print(f"[WARN] Clash hot reload may have failed: {result.stderr.strip()}")


def flush_dns_cache() -> None:
    run(["dscacheutil", "-flushcache"])
    run(["killall", "-HUP", "mDNSResponder"])


def fix_clash_media_rules(
    config_path: Path,
    *,
    dry_run: bool,
    no_reload: bool,
) -> None:
    if not config_path.exists():
        print(f"skip missing Clash config {config_path}")
        return

    original = config_path.read_text(encoding="utf-8")
    updated, fake_ip_missing = add_fake_ip_filters(original)
    updated, direct_missing = add_direct_rules(updated)

    print(f"clash_config={config_path}")
    if fake_ip_missing:
        print("missing fake-ip-filter entries:")
        for item in fake_ip_missing:
            print(f"  {item}")
    if direct_missing:
        print("missing DIRECT rules:")
        for item in direct_missing:
            print(f"  {item}")
    if not fake_ip_missing and not direct_missing:
        print("Clash WeChat media rules already look complete.")
        return

    backup = config_path.with_name(
        f"{config_path.name}.before-wechat-media-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )
    print(f"backup={backup}")
    if dry_run:
        print("[dry-run] Would update Clash WeChat media DIRECT/fake-ip rules.")
        return

    shutil.copy2(config_path, backup)
    config_path.write_text(updated, encoding="utf-8")
    if no_reload:
        print("Skipped Clash hot reload because --no-clash-reload was set.")
    else:
        reload_clash_config(config_path)
        flush_dns_cache()


def find_process_lines(patterns: tuple[str, ...]) -> list[str]:
    result = run(["ps", "-axo", "pid=,args="])
    matches: list[str] = []
    for line in result.stdout.splitlines():
        item = line.strip()
        if item and any(pattern in item for pattern in patterns):
            matches.append(item)
    return matches


def verify_official_wechat() -> None:
    print("\n[verify] Official WeChat runtime")
    if not WECHAT_APP.exists():
        print(f"FAIL missing official WeChat: {WECHAT_APP}")
        return

    result = run(["spctl", "--assess", "--type", "execute", "--verbose=2", str(WECHAT_APP)])
    combined = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part)
    status = "OK" if result.returncode == 0 else "WARN"
    print(f"{status} spctl: {combined}")

    official_pids = find_official_wechat_pids()
    print(f"OK official_pids={official_pids}" if official_pids else "WARN official WeChat is not running")

    suspicious = [
        line
        for line in find_process_lines(("frida", "gadget", "/Desktop/WeChat.app"))
        if "repair_wechat_media_runtime.py" not in line
    ]
    if suspicious:
        print("WARN suspicious/capture-runtime processes:")
        for line in suspicious:
            print(f"  {line}")
    else:
        print("OK no frida/gadget/Desktop WeChat runtime found")


def verify_clash_rules(config_path: Path) -> None:
    print("\n[verify] Clash WeChat media rules")
    if not config_path.exists():
        print(f"SKIP missing Clash config: {config_path}")
        return
    text = config_path.read_text(encoding="utf-8")
    _, missing_fake_ip = add_fake_ip_filters(text)
    _, missing_direct = add_direct_rules(text)
    if missing_fake_ip or missing_direct:
        print("WARN missing Clash media rules")
        for item in missing_fake_ip:
            print(f"  fake-ip-filter: {item}")
        for item in missing_direct:
            print(f"  rule: {item}")
    else:
        print("OK Clash config contains WeChat media fake-ip filters and DIRECT rules")

    if not CLASH_UNIX_SOCKET.exists():
        print(f"SKIP Clash Unix socket not found: {CLASH_UNIX_SOCKET}")
        return
    result = run(
        [
            "curl",
            "--unix-socket",
            str(CLASH_UNIX_SOCKET),
            "-s",
            "--max-time",
            "6",
            "http://mihomo/rules",
        ]
    )
    try:
        rules = json.loads(result.stdout).get("rules", [])
    except json.JSONDecodeError:
        print("WARN could not read live Clash rules")
        return
    wanted = {rule.split(",", 2)[1] for rule in WECHAT_MEDIA_DIRECT_RULES}
    live = {
        rule.get("payload"): rule.get("proxy")
        for rule in rules
        if rule.get("payload") in wanted
    }
    missing_live = sorted(item for item in wanted if live.get(item) != "DIRECT")
    if missing_live:
        print(f"WARN live Clash rules missing DIRECT payloads: {', '.join(missing_live)}")
    else:
        print("OK live Clash rules have WeChat media DIRECT payloads")


def resolve_host(host: str) -> list[str]:
    result = run(["dscacheutil", "-q", "host", "-a", "name", host])
    addresses: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("ip_address:"):
            addresses.append(line.split(":", 1)[1].strip())
    return addresses


def verify_media_dns() -> None:
    print("\n[verify] WeChat media DNS")
    for host in WECHAT_MEDIA_HOSTS:
        addresses = resolve_host(host)
        fake = [addr for addr in addresses if addr.startswith("198.18.")]
        if fake:
            print(f"WARN {host} resolves to fake-ip: {', '.join(fake)}")
        elif addresses:
            print(f"OK {host} real IPv4: {', '.join(addresses[:4])}")
        else:
            print(f"WARN {host} has no IPv4 result from dscacheutil")


def verify_cache_paths(wxid: str | None) -> None:
    print("\n[verify] Rebuildable cache path permissions")
    if not wxid:
        print(f"SKIP no wxid db_storage found under {XWECHAT_FILES}")
        return
    for path in rebuildable_paths(wxid, include_sns_img=True):
        if not path.exists():
            print(f"WARN missing rebuildable path: {path}")
            continue
        mode = path.stat().st_mode & 0o777
        writable = os.access(path, os.W_OK)
        status = "OK" if writable else "WARN"
        print(f"{status} {oct(mode)} writable={writable} {path}")


def verify_runtime(config_path: Path) -> None:
    print("Read-only verification. No WeChat databases, messages, contacts, or attachments are modified.")
    verify_official_wechat()
    verify_clash_rules(config_path)
    verify_media_dns()
    verify_cache_paths(find_current_wxid())


def find_current_wxid() -> str | None:
    candidates = []
    for path in XWECHAT_FILES.glob("wxid_*/db_storage"):
        wxid_dir = path.parent
        if (path / "message/message_0.db").exists():
            candidates.append(wxid_dir)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0].name


def find_official_wechat_pids() -> list[int]:
    result = run(["ps", "-axo", "pid=,args="])
    pids = []
    for line in result.stdout.splitlines():
        item = line.strip()
        if not item:
            continue
        pid_text, _, args = item.partition(" ")
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if args.startswith(f"{WECHAT_APP}/Contents/"):
            pids.append(pid)
    return sorted(set(pids))


def quit_wechat(*, dry_run: bool) -> None:
    if dry_run:
        print("[dry-run] Would ask official WeChat to quit.")
        print(f"[dry-run] Running official WeChat pids: {find_official_wechat_pids()}")
        return

    run(["osascript", "-e", 'tell application id "com.tencent.xinWeChat" to quit'])
    for _ in range(30):
        if not run(["pgrep", "-x", "WeChat"]).stdout.strip():
            break
        time.sleep(0.5)

    pids = find_official_wechat_pids()
    if pids:
        print(f"Terminating official WeChat helper pids: {', '.join(map(str, pids))}")
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    for _ in range(20):
        alive = []
        for pid in pids:
            try:
                os.kill(pid, 0)
                alive.append(pid)
            except ProcessLookupError:
                pass
        if not alive:
            break
        time.sleep(0.25)
    if alive:
        print(f"[WARN] Some WeChat helper pids are still alive: {alive}")


def rebuildable_paths(wxid: str, *, include_sns_img: bool) -> list[Path]:
    account = XWECHAT_FILES / wxid
    current_month = datetime.now().strftime("%Y-%m")
    sns_base = account / "cache" / current_month / "Sns"
    paths = [
        CONTAINER_DOCS / "app_data/net/cdncomm",
        CONTAINER_DOCS / "app_data/radium/cache",
        sns_base / "Temp",
        account / "temp/InputTemp",
        account / "temp/ImageTemp",
    ]
    if include_sns_img:
        paths.append(sns_base / "Img")
    return paths


def move_to_backup(paths: list[Path], backup_root: Path, *, dry_run: bool) -> None:
    for path in paths:
        if not path.exists():
            print(f"skip missing {path}")
            continue
        relative = path.relative_to(CONTAINER_DOCS)
        dest = backup_root / relative
        if dest.exists():
            dest = dest.with_name(f"{dest.name}_{datetime.now().strftime('%H%M%S')}")
        print(f"move {path} -> {dest}")
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))

    for path in paths:
        if dry_run:
            print(f"[dry-run] Would recreate {path}")
            continue
        path.mkdir(parents=True, exist_ok=True)
        if path.name in {"Img", "Sns"}:
            os.chmod(path, 0o700)


def reopen_official_wechat(*, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] Would open {WECHAT_APP}")
        return
    run(["open", str(WECHAT_APP)])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Safely reset rebuildable WeChat media/CDN runtime caches.",
    )
    parser.add_argument("--wxid", default=None, help="WeChat account wxid directory name.")
    parser.add_argument(
        "--include-sns-img",
        action="store_true",
        help="Also move current-month Moments image cache. Use when Moments images still fail.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--no-reopen",
        action="store_true",
        help="Do not reopen /Applications/WeChat.app after cache reset.",
    )
    parser.add_argument(
        "--fix-clash-media-rules",
        action="store_true",
        help="Patch Clash Verge rules so WeChat media CDN domains are DIRECT and excluded from fake-ip.",
    )
    parser.add_argument(
        "--clash-config",
        type=Path,
        default=DEFAULT_CLASH_CONFIG,
        help="Clash Verge generated config path.",
    )
    parser.add_argument(
        "--no-clash-reload",
        action="store_true",
        help="Do not hot-reload Clash after patching rules.",
    )
    parser.add_argument(
        "--clash-only",
        action="store_true",
        help="Only patch Clash Verge WeChat media rules; do not reset WeChat caches.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Read-only verification of official WeChat runtime, Clash rules, media DNS, and cache permissions.",
    )
    args = parser.parse_args()

    if args.verify:
        verify_runtime(args.clash_config.expanduser())
        return

    if args.clash_only and not args.fix_clash_media_rules:
        raise SystemExit("--clash-only requires --fix-clash-media-rules")

    if args.clash_only:
        fix_clash_media_rules(
            args.clash_config.expanduser(),
            dry_run=args.dry_run,
            no_reload=args.no_clash_reload,
        )
        print("Done. Clash-only mode did not touch WeChat caches.")
        return

    if not WECHAT_APP.exists():
        raise SystemExit(f"Official WeChat not found: {WECHAT_APP}")
    wxid = args.wxid or find_current_wxid()
    if not wxid:
        raise SystemExit(f"No wxid db_storage found under {XWECHAT_FILES}")

    backup_root = CONTAINER_DOCS / f".codex_safe_cache_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    paths = rebuildable_paths(wxid, include_sns_img=args.include_sns_img)

    print(f"wxid={wxid}")
    print(f"backup_root={backup_root}")
    print("This will not touch db_storage, msg/, contacts, or message databases.")
    for path in paths:
        print(f"target={path}")

    if args.fix_clash_media_rules:
        fix_clash_media_rules(
            args.clash_config.expanduser(),
            dry_run=args.dry_run,
            no_reload=args.no_clash_reload,
        )

    quit_wechat(dry_run=args.dry_run)
    move_to_backup(paths, backup_root, dry_run=args.dry_run)
    if not args.no_reopen:
        reopen_official_wechat(dry_run=args.dry_run)

    print("Done. If anything looks wrong, restore by quitting WeChat and moving files back from:")
    print(backup_root)


if __name__ == "__main__":
    main()
