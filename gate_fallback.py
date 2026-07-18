"""Pure-JS crypto fallback for the members gate.

crypto.subtle only exists in secure contexts, so over plain http (the
state of the world until the TLS cert issues) the gate must derive and
decrypt in plain JavaScript. Same parameters as gate.py: PBKDF2-HMAC-
SHA256, 200k iterations, 48 bytes -> AES-256-CBC. The AES S-boxes are
the FIPS-197 literal constants; correctness is proven byte-for-byte
against gate.encrypt_payload by tests/test_gate_fallback.py via node.
"""

# The two AES S-boxes as hex literals (FIPS-197 figure 7 and figure 14).
SBOX = (
    "637c777bf26b6fc53001672bfed7ab76ca82c97dfa5947f0add4a2af9ca472c0"
    "b7fd9326363ff7cc34a5e5f171d8311504c723c31896059a071280e2eb27b275"
    "09832c1a1b6e5aa0523bd6b329e32f8453d100ed20fcb15b6acbbe394a4c58cf"
    "d0efaafb434d338545f9027f503c9fa851a3408f929d38f5bcb6da2110fff3d2"
    "cd0c13ec5f974417c4a77e3d645d197360814fdc222a908846eeb814de5e0bdb"
    "e0323a0a4906245cc2d3ac629195e479e7c8376d8dd54ea96c56f4ea657aae08"
    "ba78252e1ca6b4c6e8dd741f4bbd8b8a703eb5664803f60e613557b986c11d9e"
    "e1f8981169d98e949b1e87e9ce5528df8ca1890dbfe6426841992d0fb054bb16")
SBOX_INV = (
    "52096ad53036a538bf40a39e81f3d7fb7ce339829b2fff87348e4344c4dee9cb"
    "547b9432a6c2233dee4c950b42fac34e082ea16628d924b2765ba2496d8bd125"
    "72f8f66486689816d4a45ccc5d65b6926c704850fdedb9da5e154657a78d9d84"
    "90d8ab008cbcd30af7e45805b8b34506d02c1e8fca3f0f02c1afbd0301138a6b"
    "3a9111414f67dcea97f2cfcef0b4e67396ac7422e7ad3585e2f937e81c75df6e"
    "47f11a711d29c5896fb7620eaa18be1bfc563e4bc6d279209adbc0fe78cd5af4"
    "1fdda8338807c731b11210592780ec5f60517fa919b54a0d2de57a9f93c99cef"
    "a0e03b4dae2af5b0c8ebbb3c83539961172b047eba77d626e169146355210c7d")

FALLBACK_JS = r"""
var YBF=(function(){
'use strict';
var K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,
0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,
0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,
0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,
0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,
0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
function sha256(msg){
  var l=msg.length,w=new Array(64),H=[0x6a09e667,0xbb67ae85,0x3c6ef372,
  0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  var bl=l*8,padded=new Uint8Array(((l+8)>>6<<6)+64);
  padded.set(msg);padded[l]=0x80;
  var dv=new DataView(padded.buffer);
  dv.setUint32(padded.length-4,bl>>>0);
  dv.setUint32(padded.length-8,Math.floor(bl/0x100000000));
  for(var i=0;i<padded.length;i+=64){
    for(var t=0;t<16;t++)w[t]=dv.getUint32(i+t*4);
    for(t=16;t<64;t++){
      var a=w[t-15],b=w[t-2];
      var s0=((a>>>7)|(a<<25))^((a>>>18)|(a<<14))^(a>>>3);
      var s1=((b>>>17)|(b<<15))^((b>>>19)|(b<<13))^(b>>>10);
      w[t]=(w[t-16]+s0+w[t-7]+s1)|0;
    }
    var A=H[0],B=H[1],C=H[2],D=H[3],E=H[4],F=H[5],G=H[6],I=H[7];
    for(t=0;t<64;t++){
      var S1=((E>>>6)|(E<<26))^((E>>>11)|(E<<21))^((E>>>25)|(E<<7));
      var ch=(E&F)^((~E)&G);
      var t1=(I+S1+ch+K[t]+w[t])|0;
      var S0=((A>>>2)|(A<<30))^((A>>>13)|(A<<19))^((A>>>22)|(A<<10));
      var maj=(A&B)^(A&C)^(B&C);
      var t2=(S0+maj)|0;
      I=G;G=F;F=E;E=(D+t1)|0;D=C;C=B;B=A;A=(t1+t2)|0;
    }
    H[0]=(H[0]+A)|0;H[1]=(H[1]+B)|0;H[2]=(H[2]+C)|0;H[3]=(H[3]+D)|0;
    H[4]=(H[4]+E)|0;H[5]=(H[5]+F)|0;H[6]=(H[6]+G)|0;H[7]=(H[7]+I)|0;
  }
  var out=new Uint8Array(32),odv=new DataView(out.buffer);
  for(i=0;i<8;i++)odv.setUint32(i*4,H[i]>>>0);
  return out;
}
function hmac(key,msg){
  if(key.length>64)key=sha256(key);
  var ik=new Uint8Array(64+msg.length),ok=new Uint8Array(96);
  for(var i=0;i<64;i++){ik[i]=(key[i]||0)^0x36;ok[i]=(key[i]||0)^0x5c;}
  ik.set(msg,64);
  ok.set(sha256(ik),64);
  return sha256(ok);
}
function pbkdf2(pass,salt,iter,dklen){
  var out=new Uint8Array(dklen),pos=0,block=1;
  while(pos<dklen){
    var msg=new Uint8Array(salt.length+4);
    msg.set(salt);
    msg[salt.length]=(block>>>24)&255;msg[salt.length+1]=(block>>>16)&255;
    msg[salt.length+2]=(block>>>8)&255;msg[salt.length+3]=block&255;
    var u=hmac(pass,msg),t=u.slice();
    for(var i=1;i<iter;i++){
      u=hmac(pass,u);
      for(var j=0;j<32;j++)t[j]^=u[j];
    }
    var n=Math.min(32,dklen-pos);
    out.set(t.subarray(0,n),pos);pos+=n;block++;
  }
  return out;
}
function hexBytes(h){
  var a=new Uint8Array(h.length/2);
  for(var i=0;i<a.length;i++)a[i]=parseInt(h.substr(i*2,2),16);
  return a;
}
var SBOX=hexBytes('__SBOX__');
var SINV=hexBytes('__SBOX_INV__');
var RCON=[1,2,4,8,16,32,64,128,27,54,108,216,171,77];
function xtime(x){return((x<<1)^((x&0x80)?0x1b:0))&255;}
function gmul(a,b){
  var p=0;
  for(var i=0;i<8;i++){
    if(b&1)p^=a;
    a=xtime(a);b>>=1;
  }
  return p&255;
}
function expandKey(key){
  // AES-256: 8-word key -> 60 words (15 round keys)
  var w=new Array(60);
  for(var i=0;i<8;i++)
    w[i]=(key[4*i]<<24)|(key[4*i+1]<<16)|(key[4*i+2]<<8)|key[4*i+3];
  for(i=8;i<60;i++){
    var t=w[i-1];
    if(i%8===0){
      t=((t<<8)|(t>>>24))>>>0;
      t=(SBOX[(t>>>24)&255]<<24)|(SBOX[(t>>>16)&255]<<16)|
        (SBOX[(t>>>8)&255]<<8)|SBOX[t&255];
      t^=RCON[i/8-1]<<24;
    }else if(i%8===4){
      t=(SBOX[(t>>>24)&255]<<24)|(SBOX[(t>>>16)&255]<<16)|
        (SBOX[(t>>>8)&255]<<8)|SBOX[t&255];
    }
    w[i]=(w[i-8]^t)>>>0;
  }
  return w;
}
function addRoundKey(st,w,round){
  for(var c=0;c<4;c++){
    var word=w[round*4+c];
    st[4*c]^=(word>>>24)&255;st[4*c+1]^=(word>>>16)&255;
    st[4*c+2]^=(word>>>8)&255;st[4*c+3]^=word&255;
  }
}
function decryptBlock(block,w){
  var st=block.slice();
  addRoundKey(st,w,14);
  for(var round=13;round>=1;round--){
    // InvShiftRows (rows shift right by row index; state is column-major)
    var t=st.slice();
    for(var r=1;r<4;r++)
      for(var c=0;c<4;c++)
        st[4*((c+r)%4)+r]=t[4*c+r];
    // InvSubBytes
    for(var i=0;i<16;i++)st[i]=SINV[st[i]];
    addRoundKey(st,w,round);
    // InvMixColumns
    for(c=0;c<4;c++){
      var a0=st[4*c],a1=st[4*c+1],a2=st[4*c+2],a3=st[4*c+3];
      st[4*c]  =gmul(a0,14)^gmul(a1,11)^gmul(a2,13)^gmul(a3,9);
      st[4*c+1]=gmul(a0,9)^gmul(a1,14)^gmul(a2,11)^gmul(a3,13);
      st[4*c+2]=gmul(a0,13)^gmul(a1,9)^gmul(a2,14)^gmul(a3,11);
      st[4*c+3]=gmul(a0,11)^gmul(a1,13)^gmul(a2,9)^gmul(a3,14);
    }
  }
  t=st.slice();
  for(r=1;r<4;r++)
    for(c=0;c<4;c++)
      st[4*((c+r)%4)+r]=t[4*c+r];
  for(i=0;i<16;i++)st[i]=SINV[st[i]];
  addRoundKey(st,w,0);
  return st;
}
function decryptCBC(ct,key,iv){
  var w=expandKey(key),out=new Uint8Array(ct.length),prev=iv;
  for(var i=0;i<ct.length;i+=16){
    var block=ct.subarray(i,i+16);
    var pt=decryptBlock(block,w);
    for(var j=0;j<16;j++)pt[j]^=prev[j];
    out.set(pt,i);prev=block;
  }
  var pad=out[out.length-1];
  if(pad<1||pad>16)return null;
  for(i=out.length-pad;i<out.length;i++)if(out[i]!==pad)return null;
  return out.subarray(0,out.length-pad);
}
function decrypt(passStr,salt,ct){
  var pass=new TextEncoder().encode(passStr);
  var kb=pbkdf2(pass,salt,200000,48);
  return decryptCBC(ct,kb.subarray(0,32),kb.subarray(32,48));
}
return {decrypt:decrypt};
})();
""".replace("__SBOX__", SBOX).replace("__SBOX_INV__", SBOX_INV)
