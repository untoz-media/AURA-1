const $=s=>document.querySelector(s), conversation=$('#conversation'), input=$('#message'), send=$('#send');
let ready=false,busy=false,stateTimer=null,setupFlowActive=false,setupLoaded=false,selectedProfile='balanced';
const toolLabels={calculator:'Calculator',datetime:'Date & time',files:'Files',system_info:'System',disk_info:'Disk',app_launcher:'Apps',process_manager:'Processes',file_manager:'Folders',system_state:'PC awareness'};
const capabilityLabels={local_chat:'Local chat',persistent_memory:'Memory',app_launcher:'App launcher',app_discovery:'App discovery',process_manager:'Processes',file_manager:'Files',system_state:'PC awareness',state_awareness:'State-aware',result_recovery:'Safe recovery'};
const stepLabels={welcome:'Welcome',hardware:'Computer check',model:'Model setup',privacy:'Privacy & control',ready:'AURA setup'};

function setCoreState(state){document.querySelectorAll('.aura-core').forEach(core=>{core.dataset.auraState=state;core.setAttribute('aria-label',`AURA Core, ${state}`)})}
function showStep(name){
  document.querySelectorAll('[data-setup-step]').forEach(x=>x.classList.toggle('active',x.dataset.setupStep===name));
  const names=['welcome','hardware','model','privacy','ready'],current=names.indexOf(name);
  document.querySelectorAll('[data-step-dot]').forEach((dot,i)=>{dot.classList.toggle('active',i===current);dot.classList.toggle('done',i<current)});
  $('#setupStepLabel').textContent=stepLabels[name]||'Setup';
}
function enterApp(){
  document.body.classList.remove('setup-active');$('#onboarding').setAttribute('aria-hidden','true');$('#appShell').setAttribute('aria-hidden','false');
  if(ready&&!stateTimer){pollSystemState();stateTimer=setInterval(pollSystemState,5000)}
  input.focus();
}
function showSetup(){document.body.classList.add('setup-active');$('#onboarding').removeAttribute('aria-hidden');$('#appShell').setAttribute('aria-hidden','true')}

function setStatus(data){
  ready=data.state==='ready';$('#setupVersion').textContent=data.version||'—';$('#statusDot').className=`dot ${data.state}`;
  $('#statusText').textContent=ready?'Ready':data.state==='error'?'Loading error':data.state==='setup'?'Setup required':'Starting model…';
  $('#modelName').textContent=data.model?data.model.split('/').pop():'Loading';$('#profileName').textContent=data.profile||'—';$('#runtimeName').textContent=data.agent_runtime?`v${data.agent_runtime}`:'—';
  const labels=data.capabilities||data.tools||[];
  if(labels.length)$('#toolList').replaceChildren(...labels.map(t=>{const x=document.createElement('span');x.textContent=capabilityLabels[t]||toolLabels[t]||t;return x}));
  input.disabled=!ready;updateSend();
  if(data.state==='setup'){setupFlowActive=true;showSetup();showStep('welcome');setCoreState('idle');if(!setupLoaded)loadSetup();return}
  if(data.state==='loading'||data.state==='booting'){showSetup();showStep('ready');setPreparingState();setCoreState('thinking');return}
  if(data.state==='error'){showSetup();showStep('ready');setErrorState(data.error||'The local model could not be started.');setCoreState('idle');return}
  if(ready){setCoreState('idle');if(setupFlowActive)setReadyState();else enterApp()}
}
async function poll(){try{const r=await fetch('/api/status'),d=await r.json();setStatus(d);if(d.state!=='ready'||setupFlowActive)setTimeout(poll,900)}catch{setTimeout(poll,1500)}}

function setPreparingState(){
  $('#readyTitle').textContent='Preparing AURA…';$('#readyMessage').textContent='Starting the local model. On a first install this can include downloading model files.';
  $('#modelProgress').hidden=false;$('#setupError').hidden=true;$('#retrySetup').hidden=true;$('#enterAura').hidden=true;
}
function setReadyState(){
  showSetup();showStep('ready');$('#readyTitle').textContent='AURA is ready.';$('#readyMessage').textContent='Your local assistant is configured and the Agent Runtime is online.';
  $('#modelProgress').hidden=true;$('#setupError').hidden=true;$('#retrySetup').hidden=true;$('#enterAura').hidden=false;setCoreState('idle');
}
function setErrorState(message){
  $('#readyTitle').textContent='AURA could not start.';$('#readyMessage').textContent='Your setup choices are safe. Fix the local runtime issue, then retry the model start.';
  $('#modelProgress').hidden=true;$('#setupError').hidden=false;$('#setupError').textContent=message;$('#retrySetup').hidden=false;$('#enterAura').hidden=true;
}

async function loadSetup(force=false){
  if(setupLoaded&&!force)return;
  const status=$('#hardwareStatus');status.className='hardware-status loading';status.querySelector('b').textContent='Checking this computer…';
  try{
    const r=await fetch('/api/setup'),d=await r.json();if(!r.ok)throw new Error(d.error||'Hardware check failed.');
    setupLoaded=true;selectedProfile=d.profile||'balanced';$('#setupModelName').textContent=(d.model||'Local model').split('/').pop();renderProfiles(d.profiles||[]);renderHardware(d.hardware||{});
  }catch(err){status.className='hardware-status unsupported';status.querySelector('b').textContent='Hardware check unavailable';status.querySelector('small').textContent=err.message;$('#hardwareContinue').disabled=true}
}
function renderProfiles(profiles){
  const root=$('#profileChoices');root.replaceChildren();
  profiles.forEach(p=>{
    const label=document.createElement('label');label.className=`profile-choice${p.id===selectedProfile?' selected':''}`;
    const radio=document.createElement('input');radio.type='radio';radio.name='aura-profile';radio.value=p.id;radio.checked=p.id===selectedProfile;
    const name=document.createElement('b');name.textContent=p.name;const desc=document.createElement('span');desc.textContent=p.description;const tag=document.createElement('em');tag.textContent=p.id==='balanced'?'Recommended':p.id==='fast'?'Lowest latency':'More reasoning';
    label.append(radio,name,desc,tag);label.addEventListener('click',()=>{selectedProfile=p.id;document.querySelectorAll('.profile-choice').forEach(x=>x.classList.remove('selected'));label.classList.add('selected');radio.checked=true});root.append(label);
  });
}
function hardwareItem(label,value,detail){const item=document.createElement('div');item.className='hardware-item';const l=document.createElement('span');l.textContent=label;const v=document.createElement('b');v.textContent=value;const d=document.createElement('small');d.textContent=detail||'';item.append(l,v,d);return item}
function renderHardware(h){
  const status=$('#hardwareStatus'),title=status.querySelector('b'),detail=status.querySelector('small');status.className=`hardware-status ${h.status||'limited'}`;
  const statusText={ready:'This computer looks ready',limited:'AURA can continue with caveats',unsupported:'Setup cannot continue yet'};title.textContent=statusText[h.status]||'Hardware check complete';
  detail.textContent=h.status==='ready'?'Meets the recommended Alpha 2 baseline.':h.status==='unsupported'?'Resolve the items below before loading the model.':'Review the recommendations below.';
  const grid=$('#hardwareGrid');grid.hidden=false;grid.replaceChildren();grid.append(
    hardwareItem('CPU',`${h.cpu_logical??'—'} threads`,`${h.operating_system||'Unknown'} · ${h.architecture||'Unknown'}`),
    hardwareItem('Memory',`${h.ram_total_gb??'—'} GB`,`${h.ram_available_gb??'—'} GB available`),
    hardwareItem('Storage',`${h.disk_free_gb??'—'} GB free`,'Model cache + app data'),
    hardwareItem('GPU',h.gpu?.name||'CPU mode',h.gpu?.available?`${h.gpu.vram_gb??'—'} GB VRAM · CUDA`:'No CUDA acceleration detected')
  );
  const notes=$('#hardwareNotes');notes.replaceChildren();(h.blockers||[]).forEach(text=>{const x=document.createElement('div');x.className='setup-note blocker';x.textContent=text;notes.append(x)});(h.warnings||[]).forEach(text=>{const x=document.createElement('div');x.className='setup-note';x.textContent=text;notes.append(x)});$('#hardwareContinue').disabled=!h.can_continue;
}
function updateConsent(){$('#prepareAura').disabled=!($('#privacyConsent').checked&&$('#permissionConsent').checked)}
async function completeSetup(){
  if(busy)return;busy=true;$('#prepareAura').disabled=true;setupFlowActive=true;showStep('ready');setPreparingState();setCoreState('thinking');
  try{
    const r=await fetch('/api/setup/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({profile:selectedProfile,privacy_acknowledged:$('#privacyConsent').checked,permission_boundary_acknowledged:$('#permissionConsent').checked})}),d=await r.json();
    if(!r.ok){setErrorState(d.error||'Setup could not be completed.');if(d.hardware)renderHardware(d.hardware);return}setTimeout(poll,350);
  }catch{setErrorState('I lost the connection to the local AURA service during setup.')}finally{busy=false}
}
async function retryModel(){
  if(busy)return;busy=true;setPreparingState();setCoreState('thinking');
  try{const r=await fetch('/api/setup/retry',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}),d=await r.json();if(!r.ok){setErrorState(d.error||'Could not retry the model start.');return}setTimeout(poll,350)}catch{setErrorState('I could not reach the local AURA service.')}finally{busy=false}
}

async function pollSystemState(){if(!ready||document.body.classList.contains('setup-active'))return;try{const r=await fetch('/api/system-state');if(!r.ok)return;const d=await r.json();$('#cpuValue').textContent=`${d.cpu_percent??'—'}%`;$('#ramValue').textContent=`${d.ram?.percentagem_usada??'—'}%`;$('#pressureValue').textContent=d.pressao||'—';$('#pressureValue').dataset.pressure=d.pressao||'normal';const battery=d.bateria;$('#batteryValue').textContent=battery?`${battery.percentagem??'—'}%`:'Desktop';$('#foregroundValue').textContent=d.foreground_app||'—'}catch{}}
function updateSend(){send.disabled=!ready||busy||!input.value.trim()}
function clearWelcome(){const welcome=$('.welcome');if(welcome)welcome.remove()}
function addMessage(text,role){clearWelcome();const row=document.createElement('div');row.className=`message ${role}`;const bubble=document.createElement('div');bubble.className='bubble';bubble.textContent=text;if(role==='assistant'){const avatar=document.createElement('div');avatar.className='avatar';avatar.innerHTML='<i></i>';row.append(avatar)}row.append(bubble);conversation.append(row);conversation.scrollTop=conversation.scrollHeight;return row}
function addCard(className){clearWelcome();const row=document.createElement('div');row.className='message assistant structured';const avatar=document.createElement('div');avatar.className='avatar';avatar.innerHTML='<i></i>';const card=document.createElement('div');card.className=`agent-card ${className}`;row.append(avatar,card);conversation.append(row);conversation.scrollTop=conversation.scrollHeight;return card}
function typing(){const row=addMessage('','assistant'),b=row.querySelector('.bubble');b.classList.add('typing');b.innerHTML='<span></span><span></span><span></span>';return row}
function renderPhases(phases=[]){phases.forEach(phase=>{const card=addCard('plan-card');const head=document.createElement('div');head.className='card-head';const label=document.createElement('span');label.className='card-kicker';label.textContent=phase.label||'Plan';const status=document.createElement('span');status.className=`plan-status ${phase.status||''}`;status.textContent=(phase.status||'ready').replaceAll('_',' ');head.append(label,status);const title=document.createElement('strong');title.textContent=phase.description||'AURA plan';card.append(head,title);const list=document.createElement('ol');list.className='plan-steps';const results=phase.results||[];(phase.actions||[]).forEach((action,i)=>{const li=document.createElement('li');const result=results[i];const icon=document.createElement('span');icon.className='step-icon';icon.textContent=result?(result.success?'✓':'!'):'•';const body=document.createElement('div');const name=document.createElement('b');name.textContent=action.description||`${action.tool}.${action.action}`;body.append(name);if(result?.display){const detail=document.createElement('small');detail.textContent=result.display;body.append(detail)}li.className=result?(result.success?'done':'warning'):'pending';li.append(icon,body);list.append(li)});card.append(list)})}
function renderConfirmation(data){const c=data.confirmation;if(!c)return;const card=addCard('confirm-card');const kicker=document.createElement('span');kicker.className='card-kicker';kicker.textContent='Permission required';const title=document.createElement('strong');title.textContent=c.description||'Protected action';const detail=document.createElement('p');detail.textContent=c.target?`${c.tool}.${c.action} · ${c.target}`:`${c.tool}.${c.action}`;const actions=document.createElement('div');actions.className='confirm-actions';const cancel=document.createElement('button');cancel.className='secondary';cancel.textContent='Cancel';const approve=document.createElement('button');approve.className='approve';approve.textContent='Allow once';actions.append(cancel,approve);card.append(kicker,title,detail,actions);cancel.addEventListener('click',()=>resolveConfirmation(c.token,false,card));approve.addEventListener('click',()=>resolveConfirmation(c.token,true,card))}
function renderReply(data){if(data.phases?.length)renderPhases(data.phases);if(data.response)addMessage(data.response,'assistant');if(data.kind==='confirmation_required')renderConfirmation(data);pollSystemState()}
async function submit(message){if(!ready||busy||!message.trim())return;busy=true;setCoreState('generating');addMessage(message.trim(),'user');input.value='';input.style.height='auto';updateSend();const loader=typing();try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:message.trim()})});const d=await r.json();loader.remove();if(r.ok)renderReply(d);else addMessage(d.error||'Something went wrong.','assistant')}catch{loader.remove();addMessage('I lost the connection to the local AURA service. Reopen the app if it was closed.','assistant')}finally{busy=false;setCoreState('idle');updateSend();input.focus()}}
async function resolveConfirmation(token,approved,card){if(busy)return;busy=true;card.querySelectorAll('button').forEach(b=>b.disabled=true);setCoreState('generating');try{const r=await fetch('/api/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token,approved})});const d=await r.json();card.classList.add(approved?'approved':'cancelled');if(r.ok)renderReply(d);else addMessage(d.error||'Confirmation failed.','assistant')}catch{addMessage('I could not reach the local AURA service to confirm that action.','assistant')}finally{busy=false;setCoreState('idle');updateSend();input.focus()}}

document.addEventListener('click',e=>{const next=e.target.closest('[data-next-step]');if(next){const target=next.dataset.nextStep;showStep(target);if(target==='hardware')loadSetup(true);return}const prompt=e.target.closest('[data-prompt]');if(prompt)submit(prompt.dataset.prompt)});
$('#privacyConsent').addEventListener('change',updateConsent);$('#permissionConsent').addEventListener('change',updateConsent);$('#prepareAura').addEventListener('click',completeSetup);$('#retrySetup').addEventListener('click',retryModel);$('#enterAura').addEventListener('click',()=>{setupFlowActive=false;enterApp()});
$('#composer').addEventListener('submit',e=>{e.preventDefault();submit(input.value)});input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,150)+'px';updateSend()});input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit(input.value)}});
$('#newChat').addEventListener('click',async()=>{if(busy)return;await fetch('/api/clear',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});conversation.replaceChildren();addMessage('Conversation cleared. What should we do next?','assistant');if(innerWidth<761)$('.sidebar').classList.remove('open')});$('#menuButton').addEventListener('click',()=>{const open=$('.sidebar').classList.toggle('open');$('#menuButton').setAttribute('aria-expanded',String(open))});poll();
