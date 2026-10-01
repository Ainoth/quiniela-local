'use strict';
const WIN_URL='https://www.win1x2.com/datos/actudato.zip';
const PCT_URL='https://www.quinielista.es/xml2/porcentajes_completo.asp?jornada=';
const LIVE_URL='https://static.dataradar.es/marcador/json/partidos.json';
const PLAY_URL='https://www.eduardolosilla.es/quiniela/archivos';
const PRICE=.75, SIGNS=['1','X','2'];
let state={season:'',round:0,matches:[],picks:Array(14).fill(''),pleno:['',''],development:[],winData:null,imported:[]};

function el(id){return document.getElementById(id)}
function showLoading(text){el('loadingText').textContent=text;el('loading').classList.remove('hidden')}
function hideLoading(){el('loading').classList.add('hidden')}
function toast(text){Android.notify(text)}
function save(){localStorage.setItem('quinielaState',JSON.stringify({...state,winData:null}))}
function restore(){try{const x=JSON.parse(localStorage.getItem('quinielaState'));if(x)state={...state,...x}}catch(e){}}
function showPage(id){document.querySelectorAll('.page').forEach(x=>x.classList.toggle('active',x.id===id));document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('active',x.dataset.page===id));window.scrollTo(0,0)}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>showPage(b.dataset.page));

function parseDates(text){return text.split(/\r?\n/).map(line=>{const m=line.match(/^(\d{2}):(\d{2})\/(\d{2})\/(\d{4})/);return m?{round:+m[1],date:new Date(+m[4],+m[3]-1,+m[2])}:null}).filter(Boolean)}
function nearestRound(entries){const now=new Date();now.setHours(0,0,0,0);return entries.sort((a,b)=>{const ad=Math.abs(a.date-now),bd=Math.abs(b.date-now);return ad-bd||(a.date<now)-(b.date<now)})[0]?.round||1}
function parseNames(text){const out={};text.split(/\r?\n/).forEach(line=>{const i=line.indexOf('-');if(i>0)out[line.slice(0,i).trim().toUpperCase()]=line.slice(i+1).trim()});return out}
function roundLine(text,round){return text.split(/\r?\n/).find(line=>+((line.match(/^\d+/)||['-1'])[0])===round)||''}
function parseTeams(pre,round){const line=roundLine(pre,round), block=line.slice(119,209),out=[];for(let i=0;i<90;i+=6)out.push([block.slice(i,i+3),block.slice(i+3,i+6)]);return out}
function parseHours(text,round){const line=text.split(/\r?\n/).find(x=>x.startsWith(String(round).padStart(2,'0')))||'',p=line.slice(2),out=[];for(let i=0;i<225;i+=15)out.push(p.slice(i,i+15));return out}
function parsePercentages(xml){const out=[];for(const tag of xml.matchAll(/<partido\b[^>]*>/gi)){const a={};for(const m of tag[0].matchAll(/([\w_]+)="([^"]*)"/g))a[m[1]]=m[2];out[+a.num-1]=[+a.p_jugados_1,+a.p_jugados_X,+a.p_jugados_2]}return out}

function updateData(){
  showLoading('Descargando jornada y porcentajes…');
  setTimeout(()=>{try{
    const raw=Android.fetchWinData();if(raw.startsWith('__ERROR__'))throw Error(raw.slice(9));
    const data=JSON.parse(raw),season=data.season,fec=data['FEC'+season+'.TXT'],pre=data['PRE'+season+'.TXT'],hours=data['HOR'+season+'.TXT'];
    if(!fec||!pre||!hours)throw Error('El paquete no contiene los ficheros de la temporada');
    const round=nearestRound(parseDates(fec)), names=parseNames(data['WEQUIPOS.TXT']||''),teams=parseTeams(pre,round),kick=parseHours(hours,round);
    const pRaw=Android.fetchText(PCT_URL+round);let pct=[];if(!pRaw.startsWith('__ERROR__'))pct=parsePercentages(pRaw);
    state.season=season;state.round=round;state.winData=data;
    state.matches=teams.map((pair,i)=>({number:i+1,home:names[pair[0]]||pair[0],away:names[pair[1]]||pair[1],codes:pair,kick:kick[i]||'',prob:pct[i]||[40,30,30]}));
    if(state.picks.length!==14)state.picks=Array(14).fill('');
    save();renderAll();el('updateStatus').textContent=`Datos descargados directamente · Temporada ${season} · Jornada ${round}`;
  }catch(e){el('updateStatus').textContent='No se pudo actualizar: '+e.message;el('updateStatus').classList.add('error')}finally{hideLoading()}},50)
}

function compactTime(x){if(!x)return '—';const d=x.slice(0,10).split('/'),time=x.slice(10);if(d.length<3)return x;const day=['DOM','LUN','MAR','MIÉ','JUE','VIE','SÁB'][new Date(+d[2],+d[1]-1,+d[0]).getDay()];return day+' '+time}
function renderMatches(){
  const box=el('matches');box.innerHTML='';
  state.matches.forEach((m,i)=>{
    if(i<14){const row=document.createElement('div');row.className='match';row.innerHTML=`<span class="num">${i+1}</span><span class="teams">${m.home} - ${m.away}</span><span class="meta">${compactTime(m.kick)}</span><span class="meta">${m.prob.map(x=>x.toFixed(0)).join('/')}</span><span class="picks">${SIGNS.map(s=>`<button class="pick ${state.picks[i].includes(s)?'on':''}" data-i="${i}" data-s="${s}">${s}</button>`).join('')}</span>`;box.appendChild(row)}
    else{const full=document.createElement('div');full.className='pleno';full.innerHTML=`<span class="teams">15. ${m.home}<br>${m.away}</span>${['0','1','2','M'].map(s=>`<button class="goal ${state.pleno[0]===s?'on':''}" data-side="0" data-g="${s}">${s}</button>`).join('')}${['0','1','2','M'].map(s=>`<button class="goal ${state.pleno[1]===s?'on':''}" data-side="1" data-g="${s}">${s}</button>`).join('')}`;box.appendChild(full)}
  });
  box.querySelectorAll('.pick').forEach(b=>b.onclick=()=>togglePick(+b.dataset.i,b.dataset.s));box.querySelectorAll('.goal').forEach(b=>b.onclick=()=>{state.pleno[+b.dataset.side]=b.dataset.g;save();renderMatches()});updatePrice()
}
function togglePick(i,s){let p=state.picks[i];p=p.includes(s)?p.replace(s,''):SIGNS.filter(x=>(p+s).includes(x)).join('');state.picks[i]=p;state.development=[];save();renderMatches()}
function useSuggestions(){if(!state.matches.length)return toast('Actualiza primero los datos');state.picks=state.matches.slice(0,14).map(m=>SIGNS[m.prob.indexOf(Math.max(...m.prob))]);state.development=[];save();renderMatches()}
function clearPicks(){state.picks=Array(14).fill('');state.pleno=['',''];state.development=[];save();renderAll()}
function baseSize(){return state.picks.every(Boolean)?state.picks.reduce((n,x)=>n*x.length,1):0}
function updatePrice(){const count=state.development.length||baseSize();el('price').textContent=count?`${count.toLocaleString('es-ES')} apuestas · ${(count*PRICE).toFixed(2)} €${state.development.length?' · desarrollo calculado':' · desarrollo completo'}`:'Selecciona al menos un signo en los 14 partidos'}

function probability(column){return [...column].reduce((p,s,i)=>p*((state.matches[i]?.prob[SIGNS.indexOf(s)]||0)/100),1)}
function maxRun(column,s){let best=0,n=0;for(const x of column){n=x===s?n+1:0;best=Math.max(best,n)}return best}
function ranges(){const n=id=>+el(id).value;return{v:[n('varMin'),n('varMax')],x:[n('xMin'),n('xMax')],t:[n('twoMin'),n('twoMax')],runs:{'1':n('run1'),'X':n('runX'),'2':n('run2')},ints:[n('intMin'),n('intMax')],limit:Math.max(2,n('limit')||125)}}
function validColumn(c,f){const x=[...c].filter(s=>s==='X').length,t=[...c].filter(s=>s==='2').length,v=x+t,ints=[...c].slice(1).filter((s,i)=>s!==c[i]).length;return v>=f.v[0]&&v<=f.v[1]&&x>=f.x[0]&&x<=f.x[1]&&t>=f.t[0]&&t<=f.t[1]&&ints>=f.ints[0]&&ints<=f.ints[1]&&SIGNS.every(s=>maxRun(c,s)<=f.runs[s])}
function makeColumns(maxCandidates=250000){if(!state.picks.every(Boolean))throw Error('Falta seleccionar algún partido');const total=baseSize();if(total>maxCandidates)throw Error(`La base contiene ${total.toLocaleString('es-ES')} columnas. Reduce triples/dobles antes de generar (máximo ${maxCandidates.toLocaleString('es-ES')}).`);let cols=[''];for(const pick of state.picks)cols=cols.flatMap(c=>[...pick].map(s=>c+s));return cols}
function generateDevelopment(){try{showLoading('Generando y aplicando condiciones…');setTimeout(()=>{try{const f=ranges(),all=makeColumns(),filtered=all.filter(c=>validColumn(c,f));filtered.sort((a,b)=>probability(b)-probability(a));state.development=filtered.slice(0,f.limit);save();renderDevelopment(all.length,filtered.length);updatePrice()}catch(e){toast(e.message)}finally{hideLoading()}},40)}catch(e){hideLoading();toast(e.message)}}
function optimizeBudget(){try{const max=Math.floor((+el('budget').value||15)/PRICE);let source=state.development.length?[...state.development]:makeColumns();source.sort((a,b)=>probability(b)-probability(a));state.development=source.slice(0,Math.max(2,max));save();renderDevelopment(source.length,source.length);updatePrice();showPage('develop')}catch(e){toast(e.message)}}
function renderDevelopment(base,filtered){const cols=state.development;el('devSummary').textContent=cols.length?`${base??baseSize()} columnas de base · ${filtered??cols.length} válidas · ${cols.length} finales · ${(cols.length*PRICE).toFixed(2)} €`:'Todavía no hay un desarrollo calculado.';el('columns').innerHTML=cols.slice(0,500).map((c,i)=>`<div class="column"><b>${i+1}. ${c}</b><span>${(probability(c)*100).toFixed(7)} %</span></div>`).join('')+(cols.length>500?`<div class="notice">Se muestran 500 de ${cols.length} columnas.</div>`:'')}

function exportTxt(){try{const cols=state.development.length?state.development:makeColumns();if(!state.pleno.every(Boolean))throw Error('Completa el Pleno al 15 antes de exportar');const text=cols.map(c=>c+state.pleno.join('')).join('\n')+'\n';Android.saveText(`quiniela_${state.season||'actual'}_J${String(state.round).padStart(2,'0')}_${cols.length}apuestas.txt`,text)}catch(e){toast(e.message)}}
function openPlaySite(){Android.openUrl(PLAY_URL)}
function onImportedText(text){const bets=text.split(/\r?\n/).map(x=>x.trim().toUpperCase().replace(/\s/g,'')).filter(Boolean);if(!bets.length||bets.some(x=>!/^([1X2]{14})([012M]{2})?$/.test(x)))return toast('TXT no válido: usa una apuesta de 14 o 16 signos por línea');state.imported=bets;save();el('hitsSummary').textContent=`TXT cargado: ${bets.length} apuestas`;refreshLive()}
function useCurrentDevelopment(){if(!state.development.length)return toast('Primero crea un desarrollo');state.imported=state.development.map(c=>c+(state.pleno.every(Boolean)?state.pleno.join(''):''));save();refreshLive()}

function refreshLive(){if(!state.season||!state.round)return toast('Actualiza primero los datos de la jornada');showLoading('Consultando resultados…');setTimeout(()=>{try{const raw=Android.fetchText(LIVE_URL+'?r='+Date.now());if(raw.startsWith('__ERROR__'))throw Error(raw.slice(9));const year=2000+(+state.season.slice(-2)),rows=JSON.parse(raw).filter(r=>+r.temporada===year&&+r.jornada===state.round).sort((a,b)=>+a.orden-+b.orden);if(rows.length!==15)throw Error(`El proveedor todavía no ofrece la jornada ${state.round}`);renderLive(rows);evaluateLive(rows);renderScrutiny()}catch(e){el('resultStatus').textContent='Sin actualización: '+e.message;el('resultStatus').classList.add('error')}finally{hideLoading()}},40)}
function liveInfo(r){const stateName=String(r.estado||''),final=/finalizado|terminado/i.test(stateName),live=String(r.live)==='1',pending=/sin comenzar|pendiente|aplazado|suspendido/i.test(stateName),valid=(final||live)&&!pending&&/^\d+$/.test(String(r.local_goles))&&/^\d+$/.test(String(r.visitante_goles));let score='—',sign='',pleno='';if(valid){const h=+r.local_goles,a=+r.visitante_goles;score=`${h}-${a}`;sign=h>a?'1':h<a?'2':'X';pleno=[h,a].map(x=>x>2?'M':x).join('')}return{...r,final,valid,score,sign,pleno,status:stateName+(pending?` · ${r.dia||''} ${r.hora||''}`:'')}}
function renderLive(rows){const info=rows.map(liveInfo);el('liveMatches').innerHTML=info.map((r,i)=>`<div class="live-row ${r.final?'final':''}"><b>${i+1}</b><span>${title(r.local)} - ${title(r.visitante)}</span><span class="score">${r.score}</span><span class="sign">${i===14?(r.pleno||'—'):(r.sign||'—')}</span><small class="state">${r.status}</small></div>`).join('');el('resultStatus').textContent=`Jornada ${state.round} · ${info.filter(x=>x.final).length}/15 finalizados · actualización ${new Date().toLocaleTimeString()}`;el('resultStatus').classList.remove('error');window.lastLive=info}
function title(x){return String(x||'').toLowerCase().replace(/(^|\s)\S/g,c=>c.toUpperCase())}
function evaluateLive(){const bets=state.imported.length?state.imported:state.development;if(!bets.length){el('hitsSummary').textContent='Carga un TXT o genera un desarrollo.';el('hits').innerHTML='';return}const known=window.lastLive.slice(0,14).filter(x=>x.sign),final=known.filter(x=>x.final),items=bets.map(b=>{const hits=known.filter(x=>b[x.orden-1]===x.sign).length,miss=final.filter(x=>b[x.orden-1]!==x.sign).length;return{b,hits,fixed:final.length-miss,max:14-miss}}).sort((a,b)=>b.hits-a.hits||b.max-a.max);el('hitsSummary').textContent=`${bets.length} apuestas · mejor: ${items[0].hits} de ${known.length} conocidos · máximo posible ${items[0].max}`;el('hits').innerHTML=items.slice(0,100).map(x=>`<div class="hit-row"><b>${x.b}</b><span>${x.hits} ahora</span><span>máx. ${x.max}</span></div>`).join('')}
function decodePleno(c){const g='012M',n=parseInt(c,16);return Number.isFinite(n)?g[Math.floor(n/4)]+g[n%4]:''}
function scrutiny(){const pre=state.winData?.['PRE'+state.season+'.TXT'];if(!pre)return null;const line=roundLine(pre,state.round),result=line.slice(104,118);if(!/^[1X2]{14}$/.test(result))return null;const pleno=decodePleno(line[118]),tokens=(line.slice(0,104).match(/\d[\d.]*,\d{2}|\d+/g)||[]),counts=tokens.slice(1,7).map(Number),amounts=tokens.slice(7,13).map(x=>+x.replace(/\./g,'').replace(',','.'));return{result,pleno,prizes:[15,14,13,12,11,10].map((cat,i)=>({cat,winners:counts[i]||0,amount:amounts[i]||0}))}}
function renderScrutiny(){const s=scrutiny(),bets=state.imported.length?state.imported:state.development;if(!s){el('prizes').textContent='El escrutinio definitivo todavía no está publicado en los datos descargados.';return}const counts={};bets.forEach(b=>{const h=[...s.result].filter((x,i)=>b[i]===x).length,cat=h===14&&b.slice(14)===s.pleno?15:h;counts[cat]=(counts[cat]||0)+1});let total=0;el('prizes').innerHTML=s.prizes.map(p=>{const mine=counts[p.cat]||0,sub=mine*p.amount;total+=sub;return`<div class="prize-row"><b>${p.cat===15?'14 + Pleno':p.cat+' aciertos'}</b><span>${mine} tuyas</span><span>${p.amount.toFixed(2)} €</span><strong>${sub.toFixed(2)} €</strong></div>`}).join('')+`<div class="big-result">Premio calculado: ${total.toFixed(2)} €</div>`}
function renderAll(){el('seasonLabel').textContent=state.season?`Temporada ${state.season} · J${state.round}`:'Aplicación autónoma';renderMatches();renderDevelopment();if(state.matches.length)el('updateStatus').textContent=`Datos guardados · Temporada ${state.season} · Jornada ${state.round}`}
restore();renderAll();
