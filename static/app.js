const $=s=>document.querySelector(s);
$('#burger')?.addEventListener('click',()=>$('#menu').classList.toggle('open'));
addEventListener('scroll',()=>{const h=document.documentElement;$('#progress').style.width=(h.scrollTop/(h.scrollHeight-h.clientHeight)*100)+'%';$('#top').classList.toggle('show',h.scrollTop>400)});
$('#top').onclick=()=>scrollTo({top:0,behavior:'smooth'});
const io=new IntersectionObserver(es=>es.forEach(e=>e.isIntersecting&&e.target.classList.add('in')),{threshold:.1});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
const facts=["Bitta daraxt yiliga 4 kishini kislorod bilan ta'minlaydi.","1 tonna qog'ozni qayta ishlash 17 ta daraxtni saqlab qoladi.","Shisha tabiatda 1 million yilgacha parchalanmaydi.","Amazon o'rmonlari dunyo kislorodining ~20% ini ishlab chiqaradi.","Jo'mrakdan tomchilagan suv yiliga 10 000 litrgacha isrof bo'ladi.","Orol dengizi 60 yilda hajmining 90% idan ko'prog'ini yo'qotdi."];
let fi=0;$('#nextFact')?.addEventListener('click',()=>{fi=(fi+1)%facts.length;$('#fact').textContent=facts[fi]});
$('#filter')?.addEventListener('input',e=>{const v=e.target.value.toLowerCase();document.querySelectorAll('#list .card').forEach(c=>c.style.display=c.dataset.name.includes(v)?'':'none')});
const tips=document.querySelectorAll('.tip');
if(tips.length){const saved=JSON.parse(localStorage.eko||'{}');const upd=()=>{const n=[...tips].filter(t=>t.checked).length,p=Math.round(n/tips.length*100);$('#pbar').style.width=p+'%';$('#ptext').textContent=p+'%'};
tips.forEach(t=>{t.checked=!!saved[t.dataset.id];t.onchange=()=>{saved[t.dataset.id]=t.checked;localStorage.eko=JSON.stringify(saved);upd()}});upd()}
