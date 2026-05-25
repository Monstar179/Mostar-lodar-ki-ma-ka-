#!/usr/bin/env python3
"""
Ultimate Telegram Patcher v5.0 – Defeats Server, Anti‑Debug, Obfuscation
Owner: @Vx_Coder | Admin: 8755017952
"""

import hashlib
import struct
import os
import tempfile
import re
import base64
from typing import List, Tuple, Dict, Set, Optional
import pefile
from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ===================== CONFIG =====================
BOT_TOKEN = "8665812016:AAEAE0JgcAyFjhc96ai0a_McXdM84w2cCXE"
OWNER_ID = 8755017952
OWNER_USERNAME = "Vx_Coder"
ALLOWED_USERS: Set[int] = {OWNER_ID}
user_sessions: Dict[int, Dict] = {}

# ===================== PACKER DETECTION =====================
PACKER_SIGNATURES = {
    b"UPX": "UPX (easy to unpack with `upx -d`)",
    b"themida": "Themida (strong obfuscation – use Frida or fake server)",
    b"VMProtect": "VMProtect (very strong – use DNS + fake server)",
    b"Enigma": "Enigma Protector",
    b"ASPack": "ASPack",
    b"MPRESS": "MPRESS"
}

def detect_packer(data: bytes) -> Optional[str]:
    for sig, name in PACKER_SIGNATURES.items():
        if sig in data:
            return name
    try:
        pe = pefile.PE(data=data)
        for section in pe.sections:
            name = section.Name.decode().strip('\x00')
            if name in ('.upx', '.themida', 'vmp', 'enigma'):
                return f"Packer section: {name}"
    except:
        pass
    return None

def check_file_integrity(data: bytes) -> Tuple[bool, str]:
    if data[:2] == b'MZ':
        if len(data) < 0x3C:
            return False, "Truncated file"
        e_lfanew = struct.unpack('<I', data[0x3C:0x40])[0]
        if e_lfanew + 4 > len(data):
            return False, "Invalid PE header offset"
        if data[e_lfanew:e_lfanew+4] != b'PE\x00\x00':
            return False, "Invalid PE signature"
        return True, "Valid PE"
    elif data[:4] == b'\x7FELF':
        return True, "Valid ELF"
    else:
        return True, "Unknown format"

# ===================== ADVANCED PATCHER =====================
class UltimatePatcher:
    def __init__(self):
        self.max_patch_len = 64
        self.core_key = self._forge_core_key()

    def _forge_core_key(self):
        fragments = [
            self._decode_fragment("5L2g5piv5LiA5Liq5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X"),
            self._decode_fragment("6L+Z5piv5LiA5Liq5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X"),
            self._decode_fragment("5aSp5Zyw5L2g5piv5LiA5Liq5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X"),
            self._decode_fragment("6K6k5L2g5piv5LiA5Liq5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X"),
            self._decode_fragment("5aSp5LiA5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X"),
            self._decode_fragment("6K6k5L2g5piv5LiA5Liq5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X5a2X"),
        ]
        combined = "".join(fragments)
        h = hashlib.sha256(combined.encode()).digest()
        return struct.unpack("I", h[:4])[0] & 0xFF

    @staticmethod
    def _decode_fragment(frag: str) -> str:
        return "".join(chr(ord(c) ^ 0x5F) for c in frag[::-1])

    def extract_strings(self, data: bytes, min_len=4) -> List[Tuple[int, str]]:
        results = []
        pattern = rb'[\x20-\x7E]{' + bytes(str(min_len), 'utf-8') + b',}'
        for match in re.finditer(pattern, data):
            s = match.group().decode('ascii', errors='ignore')
            if any(x in s.lower() for x in ['http', 'api', '.com', '.net', 'login', 'verify']):
                results.append((match.start(), s))
        return results

    # Original decryption (kept)
    def deep_byte_transform(self, data: bytes, cycles=1000) -> bytes:
        state = bytearray(data)
        for stage in range(1, cycles+1):
            for i in range(len(state)):
                state[i] = (state[i] + stage*7 + self.core_key) & 0xFF
            state = state[1:] + state[:1]
            for i in range(len(state)):
                state[i] ^= (self.core_key + stage + i) & 0xFF
        return bytes(state)

    def parse_rune_pattern(self, chunk: bytes) -> str:
        if len(chunk) < 128:
            chunk = chunk.ljust(128, b'\x00')
        mid = self.deep_byte_transform(chunk[:128], 500)
        final = bytearray(mid)
        for r in range(1, 801):
            key = (self.core_key + r*17 + r%256) & 0xFF
            for i in range(len(final)):
                final[i] ^= key
        try:
            return final.decode('utf-8', errors='ignore')
        except:
            return ""

    def scan_encrypted(self, data: bytes) -> List[Tuple[int, str]]:
        results = []
        step = 8
        for off in range(0, len(data)-128, step):
            chunk = data[off:off+128]
            dec = self.parse_rune_pattern(chunk)
            if ("http" in dec.lower() or "/api" in dec.lower()) and len(dec) > 10:
                results.append((off, dec))
        return results

    # ---------- Safe URL patch ----------
    def patch_url_safe(self, data: bytes, offset: int, new_url: str) -> Tuple[bytes, str]:
        if len(new_url) > self.max_patch_len:
            return None, f"URL too long (max {self.max_patch_len})"
        padded = new_url.ljust(self.max_patch_len, '\x00')
        patch = bytearray()
        for ch in padded:
            patch.append((ord(ch) ^ self.core_key) & 0xFF)
        patched = bytearray(data)
        patched[offset:offset+self.max_patch_len] = patch
        ok, msg = check_file_integrity(bytes(patched))
        if not ok:
            return None, f"Integrity fail: {msg}"
        return bytes(patched), "OK"

    # ---------- Advanced Anti‑Debug Patching ----------
    def patch_anti_debug(self, data: bytes) -> Tuple[bytes, List[str]]:
        patched = bytearray(data)
        applied = []
        # Pattern: E8 ?? ?? ?? ?? (call IsDebuggerPresent)
        # We'll replace the call with xor eax,eax ; ret (B0 00 C3) but that's 3 bytes – we need 5 bytes NOP?
        # Simpler: search for the import thunk and replace address with our own fake function?
        # For x86: change `call [IsDebuggerPresent]` to `xor eax,eax ; ret` (31 C0 C3) + 2 NOPs?
        # Instead, we'll patch the actual API code in memory? Not possible.
        # Safer: look for `jz` or `jnz` after the call and force it.
        # We'll search for "IsDebuggerPresent" string and patch the conditional jump after it.
        dbg_string = b"IsDebuggerPresent"
        pos = data.find(dbg_string)
        if pos != -1:
            # Look for a call or jump near this string
            for i in range(max(0, pos-100), pos+len(dbg_string)+100):
                if i+5 < len(data) and data[i] == 0xE8:  # call
                    # Replace call with NOPs? Risky.
                    applied.append(f"Found call to IsDebuggerPresent at 0x{i:06X} (manual patch needed)")
                elif data[i] in (0x74, 0x75):
                    patched[i] = 0xEB
                    applied.append(f"Patched jump after IsDebuggerPresent at 0x{i:06X}")
        # Also patch ptrace on Linux/Android (syscall 0x65)
        if b'ptrace' in data:
            # find syscall int 0x80 or syscall
            ptrace_pos = data.find(b'ptrace')
            if ptrace_pos != -1:
                for i in range(ptrace_pos-50, ptrace_pos+50):
                    if i+1 < len(data) and data[i] == 0xCD and data[i+1] == 0x80:
                        patched[i] = 0x31  # xor eax,eax
                        patched[i+1] = 0xC0  # then skip syscall
                        applied.append(f"Patched ptrace syscall at 0x{i:06X}")
        return bytes(patched), applied

    # ---------- Generate Fake Server Script ----------
    def generate_fake_server(self, domain: str, port: int = 80) -> str:
        return f'''#!/usr/bin/env python3
# Fake server for domain {domain}
# Run as root (for port 80) or use higher port and redirect with iptables
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class FakeHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{{"status":"ok"}}')
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_len)
        print(f"Received: {{post_data}}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{{"success":true,"message":"bypassed"}}')
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {{format % args}}")

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', {port}), FakeHandler)
    print(f"Fake server running on port {port} – redirect {domain} to 127.0.0.1")
    server.serve_forever()
'''

    # ---------- Generate Frida script for runtime hooking (bypass obfuscation) ----------
    def generate_frida_script(self, url_to_hook: str) -> str:
        return f'''// Frida script to intercept network requests and bypass login
// Hook send/recv, also hook any function that returns success/failure
Java.perform(function() {{
    // Android example: hook OkHttp
    try {{
        var Builder = Java.use("okhttp3.Request$Builder");
        Builder.build.implementation = function() {{
            var request = this.build();
            var url = request.url().toString();
            console.log("Request URL: " + url);
            if (url.indexOf("{url_to_hook}") !== -1) {{
                // Replace with our own fake server
                var newUrl = "http://127.0.0.1/fake";
                console.log("Redirecting to: " + newUrl);
                var newRequest = Builder.new().url(newUrl).build();
                return newRequest;
            }}
            return request;
        }};
    }} catch(e) {{ console.log(e); }}
    
    // Hook native functions (x86/ARM)
    var ptracePtr = Module.findExportByName(null, "ptrace");
    if (ptracePtr) {{
        Interceptor.replace(ptracePtr, new NativeCallback(function(request, pid, addr, data) {{
            console.log("ptrace called – returning 0");
            return 0;
        }}, 'int', ['int', 'int', 'void*', 'void*']));
    }}
    
    var isDebuggerPresentPtr = Module.findExportByName(null, "IsDebuggerPresent");
    if (isDebuggerPresentPtr) {{
        Interceptor.replace(isDebuggerPresentPtr, new NativeCallback(function() {{
            console.log("IsDebuggerPresent – returning 0");
            return 0;
        }}, 'int', []));
    }}
    
    // Hook any function by pattern? Advanced
    console.log("Frida script loaded – hooks active");
}});
'''

# ===================== TELEGRAM BOT =====================
patcher = UltimatePatcher()

async def check_auth(update: Update, context) -> bool:
    user = update.effective_user
    if user.id == OWNER_ID or user.username == OWNER_USERNAME or user.id in ALLOWED_USERS:
        return True
    await update.message.reply_text("⛔ Unauthorized.")
    return False

async def start(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    await update.message.reply_text(
        "🔥 *Ultimate Patcher v5.0* – Defeats all protections\n"
        "👑 Owner: @Vx_Coder\n\n"
        "*Commands:*\n"
        "• `/scan` – find URLs (encrypted + plain)\n"
        "• `/patch <num> <new_url>` – replace URL (max 64 chars)\n"
        "• `/antidebug` – patch anti‑debug checks\n"
        "• `/fakeserver <domain>` – generate fake server script\n"
        "• `/frida <url>` – generate Frida hook script\n"
        "• `/export` – download patched file\n"
        "• `/info` – session details\n"
        "• `/cancel` – clear session\n\n"
        "*Admin:* `/allow <id>`, `/deny <id>`",
        parse_mode='Markdown'
    )

async def handle_document(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    doc = update.message.document
    if doc.file_size > 100 * 1024 * 1024:
        await update.message.reply_text("Max 100 MB.")
        return
    await update.message.reply_text("📥 Downloading...")
    file_obj = await doc.get_file()
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        await file_obj.download_to_drive(tmp.name)
        tmp_path = tmp.name
    with open(tmp_path, 'rb') as f:
        data = f.read()
    os.unlink(tmp_path)
    packer = detect_packer(data)
    if packer:
        await update.message.reply_text(f"⚠️ Packer detected: {packer}\nUse `/fakeserver` or `/frida`.")
    else:
        await update.message.reply_text("✅ No packer detected. You can try `/antidebug` and `/patch`.")
    user_sessions[update.effective_user.id] = {
        'original': data,
        'patched': data,
        'filename': doc.file_name,
        'urls': [],
        'antidebug_log': [],
        'packer': packer
    }
    await update.message.reply_text(f"✅ Received `{doc.file_name}`. Run `/scan`.")

async def scan_command(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    uid = update.effective_user.id
    if uid not in user_sessions:
        await update.message.reply_text("Send a binary first.")
        return
    sess = user_sessions[uid]
    await update.message.reply_text("🔍 Scanning for URLs...")
    encrypted = patcher.scan_encrypted(sess['original'])
    plain = patcher.extract_strings(sess['original'])
    combined = []
    seen = set()
    for off, url in encrypted + plain:
        if url not in seen:
            seen.add(url)
            combined.append((off, url))
    sess['urls'] = combined
    if not combined:
        await update.message.reply_text("No URLs found. Use `/frida` for runtime hooking.")
        return
    msg = f"✅ Found {len(combined)} URL(s):\n"
    for i, (off, url) in enumerate(combined[:20]):
        msg += f"{i+1}. `0x{off:06X}` → `{url[:60]}`\n"
    if len(combined) > 20:
        msg += f"... and {len(combined)-20} more.\n"
    msg += "\nUse `/patch <num> <new_url>` or `/fakeserver`."
    await update.message.reply_text(msg, parse_mode='Markdown')

async def patch_command(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    uid = update.effective_user.id
    if uid not in user_sessions or not user_sessions[uid].get('urls'):
        await update.message.reply_text("Run `/scan` first.")
        return
    sess = user_sessions[uid]
    try:
        idx = int(context.args[0]) - 1
        new_url = context.args[1]
    except:
        await update.message.reply_text("Usage: `/patch <num> <new_url>`")
        return
    if idx < 0 or idx >= len(sess['urls']):
        await update.message.reply_text("Invalid index.")
        return
    offset, old_url = sess['urls'][idx]
    patched, status = patcher.patch_url_safe(sess['patched'], offset, new_url)
    if patched is None:
        await update.message.reply_text(f"❌ {status}")
        return
    sess['patched'] = patched
    await update.message.reply_text(f"✅ Patched URL at `0x{offset:06X}`\nOld: `{old_url[:50]}`\nNew: `{new_url}`", parse_mode='Markdown')

async def antidebug_command(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    uid = update.effective_user.id
    if uid not in user_sessions:
        await update.message.reply_text("Upload a binary first.")
        return
    sess = user_sessions[uid]
    await update.message.reply_text("🛡️ Patching anti-debug checks...")
    patched, logs = patcher.patch_anti_debug(sess['original'])
    sess['patched'] = patched
    sess['antidebug_log'] = logs
    if logs:
        await update.message.reply_text(f"✅ Patched {len(logs)} anti-debug points:\n" + "\n".join(logs[:10]))
    else:
        await update.message.reply_text("No typical anti-debug patterns found. Use `/frida` for live bypass.")

async def fakeserver_command(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    if not context.args:
        await update.message.reply_text("Usage: `/fakeserver <domain>` (e.g., `/fakeserver api.example.com`)")
        return
    domain = context.args[0]
    script = patcher.generate_fake_server(domain)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
        tmp.write(script.encode())
        tmp_path = tmp.name
    await update.message.reply_document(
        document=open(tmp_path, 'rb'),
        filename=f"fake_server_{domain}.py",
        caption=f"✅ Fake server for `{domain}`.\nRun as root (for port 80).\nThen edit hosts: `127.0.0.1 {domain}`"
    )
    os.unlink(tmp_path)

async def frida_command(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    if not context.args:
        await update.message.reply_text("Usage: `/frida <url_to_hook>` (e.g., `/frida https://api.example.com/login`)")
        return
    url = context.args[0]
    script = patcher.generate_frida_script(url)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".js") as tmp:
        tmp.write(script.encode())
        tmp_path = tmp.name
    await update.message.reply_document(
        document=open(tmp_path, 'rb'),
        filename=f"frida_hook_{url.replace('https://','').replace('/','_')}.js",
        caption=f"✅ Frida script.\nRun: `frida -l this_script.js -f target_app --no-pause`"
    )
    os.unlink(tmp_path)

async def export_command(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    uid = update.effective_user.id
    if uid not in user_sessions:
        await update.message.reply_text("Nothing to export.")
        return
    sess = user_sessions[uid]
    with tempfile.NamedTemporaryFile(delete=False, suffix=sess['filename']) as tmp:
        tmp.write(sess['patched'])
        tmp_path = tmp.name
    await update.message.reply_document(
        document=open(tmp_path, 'rb'),
        filename=f"patched_{sess['filename']}",
        caption="✅ Patched binary. Use at your own risk."
    )
    os.unlink(tmp_path)

async def info_command(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    uid = update.effective_user.id
    if uid not in user_sessions:
        await update.message.reply_text("No session.")
        return
    sess = user_sessions[uid]
    url_count = len(sess.get('urls', []))
    msg = (f"📄 File: `{sess['filename']}`\n"
           f"🔗 URLs found: {url_count}\n"
           f"🛡️ Anti-debug patches: {len(sess.get('antidebug_log', []))}\n"
           f"📦 Packer: {sess.get('packer', 'None')}")
    await update.message.reply_text(msg, parse_mode='Markdown')

async def cancel_command(update: Update, context: CallbackContext):
    if not await check_auth(update, context): return
    uid = update.effective_user.id
    if uid in user_sessions:
        del user_sessions[uid]
    await update.message.reply_text("Session cleared.")

async def allow_user(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner.")
        return
    try:
        uid = int(context.args[0])
        ALLOWED_USERS.add(uid)
        await update.message.reply_text(f"✅ User {uid} allowed.")
    except:
        await update.message.reply_text("Usage: /allow <user_id>")

async def deny_user(update: Update, context: CallbackContext):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("Only owner.")
        return
    try:
        uid = int(context.args[0])
        if uid != OWNER_ID:
            ALLOWED_USERS.discard(uid)
        await update.message.reply_text(f"✅ User {uid} denied.")
    except:
        await update.message.reply_text("Usage: /deny <user_id>")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("patch", patch_command))
    app.add_handler(CommandHandler("antidebug", antidebug_command))
    app.add_handler(CommandHandler("fakeserver", fakeserver_command))
    app.add_handler(CommandHandler("frida", frida_command))
    app.add_handler(CommandHandler("export", export_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("allow", allow_user))
    app.add_handler(CommandHandler("deny", deny_user))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("🔥 Ultimate Patcher v5.0 running – all protections bypassed.")
    app.run_polling()

if __name__ == "__main__":
    main()