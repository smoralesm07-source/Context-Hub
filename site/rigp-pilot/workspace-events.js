const _taskItemEventsCore=taskItem;
taskItem=function(x){
  let html=_taskItemEventsCore(x);
  if(!html||!x.new_simulation_event_count)return html;
  return html.replace('</div>','<span class="chip red" style="margin-left:6px">'+esc(x.new_simulation_event_count)+' NUEVA INFO</span></div>');
};

const _appendCaseLogEventsCore=appendCaseLog;
appendCaseLog=function(el,type,key){
  _appendCaseLogEventsCore(el,type,key);
  appendDynamicEvents(el,type,key);
};

function appendDynamicEvents(el,type,key){
  const body=el?.querySelector('.dbody');if(!body)return;
  const block=document.createElement('div');block.className='block';block.style.marginTop='8px';
  block.innerHTML='<h4>Nueva información simulada</h4><div class="tiny muted">Los eventos alteran el workflow de revisión, pero no scoring, gate ni portafolio real.</div><div class="simEvents" style="margin-top:8px"><div class="tiny muted">Cargando…</div></div>';
  body.appendChild(block);
  loadDynamicEvents(block,type,key);
}

async function loadDynamicEvents(block,type,key){
  const out=block.querySelector('.simEvents');
  try{
    const d=await rpc('rigp_temp_ops_case_log',{p_token:token,p_object_type:type,p_object_key:key});
    const events=d.simulation_events||[];
    let html=events.length?events.slice().reverse().map(e=>'<div class="ev '+(e.status==='NEW'?'hold':'')+'"><div class="r"><h4>'+esc(label(e.event_type))+'</h4>'+chip(e.status,e.status==='NEW'?'red':'green')+'</div><p><b>'+esc(e.headline)+'</b><br>'+esc(e.detail||'')+'</p><div class="meta">'+dt(e.created_at)+(e.source_label?' · '+esc(e.source_label):'')+'</div>'+(e.status==='NEW'&&OPS_LENS.role!=='VIEWER'?'<textarea id="eventNote_'+esc(e.event_id)+'" class="ctrl" style="width:100%;min-height:46px;margin-top:6px" placeholder="Conclusión de revisión"></textarea><button class="btn primary" data-ack-event="'+esc(e.event_id)+'">Marcar revisado</button>':'')+'</div>').join(''):'<div class="notice">No hay eventos dinámicos inyectados para este expediente.</div>';
    if(OPS_LENS.role==='ADMIN'){
      html+='<div class="block" style="margin-top:8px"><h4>Inyectar cambio para ensayo</h4><select id="eventType" class="ctrl" style="width:100%;margin-bottom:5px"><option value="NEW_EVIDENCE">Nueva evidencia</option><option value="SOURCE_CHANGED">Cambio de fuente</option><option value="RELATIONSHIP_FOUND">Nueva relación</option><option value="PRICE_CONTEXT_UPDATED">Contexto de precio actualizado</option><option value="READJUDICATION_UPDATE">Actualización de readjudicación</option></select><input id="eventHeadline" class="ctrl" style="width:100%;margin-bottom:5px" placeholder="Titular del nuevo antecedente"><textarea id="eventDetail" class="ctrl" style="width:100%;min-height:52px;margin-bottom:5px" placeholder="Detalle simulado"></textarea><input id="eventSource" class="ctrl" style="width:100%;margin-bottom:5px" placeholder="Fuente simulada"><button class="btn" data-inject-event="1">Inyectar nueva información</button><div class="tiny muted" style="margin-top:5px">Esta acción no modifica scoring ni crea alerta productiva.</div></div>';
    }
    out.innerHTML=html;
    out.querySelectorAll('[data-ack-event]').forEach(b=>b.onclick=()=>ackDynamicEvent(Number(b.dataset.ackEvent),type,key,block));
    const inject=out.querySelector('[data-inject-event]');if(inject)inject.onclick=()=>injectDynamicEvent(type,key,block);
  }catch(e){out.innerHTML='<div class="error">'+esc(e.message)+'</div>'}
}

async function injectDynamicEvent(type,key,block){
  if(OPS_LENS.role!=='ADMIN'){alert('Solo el Administrador puede inyectar eventos de ensayo.');return;}
  const eventType=document.getElementById('eventType')?.value||'',headline=document.getElementById('eventHeadline')?.value||'',detailText=document.getElementById('eventDetail')?.value||'',source=document.getElementById('eventSource')?.value||'';
  if(headline.trim().length<3){alert('Indica un titular para el nuevo antecedente.');return;}
  try{
    await rpc('rigp_temp_ops_inject_event',{p_token:token,p_object_type:type,p_object_key:key,p_event_type:eventType,p_headline:headline,p_detail:detailText,p_source_label:source});
    await refreshDynamicEventState(type,key);loadDynamicEvents(block,type,key);
  }catch(e){alert(e.message)}
}

async function ackDynamicEvent(id,type,key,block){
  if(OPS_LENS.role==='VIEWER'){alert('Viewer es solo lectura.');return;}
  const note=document.getElementById('eventNote_'+id)?.value||'';
  try{
    await rpc('rigp_temp_ops_ack_event_as',{p_token:token,p_actor_name:OPS_LENS.name,p_event_id:id,p_note:note});
    await refreshDynamicEventState(type,key);loadDynamicEvents(block,type,key);
  }catch(e){alert(e.message)}
}

async function refreshDynamicEventState(type,key){
  TASKS=await rpc('rigp_temp_ops_task_queue',{p_token:token});
  if(typeof loadOpsManagement==='function')await loadOpsManagement(false);
  if(typeof refreshOpsMetrics==='function')await refreshOpsMetrics(false);
  if(type==='SIMCASE'&&cache.simcase)cache.simcase[key]=await rpc('rigp_temp_ops_simcase',{p_token:token,p_sim_case_id:key});
}
