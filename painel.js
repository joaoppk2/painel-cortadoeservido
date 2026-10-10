// movimento das páginas do Painel: entrada ao rolar, números contando, telas do topo se alternando e barra de leitura.
// Sem JavaScript, ou com "reduzir movimento" ligado no aparelho, a página aparece inteira e parada.
(()=>{
 const calmo=matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(calmo||!('IntersectionObserver' in window))return;
 document.documentElement.classList.add('js');

 // entrada ao rolar: irmãos entram um depois do outro
 const alvos=document.querySelectorAll('.cab,.passo>*,.grade li,.numeros,.caixa,details,.pilha li,.chamada .dentro>*');
 const olho=new IntersectionObserver(vistos=>{
  for(const v of vistos){
   if(!v.isIntersecting)continue;
   const e=v.target;
   olho.unobserve(e);
   e.classList.add('visto');
   setTimeout(()=>{e.style.transitionDelay=''},900);
   e.querySelectorAll('b[data-conta]').forEach(conta);
  }
 },{threshold:.15,rootMargin:'0px 0px -6% 0px'});
 alvos.forEach(e=>{
  const i=[...e.parentNode.children].indexOf(e);
  e.classList.add('surge');
  e.style.transitionDelay=Math.min(i,7)*70+'ms';
  olho.observe(e);
 });

 // números contando de 0 até o valor ("23,3 mil", "3 por dia")
 document.querySelectorAll('.numeros b').forEach(b=>{
  const m=b.textContent.match(/^([\d,]+)(.*)$/);
  if(m){b.dataset.conta=m[1];b.dataset.resto=m[2]}
 });
 function conta(b){
  const alvo=parseFloat(b.dataset.conta.replace(',','.'));
  const casas=(b.dataset.conta.split(',')[1]||'').length;
  const t0=performance.now(), dura=1300;
  const passo=t=>{
   const p=Math.min(1,(t-t0)/dura), q=1-Math.pow(1-p,3);
   b.textContent=(alvo*q).toFixed(casas).replace('.',',')+b.dataset.resto;
   if(p<1)requestAnimationFrame(passo);
  };
  requestAnimationFrame(passo);
 }

 // telas do topo: Produção, Cortes e Calendário se alternam no computador e no celular
 const giras=[...document.querySelectorAll('.gira')];
 const nomes=[...document.querySelectorAll('.telas span')];
 let n=0;
 if(giras.length)setInterval(()=>{
  if(document.hidden)return;
  n=(n+1)%3;
  giras.forEach(g=>[...g.children].forEach((img,i)=>img.classList.toggle('vista',i==n)));
  nomes.forEach((s,i)=>s.classList.toggle('vista',i==n));
 },3400);

 // barra de leitura no alto
 const barra=document.createElement('div');
 barra.className='progresso';
 document.body.append(barra);
 const mede=()=>{
  const total=document.documentElement.scrollHeight-innerHeight;
  barra.style.transform='scaleX('+(total>0?scrollY/total:0)+')';
 };
 addEventListener('scroll',mede,{passive:true});
 mede();
})();

// os dois vídeos do topo (computador e celular) mostram o mesmo roteiro: o do celular segue o relógio do outro
(()=>{
 const pc=document.querySelector('.janela video'), cel=document.querySelector('.palco .celular video');
 if(!pc||!cel)return;
 cel.loop=false;
 const acerta=()=>{
  if(Math.abs(cel.currentTime-pc.currentTime)>.12)cel.currentTime=pc.currentTime;
  if(cel.paused&&!pc.paused)cel.play().catch(()=>{});
 };
 for(const e of['playing','seeked'])pc.addEventListener(e,acerta);
 setInterval(acerta,700);
})();

// vídeos dos passos: tocam só enquanto estão na tela
(()=>{
 const vs=document.querySelectorAll('video.rola');
 if(!vs.length||!('IntersectionObserver' in window))return vs.forEach(v=>{v.controls=true});
 const olho=new IntersectionObserver(es=>es.forEach(e=>{e.isIntersecting?e.target.play().catch(()=>{}):e.target.pause()}),{threshold:.35});
 vs.forEach(v=>olho.observe(v));
})();
