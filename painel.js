// PROVA com a biblioteca Motion (motion.js, global Motion): mesma página, movimento feito por ela.
// Sem JavaScript, ou com "reduzir movimento" ligado no aparelho, a página aparece inteira e parada.
const calmo=matchMedia('(prefers-reduced-motion: reduce)').matches;
const vivo=!calmo&&!!window.Motion;
const mola={type:'spring',stiffness:120,damping:18};
const pulo={type:'spring',stiffness:320,damping:14};

if(vivo)(()=>{
 const {animate,scroll,inView,stagger}=Motion;
 document.documentElement.classList.add('mo');
 const todos=s=>[...document.querySelectorAll(s)];
 // some escondido (classe surge) e, terminada a entrada, a classe sai: o elemento fica visível mesmo sem estilo na tag
 const entra=(es,quadros,opc)=>{es=[...es];es.forEach(e=>e.classList.add('surge'));return ()=>animate(es,quadros,opc).then(()=>es.forEach(e=>e.classList.remove('surge')))};

 // título do topo: as palavras sobem uma a uma
 const h1=document.querySelector('.capa h1');
 if(h1){
  const fatia=no=>{
   for(const f of [...no.childNodes]){
    if(f.nodeType!=3){fatia(f);continue}
    const pedaco=document.createDocumentFragment();
    f.textContent.split(/(\s+)/).forEach(t=>{
     if(!t.trim()){pedaco.append(t);return}
     const s=document.createElement('span');
     s.className='pal';s.textContent=t;pedaco.append(s);
    });
    f.replaceWith(pedaco);
   }
  };
  fatia(h1);
  entra(h1.querySelectorAll('.pal'),{opacity:[0,1],y:[36,0],rotate:[6,0]},{...mola,delay:stagger(.07,{startDelay:.1})})();
  const resto=todos('.capa .olho,.capa .sub,.capa .botoes');
  entra(resto,{opacity:[0,1],y:[22,0]},{...mola,delay:stagger(.14,{startDelay:.25})})();
  const palco=document.querySelector('.palco');
  if(palco)entra([palco],{opacity:[0,1],scale:[.94,1]},{...mola,delay:.35})();
 }

 // barra de leitura no alto, presa à rolagem
 const barra=document.createElement('div');
 barra.className='progresso';
 document.body.append(barra);
 scroll(animate(barra,{scaleX:[0,1]},{ease:'linear'}));

 // celular do topo: sobe mais devagar que a página
 const capa=document.querySelector('.capa'), cel=document.querySelector('.palco .celular');
 if(capa&&cel)scroll(animate(cel,{y:[0,-90]},{ease:'linear'}),{target:capa,offset:['start start','end start']});

 // entrada ao rolar: os filhos de cada bloco entram em sequência, com mola
 const grupos=[
  ['.cab,.chamada .dentro',e=>[...e.children],{opacity:[0,1],y:[26,0]},.09,mola],
  ['.grade,.dupla',e=>[...e.children],{opacity:[0,1],y:[34,0],scale:[.93,1]},.1,mola],
  ['.pilha',e=>[...e.children],{opacity:[0,1],scale:[.5,1]},.045,pulo],
  ['.numeros',e=>[e],{opacity:[0,1],y:[26,0]},0,mola],
  ['details',e=>[e],{opacity:[0,1],x:[-24,0]},0,mola],
 ];
 for(const [sel,filhos,quadros,passo,jeito] of grupos)todos(sel).forEach(bloco=>{
  const vai=entra(filhos(bloco),quadros,{...jeito,delay:stagger(passo)});
  inView(bloco,()=>{
   vai();
   bloco.querySelectorAll('.numeros b').forEach(conta);  },{amount:.2});
 });

 // números contando de 0 até o valor ("23,3 mil", "3 por dia")
 function conta(b){
  const m=b.textContent.match(/^([\d,]+)(.*)$/);
  if(!m)return;
  const alvo=parseFloat(m[1].replace(',','.')), casas=(m[1].split(',')[1]||'').length;
  animate(0,alvo,{duration:1.5,ease:'easeOut',onUpdate:v=>{b.textContent=v.toFixed(casas).replace('.',',')+m[2]}});
 }

 // modo cinema (section.cine): os passos ficam presos na tela e a rolagem troca de capítulo, com fusão entre os vídeos
 const cine=document.querySelector('section.cine');
 if(cine){
  const ps=[...cine.querySelectorAll('.passo')];
  const faz=c=>{const d=document.createElement('div');d.className=c;return d};
  const trilho=faz('cine-trilho'), palco=faz('cine-palco'), fios=faz('cine-fios');
  ps[0].before(trilho);trilho.append(palco);palco.append(...ps,fios);
  trilho.style.height=ps.length*100+'svh';
  const fs=ps.map(()=>{const i=document.createElement('i');fios.append(i);return i});
  const vs=ps.map(p=>{const v=p.querySelector('video');v.classList.remove('rola');return v});
  let atual=-1, naTela=false;
  const troca=i=>{
   if(i==atual)return;
   const antes=ps[atual], novo=ps[i], desce=i>atual;
   atual=i;
   ps.forEach((p,k)=>p.classList.toggle('ativo',k==i));
   vs.forEach((v,k)=>{k==i&&naTela?v.play().catch(()=>{}):v.pause()});
   if(antes){animate(antes,{opacity:0},{duration:.35});animate(antes.firstElementChild,{y:[0,desce?-40:40]},{duration:.35})}
   animate(novo,{opacity:1},{duration:.5});
   animate(novo.firstElementChild,{y:[desce?50:-50,0]},mola);
   animate(novo.querySelector('.foto'),{scale:[1.05,1]},{duration:.7,ease:'easeOut'});
   animate(novo.querySelector('.n'),{scale:[0,1],rotate:[-90,0]},{...pulo,delay:.1});
  };
  scroll(p=>{
   const x=p*ps.length;
   troca(Math.max(0,Math.min(ps.length-1,Math.floor(x))));
   fs.forEach((f,k)=>f.style.setProperty('--p',Math.max(0,Math.min(1,x-k))));
  },{target:trilho,offset:['start start','end end']});
  inView(trilho,()=>{naTela=true;if(vs[atual])vs[atual].play().catch(()=>{});return ()=>{naTela=false;vs.forEach(v=>v.pause())}});
 }

 // passos: o texto vem do lado dele, o número pula e a tela cresce conforme a rolagem
 todos('.passo').filter(p=>!p.closest('.cine-palco')).forEach((p,i)=>{
  const texto=p.firstElementChild, n=p.querySelector('.n'), foto=p.querySelector('.foto');
  const lado=i%2?40:-40;
  const vai=entra([texto],{opacity:[0,1],x:[lado,0]},mola);
  inView(p,()=>{
   vai();
   if(n)animate(n,{scale:[0,1],rotate:[-90,0]},{...pulo,delay:.15});
  },{amount:.3});
  if(foto)scroll(animate(foto,{opacity:[.25,1],scale:[.86,1]},{ease:'linear'}),{target:foto,offset:['start end','start 0.5']});
 });
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

// abas de recursos: cada recurso mostra o vídeo da tela dele; quando o vídeo acaba, passa para o próximo.
// Com a Motion: um fundo só desliza de uma aba para a outra e o vídeo troca com fusão.
(()=>{
 const caixa=document.querySelector('.abas');
 if(!caixa)return;
 const lista=caixa.querySelector('.abas-lista');
 const bs=[...lista.querySelectorAll('button')], v=caixa.querySelector('video');
 let n=0, naTela=false, fundo=null;
 if(calmo)v.controls=true;
 if(vivo){fundo=document.createElement('div');fundo.className='aba-fundo';lista.prepend(fundo)}
 const poe=(mexe)=>{
  if(!fundo)return;
  const b=bs[n], alvo={y:b.offsetTop,height:b.offsetHeight};
  mexe?Motion.animate(fundo,alvo,{type:'spring',stiffness:260,damping:26}):Motion.animate(fundo,alvo,{duration:0});
 };
 function mostra(i,mexe){
  n=i;
  bs.forEach((b,k)=>{b.classList.toggle('ativa',k==i);b.setAttribute('aria-selected',k==i);b.lastElementChild.style.height='0'});
  v.poster='videos/'+bs[i].dataset.v+'.jpg';v.src='videos/'+bs[i].dataset.v+'.mp4';
  poe(mexe);
  if(vivo&&mexe)Motion.animate(v,{opacity:[0,1],scale:[1.04,1]},{duration:.55,ease:'easeOut'});
 }
 const toca=()=>v.play().catch(()=>{});
 bs.forEach((b,i)=>{b.onclick=()=>{mostra(i,true);toca()}});
 v.onended=()=>{mostra((n+1)%bs.length,true);if(naTela)toca()};
 v.ontimeupdate=()=>{if(v.duration)bs[n].lastElementChild.style.height=Math.min(100,100*v.currentTime/v.duration)+'%'};
 if('IntersectionObserver' in window)new IntersectionObserver(es=>{
  naTela=es[0].isIntersecting;
  if(naTela&&!calmo)toca();else v.pause();
 },{threshold:.3}).observe(v);
 addEventListener('resize',()=>poe(false));
 mostra(0,false);
})();
