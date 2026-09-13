const _appendCaseLogLifecycleCore=appendCaseLog;
appendCaseLog=function(el,type,key){
  _appendCaseLogLifecycleCore(el,type,key);
  appendLifecycleControls(el,type,key);
};

function appendLifecycleControls(el,type,key){
  const body=el?.querySelector('.dbody');if(!body)return;
  const task=TASKS.find(x=>x.object_type===type&&x.object_key===key);
  const block=document.createElement('div');block.className='block';block.style.marginTop='8px';
  block.innerHTML='<h4>Ciclo de gestión</h4><div class="tiny muted">Simulación operacional; no modifica el núcleo analítico.</div><div class="lifecycleBody" style="margin-top:8px"><div class="tiny muted">Cargando estado…</div></div>';
  body.appendChild(block);
  loadLifecycle(block,type,key,task);
}

async function loadLifecycle(block,type,key,task){
  const out=block.querySelector('.lifecycleBody');
  try{
    const d=await rpc('rigp_temp_ops_case_log',{p_token:token,p_object_type:type,p_object_key:key});
    const req=(d.evidence_requests||[]),open=req.filter(x=>x.status==='OPEN');
    let html='';
    if(req.length){
      html+='<div class="small" style="margin-bottom:5px">Solicitudes de evidencia</div>'+req.map(x=>'<div class="ev '+(x.status==='OPEN'?'hold':'')+'"><h4>'+esc(label(x.status))+'</h4><p>'+esc(x.request_text)+'</p><div class="meta">'+dt(x.created_at)+'</div>'+(x.status==='OPEN'?'<textarea class="ctrl" id="resolveNote_'+esc(x.request_id)+'" style="width:100%;min-height:50px;margin-top:6px" placeholder="Qué evidencia llegó / resultado de revisión"></textarea><button class="btn primary" data-resolve-request="'+esc(x.request_id)+'">Marcar evidencia recibida</button>':'')+'</div>').join('');
    }else html+='<div class="notice">No hay solicitudes de evidencia abiertas.</div>';
    const current=TASKS.find(x=>x.object_type===type&&x.object_key===key)||task||{};
    if(current.workflow_state==='CLOSED_SIMULATION'){
      html+='<div style="margin-top:8px"><div class="notice">Tarea cerrada en simulación'+(current.closure_reason?': '+esc(current.closure_reason):'.')+'</div><textarea class="ctrl" id="reopenReason" style="width:100%;min-height:48px;margin-top:6px" placeholder="Motivo de reapertura"></textarea><button class="btn" data-reopen-task="1">Reabrir tarea</button></div>';
    }else{
      html+='<div style="margin-top:8px"><textarea class="ctrl" id="closeReason" style="width:100%;min-height:48px" placeholder="Motivo de cierre simulado"></textarea><button class="btn danger" data-close-task="1">Cerrar tarea</button></div>';
    }
    out.innerHTML=html;
    out.querySelectorAll('[data-resolve-request]').forEach(b=>b.onclick=()=>resolveEvidence(Number(b.dataset.resolveRequest),type,key,block));
    const c=out.querySelector('[data-close-task]');if(c)c.onclick=()=>closeOpsTask(type,key,block);
    const r=out.querySelector('[data-reopen-task]');if(r)r.onclick=()=>reopenOpsTask(type,key,block);
  }catch(e){out.innerHTML='<div class="error">'+esc(e.message)+'</div>'}
}

async function resolveEvidence(id,type,key,block){
  const note=document.getElementById('resolveNote_'+id)?.value||'';
  try{
    await rpc('rigp_temp_ops_resolve_evidence',{p_token:token,p_request_id:id,p_resolution_note:note});
    await refreshLifecycleData(type,key);
    loadLifecycle(block,type,key,TASKS.find(x=>x.object_type===type&&x.object_key===key));
  }catch(e){alert(e.message)}
}
async function closeOpsTask(type,key,block){
  const reason=document.getElementById('closeReason')?.value||'';if(reason.trim().length<3){alert('Indica un motivo de cierre.');return;}
  try{
    await rpc('rigp_temp_ops_close_task',{p_token:token,p_object_type:type,p_object_key:key,p_reason:reason});
    await refreshLifecycleData(type,key);render();
  }catch(e){alert(e.message)}
}
async function reopenOpsTask(type,key,block){
  const reason=document.getElementById('reopenReason')?.value||'';
  try{
    await rpc('rigp_temp_ops_reopen_task',{p_token:token,p_object_type:type,p_object_key:key,p_reason:reason});
    await refreshLifecycleData(type,key);render();
  }catch(e){alert(e.message)}
}
async function refreshLifecycleData(type,key){
  TASKS=await rpc('rigp_temp_ops_task_queue',{p_token:token});
  if(typeof loadOpsManagement==='function')await loadOpsManagement(false);
  if(typeof refreshOpsMetrics==='function')await refreshOpsMetrics(false);
  if(type==='SIMCASE'&&cache.simcase)cache.simcase[key]=await rpc('rigp_temp_ops_simcase',{p_token:token,p_sim_case_id:key});
}
