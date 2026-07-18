"""Member gate: encrypt the members pages so a public repo cannot leak them.

The repo and the GitHub Pages tree are world-readable, so an unlisted URL
alone is not paid gating. Each members page ships as an AES-256-CBC blob;
the passcode goes out in the paid welcome email and the browser decrypts
locally with WebCrypto. Zero infra, works offline after first unlock.

Key derivation: PBKDF2-HMAC-SHA256, 200,000 iterations, 48 bytes
(32 key + 16 iv), random 16-byte salt per build. The cipher runs through
the system openssl binary in raw -K/-iv mode, which both OpenSSL and the
LibreSSL that launchd's bare PATH resolves to support identically.
"""

import base64
import hashlib
import secrets
import subprocess

ITERATIONS = 200000
SALT_BYTES = 16


def _derive(passphrase, salt):
    raw = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"),
                              salt, ITERATIONS, dklen=48)
    return raw[:32], raw[32:48]


def _openssl(args, data):
    return subprocess.run(["openssl", "enc"] + args, input=data,
                          capture_output=True, check=True).stdout


def encrypt_payload(html, passphrase):
    """HTML -> base64(salt + ciphertext)."""
    salt = secrets.token_bytes(SALT_BYTES)
    key, iv = _derive(passphrase, salt)
    ct = _openssl(["-aes-256-cbc", "-K", key.hex(), "-iv", iv.hex()],
                  html.encode("utf-8"))
    return base64.b64encode(salt + ct).decode("ascii")


def decrypt_html(payload, passphrase):
    """Test-side inverse. Returns None when the passphrase is wrong."""
    blob = base64.b64decode(payload)
    salt, ct = blob[:SALT_BYTES], blob[SALT_BYTES:]
    key, iv = _derive(passphrase, salt)
    try:
        out = _openssl(["-d", "-aes-256-cbc", "-K", key.hex(), "-iv", iv.hex()], ct)
        return out.decode("utf-8")
    except (subprocess.CalledProcessError, UnicodeDecodeError):
        return None


GATE_CSS = """
:root { --bg:#0b0a07; --surface:#12100b; --border:#2a2415; --text:#c8c2b4;
        --bright:#efe9da; --dim:#6b6350; --gold:#f0b429; --red:#ef4444;
        --mono:'SF Mono','JetBrains Mono',Menlo,Consolas,monospace; }
* { box-sizing:border-box; margin:0; }
body { background:var(--bg); color:var(--text); font:14px/1.6 var(--mono);
       min-height:100vh; display:flex; align-items:center; justify-content:center;
       padding:24px; -webkit-font-smoothing:antialiased; }
.gate { width:100%; max-width:380px; }
.gate h1 { color:var(--gold); font-size:14px; letter-spacing:4px;
           text-transform:uppercase; margin-bottom:6px; }
.gate .sub { color:var(--dim); font-size:12px; margin-bottom:22px; line-height:1.6;
             border-bottom:1px solid var(--border); padding-bottom:14px; }
.gate input { width:100%; background:var(--surface); border:1px solid var(--border);
              color:var(--bright); font:16px var(--mono); letter-spacing:2px;
              padding:13px 14px; border-radius:6px; text-transform:uppercase; }
.gate input:focus { outline:none; border-color:var(--gold); }
.gate button { width:100%; margin-top:10px; background:var(--gold); color:var(--bg);
               border:none; font:700 13px var(--mono); letter-spacing:2px;
               text-transform:uppercase; padding:13px; border-radius:6px; cursor:pointer; }
.gate .err { color:var(--red); font-size:12px; margin-top:10px; min-height:18px; }
.gate .foot { color:var(--dim); font-size:11px; margin-top:22px; line-height:1.6; }
.gate .foot a { color:var(--gold); text-decoration:none; }
"""

from gate_fallback import FALLBACK_JS

GATE_JS = FALLBACK_JS + """
var P='__YB_GATE_PAYLOAD__', K='yb-members-pass';
function b64(s){var b=atob(s),a=new Uint8Array(b.length);
  for(var i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return a;}
async function unlock(pass,fromStore){
  var err=document.getElementById('err');
  try{
    var blob=b64(P),salt=blob.slice(0,16),ct=blob.slice(16),html;
    if(window.crypto&&crypto.subtle){
      var mat=await crypto.subtle.importKey('raw',
        new TextEncoder().encode(pass),'PBKDF2',false,['deriveBits']);
      var bits=await crypto.subtle.deriveBits(
        {name:'PBKDF2',salt:salt,iterations:200000,hash:'SHA-256'},mat,384);
      var kb=new Uint8Array(bits);
      var key=await crypto.subtle.importKey('raw',kb.slice(0,32),
        {name:'AES-CBC'},false,['decrypt']);
      var pt=await crypto.subtle.decrypt(
        {name:'AES-CBC',iv:kb.slice(32,48)},key,ct);
      html=new TextDecoder().decode(pt);
    }else{
      // plain-http fallback: same math in pure JS, takes a few seconds
      err.textContent='Unlocking, give it a few seconds...';
      await new Promise(function(r){setTimeout(r,30);});
      var pt2=YBF.decrypt(pass,salt,ct);
      if(!pt2) throw 0;
      html=new TextDecoder().decode(pt2);
    }
    if(html.slice(0,9).toLowerCase()!=='<!doctype') throw 0;
    localStorage.setItem(K,pass);
    document.open();document.write(html);document.close();
  }catch(e){
    localStorage.removeItem(K);
    if(!fromStore) err.textContent='That passcode did not unlock the desk. Check the welcome email.';
    else err.textContent='';
  }
}
window.ybGo=function(){
  var v=document.getElementById('pass').value.trim().toUpperCase();
  if(v) unlock(v,false);
};
document.addEventListener('DOMContentLoaded',function(){
  var saved=localStorage.getItem(K);
  if(saved) unlock(saved,true);
  document.getElementById('pass').addEventListener('keydown',
    function(e){if(e.key==='Enter')ybGo();});
});
"""


def gate_page_html(payload, title):
    """The shell that ships: passcode prompt + encrypted payload, nothing else."""
    js = GATE_JS.replace("__YB_GATE_PAYLOAD__", payload)
    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{title}</title>
<style>{GATE_CSS}</style></head><body>
<div class="gate">
<h1>Young Bull</h1>
<div class="sub">Members desk. Enter the passcode from your welcome email.
It unlocks on this device and stays unlocked.</div>
<input id="pass" placeholder="YB-XXXX-XXXX" autocomplete="off" spellcheck="false"
 autocapitalize="characters">
<button onclick="ybGo()">Unlock the desk</button>
<div class="err" id="err"></div>
<div class="foot">Not a member yet? <a href="../../pricing.html">The desk is $99 a year
for founding members.</a> Decryption happens in your browser. YB_GATE</div>
</div>
<script>{js}</script>
</body></html>"""
