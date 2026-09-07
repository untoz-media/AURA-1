const $=s=>document.querySelector(s), conversation=$('#conversation'), input=$('#message'), send=$('#send');
let ready=false,busy=false;
const toolLabels={calculator:'Calculator',datetime:'Date & time',files:'Files',system_info:'System'};
function setStatus(data){
  ready=data.state==='ready'; $('#statusDot').className=`dot ${data.state}`;
  $('#statusText').textContent=ready?'Ready':data.state==='error'?'Loading error':'Starting model…';
  $('#modelName').textContent=data.model?data.model.split('/').pop():'Loading'; $('#profileName').textContent=data.profile||'—';
  if(data.tools) $('#toolList').replaceChildren(...data.tools.map(t=>{const x=document.createElement('span');x.textContent=toolLabels[t]||t;return x;}));
  input.disabled=!ready; updateSend();
  if(data.error) addMessage(data.error,'assistant');
}
async function poll(){try{const r=await fetch('/api/status');const d=await r.json();setStatus(d);if(!ready&&d.state!=='error')setTimeout(poll,1000);}catch{setTimeout(poll,1500)}}
function updateSend(){send.disabled=!ready||busy||!input.value.trim()}
function addMessage(text,role){
  const welcome=$('.welcome');if(welcome)welcome.remove();
  const row=document.createElement('div');row.className=`message ${role}`;
  const bubble=document.createElement('div');bubble.className='bubble';bubble.textContent=text;
  if(role==='assistant'){const avatar=document.createElement('div');avatar.className='avatar';avatar.textContent='A';row.append(avatar)}
  row.append(bubble);conversation.append(row);conversation.scrollTop=conversation.scrollHeight;return row;
}
function typing(){const row=addMessage('','assistant'),b=row.querySelector('.bubble');b.classList.add('typing');b.innerHTML='<span></span><span></span><span></span>';return row}
async function submit(message){
  if(!ready||busy||!message.trim())return;busy=true;addMessage(message.trim(),'user');input.value='';input.style.height='auto';updateSend();const loader=typing();
  try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:message.trim()})});const d=await r.json();loader.remove();addMessage(r.ok?d.response:(d.error||'Ocorreu um erro.'),'assistant');}
  catch{loader.remove();addMessage('I lost the connection to the local server. Check that the AURA window is still open.','assistant')}
  finally{busy=false;updateSend();input.focus()}
}
$('#composer').addEventListener('submit',e=>{e.preventDefault();submit(input.value)});
input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,150)+'px';updateSend()});
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit(input.value)}});
document.addEventListener('click',e=>{const b=e.target.closest('[data-prompt]');if(b)submit(b.dataset.prompt)});
$('#newChat').addEventListener('click',async()=>{if(busy)return;await fetch('/api/clear',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});conversation.replaceChildren();addMessage('Conversation cleared. How can I help now?','assistant');if(innerWidth<761)$('.sidebar').classList.remove('open')});
$('#menuButton').addEventListener('click',()=>$('.sidebar').classList.toggle('open'));
poll();
