cache.simcase={};
const _openTaskCore=openTask;
openTask=async function(taskId){
  const t=TASKS.find(x=>x.task_id===taskId);if(!t)return;
  if(t.object_type!=='SIMCASE')return _openTaskCore(taskId);
  selected=t;view='queue';detail=null;
  if(!cache.simcase[t.object_key])cache.simcase[t.object_key]=await rpc('rigp_temp_ops_simcase',{p_token:token,p_sim_case_id:t.object_key});
  render();
};
const _renderDrawerCore=renderDrawer;
renderDrawer=function(){
  const el=document.getElementById('drawer');if(!el||!selected)return;
  if(selected.object_type==='SIMCASE')return drawSimCase(el,cache.simcase[selected.object_key]);
  return _renderDrawerCore();
};
function drawSimCase(el,d){
  if(!d)return;const c=d.case||{},src=d.source_intake||{},req=d.evidence_requests||[],escs=d.escalations||[],acts=d.actions||[];
  el.innerHTML='<div class="dhead"><button class="close" id="xclose">×</button><div class="tiny mono muted">'+esc(c.sim_case_id)+'</div><h3>'+esc(c.title)+'</h3><p>'+esc(c.hypothesis_summary||'Hipótesis simulada en construcción.')+'</p></div><div class="dbody">'
    +'<div class="kv"><div><div class="k">Proceso</div><div class="v">'+esc(c.tender_id||'—')+'</div></div><div><div class="k">Estado</div><div class="v">'+esc(label(c.state))+'</div></div><div><div class="k">Prioridad inicial</div><div class="v">'+esc(c.initial_priority??'—')+'</div></div><div><div class="k">Proveedor</div><div class="v">'+esc(c.supplier_rut||'—')+'</div></div></div>'
    +'<div class="block" style="margin-top:8px"><h4>Origen del caso</h4><p>'+esc(c.buyer_name||c.buyer_rut||'Comprador')+' → '+esc(c.supplier_rut||'Proveedor')+'<br>Familias: '+esc((c.families||[]).join(', ')||'—')+'<br>Señales: '+esc((c.signal_codes||[]).join(', ')||'—')+'</p><div class="notice" style="margin-top:7px">Origen: '+esc(src.logical_key||c.source_logical_key)+' · '+esc(label(src.review_lane||''))+'</div></div>'
    +'<div class="block" style="margin-top:8px"><h4>Solicitudes de evidencia</h4>'+(req.length?req.map(x=>'<div class="ev"><h4>'+esc(label(x.status))+'</h4><p>'+esc(x.request_text)+'</p><div class="meta">'+dt(x.created_at)+' · '+esc(x.requested_by_label||'TEMP_ADMIN')+'</div></div>').join(''):'<p>Sin solicitudes aún.</p>')+'</div>'
    +'<div class="block" style="margin-top:8px"><h4>Escalamiento simulado</h4>'+(escs.length?escs.map(x=>'<div class="ev '+(x.status==='PROPOSED'?'hold':'')+'"><h4>'+esc(label(x.status))+'</h4><p>'+esc(x.rationale||'Sin fundamento escrito.')+'</p><div class="meta">'+dt(x.created_at)+' · '+esc(x.proposed_by_label||'TEMP_ADMIN')+'</div></div>').join(''):'<p>No se ha propuesto escalamiento.</p>')+'</div>'
    +'<div class="block" style="margin-top:8px"><h4>Bitácora del caso</h4>'+(acts.length?acts.map(x=>'<div class="component"><div><div class="name">'+esc(label(x.action_type))+'</div><div class="sub">'+esc(x.note||'Sin nota')+'</div></div><span class="tiny muted">'+dt(x.created_at)+'</span></div>').join(''):'<p>Sin acciones adicionales.</p>')+'</div>'
    +actionBox('SIMCASE',c.sim_case_id)+'</div>';
  wireDrawer();
}
const _saveActionCore=saveAction;
saveAction=async function(type,key,action){
  const note=document.getElementById('actionNote')?.value||'';
  try{
    const result=await rpc('rigp_temp_ops_save_action',{p_token:token,p_object_type:type,p_object_key:key,p_action_type:action,p_note:note});
    [TASKS,ACTIONS]=await Promise.all([rpc('rigp_temp_ops_task_queue',{p_token:token}),rpc('rigp_temp_ops_get_actions',{p_token:token})]);
    if(type==='SIMCASE')cache.simcase[key]=await rpc('rigp_temp_ops_simcase',{p_token:token,p_sim_case_id:key});
    if(type==='INTAKE'&&action==='PROPOSE'&&result?.effect?.sim_case_id){cache.simcase[result.effect.sim_case_id]=await rpc('rigp_temp_ops_simcase',{p_token:token,p_sim_case_id:result.effect.sim_case_id});selected=TASKS.find(x=>x.object_type==='SIMCASE'&&x.object_key===result.effect.sim_case_id)||selected;}
    render();
  }catch(e){alert(e.message)}
};