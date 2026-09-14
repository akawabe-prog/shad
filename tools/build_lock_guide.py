#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ワンキー化ガイド（/lock-guide）を生成する。

    python3 tools/build_lock_guide.py

・ルールは site/data/lock_guide.json（本国 LOCK_GUIDE_2026.pdf を日本販売品に絞って整理したもの）。
  ページはこのJSONを実行時に読み、トップ→サイド→鍵の色 の順に選ばせて結果を出す。
・部品の定価は /data/catalog/accessories.json から実行時に表示（商品マスター更新に追従）。
・カードの画像・商品名は /data/catalog/cards.json から。
・ヘッダー／ナビ／フッターは site/fitting-kits.html から複製（サイト共通部分を1か所に保つため）。
・?top=TR46&side=TR27 のように URL で初期選択できる（商品ページの＋αブロックから誘導）。
"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
src = open(os.path.join(SITE, "fitting-kits.html"), encoding="utf-8").read()

head = src[:src.index("<style>")]
head = head.replace("フィッティングキットとは｜SHAD JAPAN — バイクとケースをつなぐ取付キット", "ワンキー化ガイド｜SHAD JAPAN — トップとサイドの鍵をひとつに")
head = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="SHADのトップケースとサイドケースの鍵をひとつにまとめる方法を、組み合わせごとに案内します。付属の予備シリンダーで済むか、追加部品が必要かを3ステップで確認できます。">', head)
head = re.sub(r'(property="og:description" content=")[^"]*"', r'\1SHADのトップケースとサイドケースの鍵をひとつに。組み合わせを選ぶと必要な部品と手順がわかります。"', head)
head = re.sub(r'(name="twitter:description" content=")[^"]*"', r'\1SHADのトップケースとサイドケースの鍵をひとつに。組み合わせを選ぶと必要な部品と手順がわかります。"', head)
head = head.replace("https://www.shad-japan.com/fitting-kits", "https://www.shad-japan.com/lock-guide")
nav = src[src.index("<body"):src.index("<!-- ===== NAV ===== -->")] if "<!-- ===== NAV ===== -->" in src else ""
body_start = src.index("<body")
nav_block = src[body_start:src.index("</div>", src.index('id="navMobile"')) + len("</div>")]
nav_block = nav_block.replace('<li><a class="text-white" href="/fitting-kits">Fitting Kits</a>', '<li><a class="hover:text-white transition" href="/fitting-kits">Fitting Kits</a>')
nav_block = nav_block.replace('class="block py-3.5 border-b border-white/10 font-disp uppercase tracking-[.14em] text-[16px] text-shad">Fitting Kits', 'class="block py-3.5 border-b border-white/10 font-disp uppercase tracking-[.14em] text-[16px] text-white/85 hover:text-white transition">Fitting Kits')
footer = src[src.index("<footer"):src.index("</footer>") + len("</footer>")]

content = r'''
<!-- ===== ワンキー化ガイド（生成：tools/build_lock_guide.py ／ ルール：/data/lock_guide.json）===== -->
<header class="bg-ink text-white">
  <div class="max-w-site mx-auto px-7 pt-16 pb-14">
    <p class="font-disp font-semibold text-[13px] tracking-[.3em] uppercase text-shad">One Key Guide</p>
    <h1 class="sec-ttl text-white mt-3 lg-h1">トップとサイドの鍵を、ひとつに。</h1>
    <p class="text-white/65 text-[15px] mt-5 max-w-[680px] leading-[1.9]">SHADのケースはキーシリンダーが差し替え式。トップケースとサイドケースのシリンダーを同じ鍵のものに揃えれば、3つのケースを1本の鍵で開ける・閉める・外すことができます。お使いの組み合わせを選ぶと、付属の予備シリンダーで済むのか、追加部品が必要なのかがわかります。</p>
    <div class="flex flex-wrap gap-x-8 gap-y-2 mt-6 text-[13px] text-white/55">
      <span><i class="ti ti-clock mr-1.5 text-shad"></i>作業時間の目安：数分</span>
      <span><i class="ti ti-tool mr-1.5 text-shad"></i>工具：プラスドライバー程度</span>
      <span><i class="ti ti-key mr-1.5 text-shad"></i>本国 SHAD Lock Guide 2026 準拠</span>
    </div>
  </div>
</header>

<main class="bg-mist">
  <div class="max-w-site mx-auto px-7 py-12 lg:py-16">
    <div class="lg:grid lg:grid-cols-[1fr_380px] lg:gap-10 items-start">
      <div class="space-y-10">
        <!-- STEP 1 -->
        <section class="lg-step" id="step1">
          <div class="lg-step-h"><span class="lg-step-num">1</span><div><h2>トップケースを選ぶ</h2><p>お使いの、または検討中のトップケース（リアバッグ）</p></div></div>
          <div class="lg-tiles" id="topTiles"></div>
        </section>
        <!-- STEP 2 -->
        <section class="lg-step" id="step2">
          <div class="lg-step-h"><span class="lg-step-num">2</span><div><h2>サイドケース／バッグを選ぶ</h2><p>統一できない組み合わせはグレーで表示します</p></div></div>
          <div class="lg-tiles" id="sideTiles"></div>
        </section>
        <!-- STEP 3 -->
        <section class="lg-step" id="step3" hidden>
          <div class="lg-step-h"><span class="lg-step-num">3</span><div><h2>鍵の色を選ぶ</h2><p>製造時期によってレッドキー／ブラックキーが混在するモデルです。お手元の鍵をご確認ください</p></div></div>
          <div class="lg-keys" id="keyPick"></div>
        </section>
      </div>

      <!-- 結果 -->
      <aside class="lg-result mt-10 lg:mt-0 lg:sticky lg:top-[92px]" id="result" aria-live="polite">
        <div class="lg-result-empty">
          <i class="ti ti-key text-[34px] text-shad"></i>
          <p class="font-bold text-[16px] mt-3">トップとサイドを選ぶと、ここに結果が出ます</p>
          <p class="text-[13px] text-neutral-500 mt-2 leading-relaxed">必要な部品・費用の目安・手順動画へのリンクを表示します。</p>
        </div>
      </aside>
    </div>

    <!-- 鍵の見分け方・仕組み -->
    <section class="mt-16 grid md:grid-cols-2 gap-6">
      <div class="lg-card">
        <p class="pd-sec-en">Key Types</p>
        <h2 class="text-[20px] font-bold mt-1">鍵の種類の見分け方</h2>
        <div class="grid grid-cols-3 gap-4 mt-5 text-center">
          <div><img src="/img/lock-guide/key_red.webp" alt="レッドキー" class="lg-keyimg"><b class="block mt-2 text-[14px]">レッドキー</b><span class="block text-[12px] text-neutral-500 mt-1">赤い樹脂ヘッド。従来のSHADシリンダー。TR41・TR46・SH47・SH44・SH33 など</span></div>
          <div><img src="/img/lock-guide/key_black.webp" alt="ブラックキー" class="lg-keyimg"><b class="block mt-2 text-[14px]">ブラックキー</b><span class="block text-[12px] text-neutral-500 mt-1">黒いヘッドで刻印入りのプレミアムシリンダー。SH51・SH38X・TR30、近年のSH58X／SH59X／SH48</span></div>
          <div><div class="lg-keyimg flex items-center justify-center bg-mist rounded-[12px]"><span class="font-disp font-semibold text-[26px] tracking-[.08em] text-ink">TERRA</span></div><b class="block mt-2 text-[14px]">TERRAキー</b><span class="block text-[12px] text-neutral-500 mt-1">TERRAアルミケースとTR50専用のシリンダー</span></div>
        </div>
      </div>
      <div class="lg-card">
        <p class="pd-sec-en">How It Works</p>
        <h2 class="text-[20px] font-bold mt-1">ワンキー化の仕組み</h2>
        <ol class="lg-steps mt-5">
          <li><b>予備シリンダーを用意する</b><span>多くのサイドケースには右側に予備のキーシリンダーが1個付属しています（Option A）。ない場合や3個まとめて揃えたい場合はキーシリンダーセットを購入します（Option B）。</span></li>
          <li><b>トップケースのシリンダーを差し替える</b><span>ロック部のカバーを外し、シリンダーを引き抜いて、サイドと同じ鍵のシリンダーを差し込みます。</span></li>
          <li><b>3つのケースを1本の鍵で</b><span>差し替え後はトップもサイドも同じ鍵で開閉・着脱できます。余った鍵は予備として保管してください。</span></li>
        </ol>
        <p class="text-[12px] text-neutral-500 mt-4 leading-relaxed">鍵の系統（TERRA／レッド／ブラック）が異なる組み合わせは、シリンダーの差し替えだけでは統一できません。上の診断でご確認ください。</p>
      </div>
    </section>

    <div class="mt-10 flex flex-wrap items-center gap-3">
      <a href="/fitting-kits" class="btn border-[1.5px] border-ink text-ink hover:bg-ink hover:text-white"><i class="ti ti-tool"></i>フィッティングキットとは</a>
      <a href="/faq" class="btn border border-black/25 text-ink hover:bg-white"><i class="ti ti-help-circle"></i>FAQ</a>
      <a href="https://www.shad.es/assets/anexos/ANEXOS_WEB/LOCK_GUIDE_2026.pdf" target="_blank" rel="noopener" class="btn border border-black/25 text-ink hover:bg-white"><i class="ti ti-file-type-pdf"></i>本国 Lock Guide（英語PDF）</a>
    </div>
  </div>
</main>
'''

script = r'''
<script>
/* ===== ワンキー化ガイド：ルール（/data/lock_guide.json）を読んで診断する ===== */
(function(){
  var R=null, CARDS={}, ACC={}, st={top:null, side:null, tkey:null, skey:null};
  var q=new URLSearchParams(location.search);
  function el(h){ var d=document.createElement('div'); d.innerHTML=h.trim(); return d.firstChild; }
  function esc(s){ return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];}); }
  function yen(n){ return n?('¥'+Number(n).toLocaleString('ja-JP')+'（税込）'):''; }
  function groupOf(list,code){ for(var i=0;i<list.length;i++) if(list[i].codes.indexOf(code)>=0) return list[i]; return null; }
  function famOf(g,key){ return g.family==='ask' ? key : g.family; }

  function tiles(host,list,kind){
    host.innerHTML='';
    list.forEach(function(g){
      g.codes.forEach(function(code){
        var c=CARDS[code]||{}; if(c.status) return;           // 生産終了は出さない
        var t=el('<button type="button" class="lg-tile" data-code="'+code+'"><span class="lg-tile-img"><img src="'+(c.img||'')+'" alt="" loading="lazy"></span><span class="lg-tile-code">'+code+'</span><span class="lg-tile-jp">'+esc(c.jp||g.label)+'</span><span class="lg-tile-na">統一不可</span></button>');
        t.addEventListener('click',function(){ pick(kind,code); });
        host.appendChild(t);
      });
    });
  }
  function pick(kind,code){
    if(kind==='top'){ st.top=code; st.tkey=null; } else { st.side=code; st.skey=null; }
    sync();
  }
  function statusFor(){
    var tg=groupOf(R.tops,st.top), sg=groupOf(R.sides,st.side); if(!tg||!sg) return null;
    var tf=famOf(tg,st.tkey), sf=famOf(sg,st.skey); if(!tf||!sf) return {pending:true};
    var m=R.matrix[tf+'|'+sf]; if(!m) return {status:'no'};
    if(m.only_sides && m.only_sides.indexOf(sg.id)<0) m=m['else']||{status:'no'};
    return Object.assign({tf:tf,sf:sf,tg:tg,sg:sg},m);
  }
  function sync(){
    /* タイルの選択・不可表示 */
    document.querySelectorAll('#topTiles .lg-tile').forEach(function(t){ t.classList.toggle('on',t.dataset.code===st.top); });
    var tg=groupOf(R.tops,st.top);
    document.querySelectorAll('#sideTiles .lg-tile').forEach(function(t){
      t.classList.toggle('on',t.dataset.code===st.side);
      var na=false;
      if(tg){ var sg=groupOf(R.sides,t.dataset.code); var tfs= tg.family==='ask'?['red','black']:[tg.family]; var sfs= sg.family==='ask'?['red','black']:[sg.family];
        na = tfs.every(function(tf){ return sfs.every(function(sf){ var m=R.matrix[tf+'|'+sf]; if(!m) return true; if(m.only_sides&&m.only_sides.indexOf(sg.id)<0) m=m['else']||{status:'no'}; return m.status==='no'; }); }); }
      t.classList.toggle('na',na);
    });
    /* STEP3：鍵の色 */
    var kp=document.getElementById('keyPick'), s3=document.getElementById('step3'); kp.innerHTML='';
    var asks=[]; var sg=groupOf(R.sides,st.side);
    if(tg&&tg.family==='ask') asks.push({kind:'tkey',label:tg.label+'（トップ）の鍵'});
    if(sg&&sg.family==='ask') asks.push({kind:'skey',label:sg.label+'（サイド）の鍵'});
    s3.hidden=!asks.length;
    asks.forEach(function(a){
      var row=el('<div class="lg-keyrow"><p class="lg-keyrow-lb">'+esc(a.label)+'</p><div class="lg-keyopts"></div></div>');
      ['red','black'].forEach(function(k){
        var b=el('<button type="button" class="lg-keyopt'+(st[a.kind]===k?' on':'')+'" data-k="'+k+'"><img src="/img/lock-guide/key_'+k+'.webp" alt=""><b>'+R.families[k].label+'</b><span>'+esc(R.families[k].hint)+'</span></button>');
        b.addEventListener('click',function(){ st[a.kind]=k; sync(); });
        row.querySelector('.lg-keyopts').appendChild(b);
      });
      kp.appendChild(row);
    });
    render();
    var u=new URLSearchParams(); if(st.top)u.set('top',st.top); if(st.side)u.set('side',st.side); if(st.tkey)u.set('tkey',st.tkey); if(st.skey)u.set('skey',st.skey);
    history.replaceState(null,'',location.pathname+(u.toString()?'?'+u.toString():''));
  }
  function partCard(code){
    var p=R.parts[code]||{}, a=ACC[code]||{};
    return '<a href="https://moto.customjapan.net/i/'+code+'" target="_blank" rel="noopener" class="lg-part"><img src="https://img.customjapan.net/items/'+code+'_1.jpg" alt="" loading="lazy"><span><b>'+esc(p.name||a.name||code)+'</b><em>'+(yen(a.msrpTaxIn)||'定価はリンク先でご確認ください')+'</em><small>品番：'+code+(p.shad?'（SHAD '+p.shad+'）':'')+(p.note?' ／ '+esc(p.note):'')+'</small></span><i class="ti ti-external-link"></i></a>';
  }
  function video(id,label){ return id?'<a href="https://youtu.be/'+id+'" target="_blank" rel="noopener" class="lg-video"><i class="ti ti-brand-youtube"></i>'+esc(label)+'</a>':''; }
  function render(){
    var box=document.getElementById('result'); var r=statusFor();
    if(!r){ box.innerHTML='<div class="lg-result-empty"><i class="ti ti-key text-[34px] text-shad"></i><p class="font-bold text-[16px] mt-3">トップとサイドを選ぶと、ここに結果が出ます</p><p class="text-[13px] text-neutral-500 mt-2 leading-relaxed">必要な部品・費用の目安・手順動画へのリンクを表示します。</p></div>'; return; }
    var tg=groupOf(R.tops,st.top), sg=groupOf(R.sides,st.side);
    var head='<div class="lg-pair"><span>'+st.top+'</span><i class="ti ti-plus"></i><span>'+st.side+'</span></div>';
    if(r.pending){ box.innerHTML=head+'<p class="lg-badge is-wait"><i class="ti ti-key"></i>STEP 3 で鍵の色を選んでください</p>'; return; }
    var L=R.labels[r.status]; var h=head+'<p class="lg-badge is-'+L.tone+'">'+esc(L.badge)+'</p>';
    var tf=R.families[r.tf].label, sf=R.families[r.sf].label;
    h+='<p class="lg-fam">トップ：'+esc(tf)+'　／　サイド：'+esc(sf)+'</p>';
    if(r.status==='no'){
      h+='<p class="lg-txt">鍵の系統が異なるため、シリンダーの差し替えでは統一できません。TERRAキーの組み合わせはTERRA同士、レッドキーとブラックキーは同系統か、対応する変換部品がある組み合わせでご検討ください。</p>';
      h+='<a href="/products?feat=fullpannier" class="lg-link">フルパニア対応の商品を見る <i class="ti ti-arrow-right"></i></a>';
    } else if(r.status==='mech_contact'){
      h+='<p class="lg-txt">'+esc(r.note)+'</p><a href="/contact" class="lg-link">お問い合わせ <i class="ti ti-arrow-right"></i></a>';
    } else {
      if(r.note) h+='<p class="lg-txt">'+esc(r.note)+'</p>';
      var n=0;
      if(r.mech==='top'){ n++; var codes=(tg.downgrade&&tg.downgrade[st.top])||[]; h+='<div class="lg-opt"><span class="lg-opt-lb">Step '+n+'</span><b>トップケースのロック機構をレッドキー仕様に交換</b><p>専用ロックカバー（レッドキー付属）に交換します。カラーに合うものをお選びください。</p>'+codes.map(partCard).join('')+'</div>'; }
      if(r.spare && sg.spare){ n++; h+='<div class="lg-opt"><span class="lg-opt-lb">Option A</span><b>サイドケース付属の予備シリンダーを使う</b><p>'+esc(sg.label)+'の右側ケースに付属する予備キーシリンダーを、トップケースのシリンダーと差し替えます。追加費用はかかりません。</p></div>'; }
      if(r.part){ n++; h+='<div class="lg-opt"><span class="lg-opt-lb">'+(r.spare&&sg.spare?'Option B':'必要な部品')+'</span><b>キーシリンダーセットで揃える</b><p>'+(r.spare&&sg.spare?'3個をまとめて同じ鍵に統一したい場合や、予備が必要な場合はこちら。':'このセットのシリンダーに差し替えて、トップとサイドの鍵を統一します。')+'</p>'+partCard(r.part)+'</div>'; }
      var vt = tg.family==='ask' ? tg['video_'+r.tf] : tg.video;
      var vids=video(vt,tg.label+' の交換手順')+video(sg.video,sg.label+' の交換手順');
      if(vids) h+='<div class="lg-videos"><p class="lg-opt-lb">Watch</p>'+vids+'<small>本国SHADの手順動画（英語）。作業は自己責任で、難しい場合は取扱店へご相談ください。</small></div>';
      h+='<div class="lg-cta"><a href="/product/'+st.top.toLowerCase()+'" class="lg-link">'+st.top+' の商品ページ <i class="ti ti-arrow-right"></i></a><a href="/store-locator" class="lg-link">取扱店を探す <i class="ti ti-arrow-right"></i></a></div>';
    }
    box.innerHTML=h;
  }
  Promise.all(['/data/lock_guide.json','/data/catalog/cards.json','/data/catalog/accessories.json','/data/catalog/others.json'].map(function(u){return fetch(u).then(function(r){return r.ok?r.json():null;}).catch(function(){return null;});}))
  .then(function(rs){
    R=rs[0]; CARDS=rs[1]||{}; (rs[2]||[]).concat(rs[3]||[]).forEach(function(a){ ACC[String(a.cjCode)]=a; });
    if(!R){ document.getElementById('result').innerHTML='<p class="p-6 text-neutral-500">ガイドのデータを読み込めませんでした。</p>'; return; }
    tiles(document.getElementById('topTiles'),R.tops,'top'); tiles(document.getElementById('sideTiles'),R.sides,'side');
    var t=(q.get('top')||'').toUpperCase(), s=(q.get('side')||'').toUpperCase();
    if(groupOf(R.tops,t)) st.top=t; if(groupOf(R.sides,s)) st.side=s;
    if(['red','black'].indexOf(q.get('tkey'))>=0) st.tkey=q.get('tkey'); if(['red','black'].indexOf(q.get('skey'))>=0) st.skey=q.get('skey');
    sync();
  });
})();
</script>
'''

html = head + '<style>\n.chip{display:none}\n</style>\n<link rel="stylesheet" href="/css/custom.css">\n</head>\n' + nav_block + "\n" + content + "\n" + footer + "\n" + script + '\n<script src="/js/nav.js"></script>\n</body>\n</html>\n'
# head には既に custom.css の link があるので二重にしない
html = html.replace('<link rel="stylesheet" href="/css/custom.css">\n<style>\n.chip{display:none}\n</style>\n<link rel="stylesheet" href="/css/custom.css">\n</head>', '<link rel="stylesheet" href="/css/custom.css">\n</head>')
open(os.path.join(SITE, "lock-guide.html"), "w", encoding="utf-8").write(html)
print("生成: site/lock-guide.html（%d行）" % html.count("\n"))
