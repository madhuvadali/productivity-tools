// India Makerspace Map — each data layer is a CSV listed in DATA_FILES.
// Sources and confidence rules: databases/SOURCES.md
const DATA_FILES = ['data/idea_labs_map.csv','data/higher_ed_institute_makerspaces_map.csv',
                    'data/maker_bhavan_tinkerers_labs_map.csv','data/community_makerspaces_checked_map.csv',
                    'data/government_prototyping_hubs_map.csv','data/incubators_with_makerspaces_map.csv',
                    'data/fablabs_checked_map.csv'];
const TYPE_COLORS = {'IDEA Lab (AICTE, higher education)':'#2563eb','Institute makerspace (IIT/NIT/IIIT/IISc/IISER)':'#7c3aed',"Tinkerers' Lab (Maker Bhavan network)":'#db2777','Community makerspace':'#0f766e','Government prototyping hub':'#d97706','Incubator with makerspace':'#dc2626',FabLab:'#c026d3'};
const CONFIDENCE_LABEL = {high:'Verified from official source', medium:'Partly verified', low:'Unverified'};
const BADGE_LABEL = {high:'Verified', medium:'Partly verified', low:'Unverified'};
const TRUST_ORDER = {high:0, medium:1, low:2};
const PRECISION_LABEL = {manual:'Pin checked by hand', campus:'Pin at campus', site:'Pin at site', self_reported:'Pin from FabLabs.io (self-reported)', pin_area:'Approximate pin: PIN-code area', town:'Approximate pin: town centre'};
const EXACT = ['campus','site','manual'];
const FALLBACK = '#78716c';
const colorOf = t => TYPE_COLORS[t] || FALLBACK;
const isApprox = d => !!d.location_precision && !EXACT.includes(d.location_precision);

function parseCSV(text){
  const rows=[];let row=[],f='',q=false;
  text=text.replace(/^﻿/,'');
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(q){ if(c==='"'){ if(text[i+1]==='"'){f+='"';i++;} else q=false; } else f+=c; }
    else if(c==='"') q=true;
    else if(c===','){row.push(f);f='';}
    else if(c==='\n'||c==='\r'){ if(c==='\r'&&text[i+1]==='\n')i++; row.push(f);f=''; if(row.some(x=>x.trim()!==''))rows.push(row); row=[]; }
    else f+=c;
  }
  if(f!==''||row.length){row.push(f);if(row.some(x=>x.trim()!==''))rows.push(row);}
  if(!rows.length) return [];
  const head=rows.shift().map(h=>h.trim().toLowerCase());
  return rows.map(r=>Object.fromEntries(head.map((h,i)=>[h,(r[i]||'').trim()])));
}

const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let data=[], allTypes=[], activeTypes=new Set(), activeId=null, popup=null;

const map=new maplibregl.Map({
  container:'map',
  style:'https://tiles.openfreemap.org/styles/positron',
  center:[78.9,22.5], zoom:4.3,
  attributionControl:false
});
map.addControl(new maplibregl.NavigationControl({showCompass:false}),'top-right');
map.addControl(new maplibregl.AttributionControl({compact:true,customAttribution:'Locations geocoded with <a href="https://nominatim.org" target="_blank" rel="noopener">Nominatim</a>, <a href="databases/SOURCES.md" target="_blank" rel="noopener">data sources</a>'}));
map.addControl(new maplibregl.GeolocateControl({}),'top-right');

// On-map category checkboxes, stacked under the zoom/locate buttons in the top-right corner.
class CategoryFilterControl{
  onAdd(){
    this._el=document.createElement('div');
    this._el.className='maplibregl-ctrl map-filter';
    return this._el;
  }
  onRemove(){ this._el.parentNode?.removeChild(this._el); }
  build(){
    this._el.innerHTML=`<div class="map-filter-title">Categories</div>`+allTypes.map((t,i)=>{
      const id='mf-'+i;
      return `<label class="map-filter-row" for="${id}">
        <input type="checkbox" id="${id}" data-t="${esc(t)}" ${activeTypes.has(t)?'checked':''}>
        <span class="dot" style="background:${colorOf(t)}"></span>
        <span class="map-filter-label">${esc(t)}</span>
      </label>`;
    }).join('');
    this._el.querySelectorAll('input[type=checkbox]').forEach(cb=>
      cb.addEventListener('change',()=>{
        const t=cb.dataset.t;
        if(cb.checked) activeTypes.add(t);
        else { activeTypes.delete(t); if(!activeTypes.size) activeTypes=new Set(allTypes); }
        render(true);
      }));
  }
  sync(){
    this._el?.querySelectorAll('input[type=checkbox]').forEach(cb=>{ cb.checked=activeTypes.has(cb.dataset.t); });
  }
}
const mapFilter=new CategoryFilterControl();
map.addControl(mapFilter,'top-right');
const mapReady=new Promise(r=>map.on('load',r));

async function init(){
  let rows=[];
  for(const file of DATA_FILES){
    try{
      const res=await fetch(file+'?'+Date.now());
      if(!res.ok) throw new Error(res.status);
      rows=rows.concat(parseCSV(await res.text()));
    }catch(e){ console.warn('Skipped layer',file,e); }
  }
  if(!rows.length){
    $('list').innerHTML='<li class="empty">No data files found in the data folder. Run the geocoding scripts first, then open this page through a local server (Live Server in VS Code).</li>';
    return;
  }
  data=rows.map(r=>({...r,lat:parseFloat(r.latitude),lng:parseFloat(r.longitude)}))
       .filter(r=>isFinite(r.lat)&&isFinite(r.lng))
       .map((r,i)=>({...r,id:i}));
  const known=Object.keys(TYPE_COLORS);
  allTypes=[...new Set(data.map(d=>d.type).filter(Boolean))]
    .sort((a,b)=>(known.indexOf(a)+1||99)-(known.indexOf(b)+1||99)||a.localeCompare(b));
  activeTypes=new Set(allTypes);
  fillSelect($('state'),uniq(data.map(d=>d.state)),'All states');
  fillCities();
  fillAbout();
  mapFilter.build();

  await mapReady;
  map.addSource('ms',{type:'geojson',data:fc([])});
  map.addLayer({id:'ms-sel',type:'circle',source:'ms',filter:['==',['get','id'],-1],paint:{
    'circle-radius':13,'circle-color':'#fff','circle-stroke-color':'#1f2328','circle-stroke-width':2}});
  map.addLayer({id:'ms-pts',type:'circle',source:'ms',paint:{
    'circle-radius':7,'circle-color':['get','color'],'circle-stroke-color':'#fff','circle-stroke-width':1.5,
    'circle-opacity':['case',['get','approx'],0.45,1],'circle-stroke-opacity':['case',['get','approx'],0.6,1]}});

  map.on('click','ms-pts',e=>select(e.features[0].properties.id,false));
  map.on('mouseenter','ms-pts',()=>map.getCanvas().style.cursor='pointer');
  map.on('mouseleave','ms-pts',()=>map.getCanvas().style.cursor='');
  render(true);
}

const uniq=a=>[...new Set(a.filter(Boolean))].sort((x,y)=>x.localeCompare(y));
const fc=features=>({type:'FeatureCollection',features});
function fillSelect(el,vals,all){
  const cur=el.value;
  el.innerHTML=`<option value="">${all}</option>`+vals.map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');
  if(vals.includes(cur)) el.value=cur;
}
function fillCities(){
  const s=$('state').value;
  fillSelect($('city'),uniq(data.filter(d=>!s||d.state===s).map(d=>d.city)),'All cities');
}

// Filters. `skip` leaves one filter out, so counts next to a control show what choosing it would give.
function matches(d,skip=''){
  const q=$('search').value.trim().toLowerCase(), s=$('state').value, c=$('city').value;
  const conf=[...document.querySelectorAll('.conf:checked')].map(x=>x.value);
  if(skip!=='type'&&!activeTypes.has(d.type)) return false;
  if(skip!=='place'&&s&&d.state!==s) return false;
  if(skip!=='place'&&c&&d.city!==c) return false;
  if(!conf.includes(d.verified||'low')) return false;
  if($('exact').checked&&isApprox(d)) return false;
  if(q&&![d.name,d.institution,d.city,d.state,d.description,d.type].join(' ').toLowerCase().includes(q)) return false;
  return true;
}
function sorted(rows){
  const k=$('sort').value, byName=(a,b)=>a.name.localeCompare(b.name);
  const cmp={
    name:byName,
    state:(a,b)=>(a.state||'').localeCompare(b.state||'')||(a.city||'').localeCompare(b.city||'')||byName(a,b),
    type:(a,b)=>allTypes.indexOf(a.type)-allTypes.indexOf(b.type)||byName(a,b),
    trust:(a,b)=>(TRUST_ORDER[a.verified]??3)-(TRUST_ORDER[b.verified]??3)||byName(a,b)
  }[k]||byName;
  return rows.slice().sort(cmp);
}

function render(fit){
  const rows=sorted(data.filter(d=>matches(d)));
  const n=rows.length, word=n===1?'place':'places';
  $('count').textContent=n===data.length?`${data.length} places across India`:`Showing ${n} of ${data.length} places`;
  $('list-count').textContent=`${n} ${word}`;

  renderChips();
  renderStateBars();
  mapFilter.sync();

  if(map.getSource('ms')) map.getSource('ms').setData(fc(rows.map(d=>({type:'Feature',
    geometry:{type:'Point',coordinates:[d.lng,d.lat]},
    properties:{id:d.id,color:colorOf(d.type),approx:isApprox(d)}}))));

  if(activeId!==null&&!rows.some(d=>d.id===activeId)) clearSelection();

  $('list').innerHTML=n?rows.map(d=>`<li data-id="${d.id}" tabindex="0" class="${d.id===activeId?'active':''}"${d.id===activeId?' aria-current="true"':''}>
    <span class="dot" style="background:${colorOf(d.type)}${isApprox(d)?';opacity:.45':''}" title="${esc(d.type)}"></span>
    <span class="name">${esc(d.name)}</span>
    <span class="meta">${esc([d.city,d.state].filter(Boolean).join(', '))}${d.verified?`<span class="badge ${esc(d.verified)}">${esc(BADGE_LABEL[d.verified]||d.verified)}</span>`:''}</span></li>`).join('')
    :'<li class="empty">No places match these filters. Try clearing the search or choosing "Clear all filters".</li>';

  if(fit&&n&&map.getSource('ms')){
    const b=new maplibregl.LngLatBounds(); rows.forEach(d=>b.extend([d.lng,d.lat]));
    map.fitBounds(b,{padding:fitPadding(),maxZoom:n===1?12:7,duration:600});
  }
}
function fitPadding(){
  if(window.matchMedia('(max-width:760px)').matches){
    const h=$('sidebar').getBoundingClientRect().height;
    return {top:50,left:30,right:30,bottom:Math.min(h+20,window.innerHeight*0.6)};
  }
  return 60;
}

function renderChips(){
  const counts={}; data.forEach(d=>{ if(matches(d,'type')) counts[d.type]=(counts[d.type]||0)+1; });
  const existing=!!$('types').children.length;
  if(existing){
    // keep the existing checkboxes (and focus) in place; just sync state and counts
    $('types').querySelectorAll('.chip').forEach(chip=>{
      const t=chip.dataset.t, cb=chip.querySelector('input');
      cb.checked=activeTypes.has(t);
      chip.querySelector('.n').textContent=counts[t]||0;
    });
    return;
  }
  $('types').innerHTML=allTypes.map((t,i)=>`<label class="chip" data-t="${esc(t)}" style="--c:${colorOf(t)}">
    <input type="checkbox" id="chip-${i}" ${activeTypes.has(t)?'checked':''}>
    <span class="dot" aria-hidden="true"></span><span>${esc(t)}</span><span class="n">${counts[t]||0}</span></label>`).join('');
}
function renderStateBars(){
  const counts={}; data.forEach(d=>{ if(d.state&&matches(d,'place')) counts[d.state]=(counts[d.state]||0)+1; });
  const list=Object.entries(counts).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
  const max=list.length?list[0][1]:1, cur=$('state').value;
  $('state-bars').innerHTML=list.length?list.map(([s,v])=>`<li><button data-s="${esc(s)}" aria-pressed="${s===cur}" title="Show only ${esc(s)}">
    <span>${esc(s)}</span><span class="bar" style="width:${Math.max(4,v/max*100)}%"></span><span class="v">${v}</span></button></li>`).join('')
    :'<li class="muted">No places match.</li>';
}
function fillAbout(){
  const counts={}; data.forEach(d=>counts[d.type]=(counts[d.type]||0)+1);
  $('about-cats').innerHTML=allTypes.map(t=>`<li><span class="dot" style="background:${colorOf(t)}"></span><span>${esc(t)}</span><span class="muted">${counts[t]}</span></li>`).join('');
}

function clearSelection(){
  activeId=null; if(popup){popup.remove();popup=null;}
  if(map.getLayer('ms-sel')) map.setFilter('ms-sel',['==',['get','id'],-1]);
}
function select(id,fly=true){
  const d=data[id]; if(!d)return; activeId=id;
  if(popup)popup.remove();
  popup=new maplibregl.Popup({offset:12,maxWidth:'300px'}).setLngLat([d.lng,d.lat]).setHTML(
    `<h3>${esc(d.name)}</h3><div class="muted">${esc([d.type,d.city,d.state].filter(Boolean).join(', '))}</div>
     ${d.description?`<p>${esc(d.description)}</p>`:''}${d.address?`<div>${esc(d.address)}</div>`:''}
     ${/^https?:\/\//.test(d.website)?`<div><a href="${esc(d.website)}" target="_blank" rel="noopener">Website</a></div>`:''}
     ${d.contact?`<div>${esc(d.contact)}</div>`:''}
     <div class="prov">
       ${d.verified?`<span><span class="badge ${esc(d.verified)}">${esc(CONFIDENCE_LABEL[d.verified]||d.verified)}</span></span>`:''}
       ${d.status&&d.status!=='active'&&d.status!=='listed'?`<div>Status: ${esc(d.status)}</div>`:''}
       ${d.location_precision?`<div>${esc(PRECISION_LABEL[d.location_precision]||d.location_precision)}</div>`:''}
       ${/^https?:\/\//.test(d.source_url)?`<div><a href="${esc(d.source_url)}" target="_blank" rel="noopener">Address source</a></div>`:''}
       ${d.notes?`<div class="note">${esc(d.notes)}</div>`:''}
     </div>`).addTo(map);
  popup.on('close',()=>{ if(activeId===id){ activeId=null; map.setFilter('ms-sel',['==',['get','id'],-1]);
    document.querySelectorAll('#list li.active').forEach(li=>{li.classList.remove('active');li.removeAttribute('aria-current');}); } });
  map.setFilter('ms-sel',['all',['!',['has','point_count']],['==',['get','id'],id]]);
  if(fly)map.flyTo({center:[d.lng,d.lat],zoom:Math.max(map.getZoom(),11),duration:700,padding:fitPadding()});
  document.querySelectorAll('#list li').forEach(li=>{
    const on=+li.dataset.id===id; li.classList.toggle('active',on);
    on?li.setAttribute('aria-current','true'):li.removeAttribute('aria-current');
  });
  const li=document.querySelector(`#list li[data-id="${id}"]`); if(li)li.scrollIntoView({block:'nearest'});
}

// Controls
$('search').addEventListener('input',()=>render(true));
$('state').addEventListener('change',()=>{fillCities();render(true);});
$('city').addEventListener('change',()=>render(true));
$('sort').addEventListener('change',()=>render(false));
$('exact').addEventListener('change',()=>render(false));
document.querySelectorAll('.conf').forEach(c=>c.addEventListener('change',()=>render(false)));
$('types').addEventListener('change',e=>{
  const cb=e.target; const c=cb.closest('.chip'); if(!c)return;
  const t=c.dataset.t;
  if(cb.checked) activeTypes.add(t);
  else { activeTypes.delete(t); if(!activeTypes.size) activeTypes=new Set(allTypes); }
  render(true);
});
$('state-bars').addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b)return;
  $('state').value=$('state').value===b.dataset.s?'':b.dataset.s;
  fillCities(); render(true);
  const again=document.querySelector(`#state-bars button[data-s="${CSS.escape(b.dataset.s)}"]`); if(again)again.focus();
});
$('reset').addEventListener('click',()=>{
  $('search').value=''; $('state').value=''; fillCities(); $('city').value='';
  document.querySelectorAll('.conf').forEach(c=>c.checked=true); $('exact').checked=false;
  activeTypes=new Set(allTypes); render(true);
});
$('list').addEventListener('click',e=>{const li=e.target.closest('li[data-id]');if(li)select(+li.dataset.id);});
$('list').addEventListener('keydown',e=>{
  const li=e.target.closest('li[data-id]'); if(!li)return;
  if(e.key==='Enter'||e.key===' '){e.preventDefault();select(+li.dataset.id);}
  else if(e.key==='ArrowDown'&&li.nextElementSibling){e.preventDefault();li.nextElementSibling.focus();}
  else if(e.key==='ArrowUp'&&li.previousElementSibling){e.preventDefault();li.previousElementSibling.focus();}
});

// About dialog
$('about-open').addEventListener('click',()=>$('about').showModal());
$('about-close').addEventListener('click',()=>$('about').close());
$('about').addEventListener('click',e=>{ if(e.target===$('about')) $('about').close(); });

// Phone bottom sheet
$('sheet-toggle').addEventListener('click',()=>{
  const open=$('sidebar').classList.toggle('expanded');
  $('sheet-toggle').textContent=open?'Show map':'Show list';
  $('sheet-toggle').setAttribute('aria-expanded',open);
});

init();
