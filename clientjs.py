"""Client-side assets for the Terminal: tracker + pro-tools JS, viz shell.

Plain strings inlined into the page at render time. No network, no build
step; generate.py imports these so the render logic stays readable.
"""

# ── Client-side JS for portfolio tracker ─────────────────────────

# Liquid names subscribers are likely to hold; keeps the tracker's
# prices.json useful beyond the research universe. Dedupe happens at fetch.
TRACKER_POPULAR = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "AMD", "NFLX",
    "COST", "WMT", "JPM", "V", "MA", "BRK-B", "UNH", "XOM", "CVX", "PLTR",
    "COIN", "HOOD", "SOFI", "F", "GM", "INTC", "QCOM", "TXN", "TSM", "SMCI",
    "DELL", "ORCL", "CRM", "NOW", "SNOW", "CRWD", "NET", "DDOG", "UBER",
    "ABNB", "DIS", "PYPL", "SHOP", "SPOT", "BA", "CAT", "DE", "GE", "HON",
    "LMT", "RTX", "IONQ", "RGTI", "QBTS", "SPY", "QQQ", "IWM", "VTI", "VOO",
    "SCHD", "O", "KO", "PEP", "MCD", "SBUX", "NKE",
]

TRACKER_JS = """
(function(){
  var K='yb-portfolio', prices={};
  var pos = JSON.parse(localStorage.getItem(K)||'[]');
  fetch('prices.json').then(function(r){return r.json()}).then(function(p){
    prices=p; render();
  }).catch(function(){ render(); });
  function esc(s){
    return String(s==null?'':s).replace(/[&<>"']/g,function(c){
      return({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]);
    });
  }
  function render(){
    var empty=document.getElementById('tracker-empty');
    var tbl=document.getElementById('tracker-table');
    var sum=document.getElementById('tracker-summary');
    if(!pos.length){ empty.style.display=''; tbl.style.display='none'; sum.textContent=''; return; }
    empty.style.display='none'; tbl.style.display='';
    var totalVal=0, totalCost=0, html='';
    for(var i=0;i<pos.length;i++){
      var p=pos[i], q=prices[p.t]||{}, pr=q.price||null;
      var val=pr?pr*p.shares:null, cst=p.cost*p.shares;
      var gain=pr?((pr-p.cost)/p.cost*100):null;
      if(val){ totalVal+=val; totalCost+=cst; }
      var gc=gain!=null?(gain>=0?'up':'down'):'';
      var gs=gain!=null?((gain>=0?'+':'')+gain.toFixed(1)+'%'):'-';
      html+='<tr><td class="tk">'+esc(p.t)+'</td>'
        +'<td>'+p.shares+'</td>'
        +'<td>$'+p.cost.toFixed(2)+'</td>'
        +'<td>'+(pr?'$'+pr.toFixed(2):'-')+'</td>'
        +'<td class="'+gc+'">'+gs+'</td>'
        +'<td><button class="btn-rm" onclick="ybRemove('+i+')">x</button></td></tr>';
    }
    tbl.querySelector('tbody').innerHTML=html;
    if(totalCost>0 && totalVal>0){
      var tg=((totalVal-totalCost)/totalCost*100);
      sum.innerHTML='Your book: <span class="'+(tg>=0?'up':'down')+'">'
        +(tg>=0?'+':'')+tg.toFixed(1)+'%</span>';
    } else { sum.textContent=''; }
    if(window.renderTools) window.renderTools();
  }
  window.ybAdd=function(){
    var ti=document.getElementById('add-ticker');
    var si=document.getElementById('add-shares');
    var ci=document.getElementById('add-cost');
    var t=ti.value.toUpperCase().trim(), s=parseFloat(si.value), c=parseFloat(ci.value);
    if(!t||!s||!c||s<=0||c<=0) return;
    pos.push({t:t,shares:s,cost:c});
    localStorage.setItem(K,JSON.stringify(pos));
    ti.value=''; si.value=''; ci.value=''; ti.focus();
    render();
  };
  window.ybRemove=function(i){
    pos.splice(i,1);
    localStorage.setItem(K,JSON.stringify(pos));
    render();
  };
  document.querySelectorAll('.tracker-form input').forEach(function(el){
    el.addEventListener('keydown',function(e){ if(e.key==='Enter') ybAdd(); });
  });
  render();
})();
"""


VIZ_SECTION = """
<section id="screens" style="display:none">
  <h2>Your Book, Visualized <span class="chip" style="border-color:var(--gold);color:var(--gold)">Pro, free until July 22</span></h2>
  <div class="sub" style="margin-bottom:4px">Computed in your browser from the positions
  you track above and the Terminal's own data files. Names outside the coverage universe
  are labeled as such, never guessed at.</div>
  <div class="viz-grid">
    <div><h3>Allocation by value</h3><div id="viz-alloc"></div></div>
    <div><h3>Gain and loss</h3><div id="viz-pl"></div></div>
    <div><h3>Physical Layer exposure</h3><div id="viz-layer"></div></div>
    <div><h3>Earnings radar, next 30 days</h3><div id="viz-earn"></div></div>
  </div>
  <h3>Against my book</h3><div id="viz-overlap"></div>
  <h3>Price history, from the Terminal's own daily snapshots</h3>
  <div id="viz-spark"></div>
  <div class="viz-note">History starts July 1, 2026 and grows one point per trading
  day. Only positions with a live quote appear in value math.</div>
</section>
"""

TOOLS_JS = """
(function(){
  var tools={}, hist={}, prices={};
  Promise.all([
    fetch('tools-data.json').then(function(r){return r.json()}),
    fetch('history.json').then(function(r){return r.json()}),
    fetch('prices.json').then(function(r){return r.json()})
  ]).then(function(a){ tools=a[0].tickers||{}; hist=a[1]||{}; prices=a[2]||{};
    renderTools(); wireScanner(); }).catch(function(){});
  function esc(s){
    return String(s==null?'':s).replace(/[&<>"']/g,function(c){
      return({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]);
    });
  }
  function positions(){
    try { return JSON.parse(localStorage.getItem('yb-portfolio')||'[]'); }
    catch(e){ return []; }
  }
  function bars(el, items, fmt, signed){
    // items: [{lbl, val}] with val >= 0 share-of-max for width
    if(!items.length){ el.innerHTML='<div class="viz-note">nothing to show yet</div>'; return; }
    var max=0; items.forEach(function(i){ max=Math.max(max,Math.abs(i.val)); });
    el.innerHTML=items.map(function(i){
      var w=max?Math.max(2,Math.abs(i.val)/max*100):0;
      var cls=signed?(i.val>=0?'up':'down'):'';
      return '<div class="bar-row"><span class="lbl">'+esc(i.lbl)+'</span>'
        +'<span class="bar-track"><span class="bar-fill '+cls+'" style="width:'+w+'%"></span></span>'
        +'<span class="val">'+fmt(i.val)+'</span></div>';
    }).join('');
  }
  function spark(t, days){
    var ds=Object.keys(days).sort(), vs=ds.map(function(d){return days[d]});
    if(vs.length<3) return '';
    var min=Math.min.apply(0,vs), max=Math.max.apply(0,vs), rng=(max-min)||1;
    var pts=vs.map(function(v,i){
      return (i/(vs.length-1)*96+2).toFixed(1)+','+(30-(v-min)/rng*26+2).toFixed(1);
    }).join(' ');
    var up=vs[vs.length-1]>=vs[0];
    return '<span class="spark"><svg width="100" height="34" viewBox="0 0 100 34">'
      +'<polyline points="'+pts+'" fill="none" stroke="'+(up?'#22c55e':'#ef4444')+'" stroke-width="1.5"/></svg>'
      +'<span class="lbl">'+esc(t)+' '+vs.length+'d</span></span>';
  }
  window.renderTools=function(){
    var sec=document.getElementById('screens');
    if(!sec) return;
    var pos=positions();
    if(!pos.length){ sec.style.display='none'; return; }
    sec.style.display='';
    var priced=pos.filter(function(p){return prices[p.t]&&prices[p.t].price});
    // allocation + P/L
    var alloc=priced.map(function(p){
      return {lbl:p.t, val:prices[p.t].price*p.shares};
    }).sort(function(a,b){return b.val-a.val});
    bars(document.getElementById('viz-alloc'), alloc,
         function(v){return '$'+v.toFixed(0)}, false);
    var pl=priced.map(function(p){
      return {lbl:p.t, val:(prices[p.t].price-p.cost)/p.cost*100};
    }).sort(function(a,b){return b.val-a.val});
    bars(document.getElementById('viz-pl'), pl,
         function(v){return (v>=0?'+':'')+v.toFixed(1)+'%'}, true);
    // layer exposure (honest bucket for names without coverage)
    var byLayer={};
    priced.forEach(function(p){
      var l=(tools[p.t]&&tools[p.t].layer)||'No coverage data';
      byLayer[l]=(byLayer[l]||0)+prices[p.t].price*p.shares;
    });
    var total=0; Object.keys(byLayer).forEach(function(l){total+=byLayer[l]});
    var layers=Object.keys(byLayer).map(function(l){
      return {lbl:l.length>14?l.slice(0,13)+'.':l, val:byLayer[l]/total*100};
    }).sort(function(a,b){return b.val-a.val});
    bars(document.getElementById('viz-layer'), layers,
         function(v){return v.toFixed(0)+'%'}, false);
    // earnings radar (real calendar dates only)
    var now=new Date(), soon=[];
    pos.forEach(function(p){
      var e=tools[p.t]&&tools[p.t].earnings;
      if(!e) return;
      var dd=(new Date(e+'T00:00:00Z')-now)/864e5;
      if(dd>=-1&&dd<=30) soon.push({t:p.t,e:e});
    });
    soon.sort(function(a,b){return a.e<b.e?-1:1});
    document.getElementById('viz-earn').innerHTML = soon.length
      ? soon.map(function(s){return '<div class="bar-row"><span class="lbl">'+esc(s.t)
          +'</span><span style="font-size:12px">reports '+esc(s.e)+'</span></div>'}).join('')
      : '<div class="viz-note">none of your names has a known earnings date in the next 30 days</div>';
    // overlap with Quinn's book
    var ov=pos.map(function(p){
      var d=tools[p.t]||{};
      if(d.held==null) return '<div class="bar-row"><span class="lbl">'+esc(p.t)
        +'</span><span style="font-size:12px;color:var(--dim)">not in my book</span></div>';
      var bits=[d.held.toFixed(1)+'% of my book'];
      if(d.health) bits.push(d.health);
      if(d.conviction!=null) bits.push('machine '+d.conviction+'/100 '+(d.stance||''));
      return '<div class="bar-row"><span class="lbl">'+esc(p.t)
        +'</span><span style="font-size:12px">'+esc(bits.join(' | '))+'</span></div>';
    });
    document.getElementById('viz-overlap').innerHTML=ov.join('');
    // sparklines from our own snapshots
    var sp=pos.map(function(p){ return hist[p.t]?spark(p.t,hist[p.t]):''; }).join('');
    document.getElementById('viz-spark').innerHTML =
      sp || '<div class="viz-note">no snapshot history yet for your names; it accrues daily</div>';
  };
  function wireScanner(){
    var table=document.getElementById('scan-table');
    if(!table) return;
    var body=table.querySelector('tbody');
    document.querySelectorAll('.scan-chip').forEach(function(btn){
      btn.addEventListener('click',function(){
        if(btn.dataset.sort){
          var key=btn.dataset.sort;
          Array.from(body.rows).sort(function(a,b){
            var av=parseFloat(a.dataset[key==='day'?'day':'conv']);
            var bv=parseFloat(b.dataset[key==='day'?'day':'conv']);
            if(isNaN(av)) av=-1e9; if(isNaN(bv)) bv=-1e9;
            return key==='day'?Math.abs(bv)-Math.abs(av):bv-av;
          }).forEach(function(r){body.appendChild(r)});
          return;
        }
        document.querySelectorAll('.scan-chip[data-filter-layer],.scan-chip[data-filter-held]')
          .forEach(function(b){b.classList.remove('active')});
        btn.classList.add('active');
        Array.from(body.rows).forEach(function(r){
          var show=true;
          if(btn.dataset.filterHeld) show=r.dataset.held==='1';
          else if(btn.dataset.filterLayer&&btn.dataset.filterLayer!=='*')
            show=r.dataset.layer===btn.dataset.filterLayer;
          r.style.display=show?'':'none';
        });
      });
    });
  }
})();
"""
