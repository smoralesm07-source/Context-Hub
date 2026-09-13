var OPS_WORKLOAD=null,OPS_ESCALATIONS=null;
const _taskItemOpsCore=taskItem;
taskItem=function(x){
  const slaClass=x.sla_state==='OVERDUE'?'red':x.sla_state==='DUE_SOON'?'amber':'green';
  const due=x.due_at?(' · vence '+dt(x.due_at)):'';
  return '<div class="item" data-task="'+esc(x.task_id)+'"><div class="r"><div>'+chip(x.object_type,x.object_type==='INTAKE'?'blue':x.object_type==='ATTENTION'?'amber':x.object_type==='SIMCASE'?'green':'violet')+' '+workflow(x.workflow_state)+' '+chip(x.sla_state||'ON_TRACK',slaClass)+'</div><span class="tiny muted">P'+esc(x.priority_score)+'</span></div><h4>'+esc(x.title)+'</h4><p>'+esc(label(x.system_state))+' · '+(x.assignee_name?'Responsable: '+esc(x.assignee_name):'Sin asignar')+due+'</p></div>';
};

function workloadPanel(){
  const s=OPS_WORKLOAD?.sla||{},w=OPS_WORKLOAD?.workload||[],pending=OPS_ESCALATIONS?.pending||[];
  return '<div class="grid2" style="margin-top:11px"><div class="card"><div class="title"><h3>Gestión de carga y SLA</h3><span>gestión, no riesgo</span></div><div class="pad"><div class="metrics">'
    +metric(s.overdue||0,'Vencidas','requieren gestión')+metric(s.due_soon||0,'Próximas a vencer','ventana operativa')+metric(s.on_track||0,'En plazo','flujo normal')+'</div>'
    +'<div class="notice" style="margin-top:8px">'+esc(s.guardrail||'SLA operacional; no representa riesgo ni sospecha')+'</div>'
    +(w.length?'<div style="margin-top:8px">'+w.map(x=>'<div class="component"><div><div class="name">'+esc(x.assignee_name)+'</div><div class="sub">'+esc(x.assignee_role)+' · '+esc(x.task_count)+' tareas · edad media '+esc(x.avg_age_hours)+' h</div></div><span class="small">'+esc(x.overdue_count)+' vencidas</span></div>').join('')+'</div>':'')
    +'</div></div><div class="card"><div class="title"><h3>Bandeja de escalaciones</h3><span>'+pending.length+' pendientes</span></div><div class="pad rowlist">'
    +(pending.length?pending.map(e=>'<div class="item"><div class="r"><div>'+chip('PROPOSED','red')+'</div><span class="tiny muted">'+esc(e.pending_hours)+' h</span></div><h4>'+esc(e.title||e.object_key)+'</h4><p>'+esc(e.proposed_by_label||'Analista')+' · '+esc(e.rationale||'Sin fundamento')+'</p><button class="btn" data-open-escalation="'+esc(e.object_type)+':'+esc(e.object_key)+'">Abrir expediente</button></div>').join(''):'<div class="empty">No hay escalaciones pendientes.</div>')
    +'</div></div></div>';
}

const _renderCommandOpsCore=renderCommand;
renderCommand=function(){
  _renderCommandOpsCore();
  if(!OPS_WORKLOAD||!OPS_ESCALATIONS)return;
  const main=document.querySelector('.main');if(!main)return;
  const box=document.createElement('div');box.innerHTML=workloadPanel();
  while(box.firstChild)main.appendChild(box.firstChild);
  document.querySelectorAll('[data-open-escalation]').forEach(b=>b.onclick=()=>{
    const [type,key]=b.dataset.openEscalation.split(':');const task=TASKS.find(x=>x.object_type===type&&x.object_key===key);if(task)openTask(task.task_id);
  });
};

async function loadOpsManagement(redraw=true){
  try{
    [OPS_WORKLOAD,OPS_ESCALATIONS]=await Promise.all([rpc('rigp_temp_ops_workload',{p_token:token}),rpc('rigp_temp_ops_escalations',{p_token:token})]);
    if(redraw&&D&&view==='command')renderCommand();
  }catch(e){console.warn('RIGP ops management',e)}
}

function appendCaseLog(el,type,key){
  const body=el?.querySelector('.dbody');if(!body)return;
  const block=document.createElement('div');block.className='block';block.style.marginTop='8px';
  block.innerHTML='<h4>Bitácora operacional</h4><p>Acciones, asignaciones, solicitudes de evidencia y escalaciones del sandbox.</p><button class="btn" data-load-log="1">Ver bitácora completa</button><div class="opslog" style="margin-top:8px"></div>';
  body.appendChild(block);
  block.querySelector('[data-load-log]').onclick=async()=>{
    const out=block.querySelector('.opslog');out.innerHTML='<div class="tiny muted">Cargando…</div>';
    try{
      const d=await rpc('rigp_temp_ops_case_log',{p_token:token,p_object_type:type,p_object_key:key});
      const events=[];
      (d.assignments||[]).forEach(x=>events.push({at:x.assigned_at,label:'ASIGNACIÓN',text:(x.assignee_name||'Usuario')+' · '+(x.status||'')}));
      (d.actions||[]).forEach(x=>events.push({at:x.created_at,label:x.action_type,text:x.note||'Sin nota'}));
      (d.evidence_requests||[]).forEach(x=>events.push({at:x.created_at,label:'EVIDENCIA',text:x.request_text+' · '+x.status}));
      (d.escalations||[]).forEach(x=>events.push({at:x.created_at,label:'ESCALAMIENTO',text:(x.rationale||'Sin fundamento')+' · '+x.status}));
      events.sort((a,b)=>String(a.at).localeCompare(String(b.at)));
      out.innerHTML=events.length?events.map(x=>'<div class="ev"><h4>'+esc(label(x.label))+'</h4><p>'+esc(x.text)+'</p><div class="meta">'+dt(x.at)+'</div></div>').join(''):'<div class="empty">Sin actividad registrada.</div>';
    }catch(e){out.innerHTML='<div class="error">'+esc(e.message)+'</div>'}
  };
}

const _drawCaseOpsCore=drawCase;
drawCase=function(el,d,id){_drawCaseOpsCore(el,d,id);appendCaseLog(el,'CASE',id)};
const _drawIntakeOpsCore=drawIntake;
drawIntake=function(el,d){_drawIntakeOpsCore(el,d);const k=d?.intake?.logical_key;if(k)appendCaseLog(el,'INTAKE',k)};
const _drawAttentionOpsCore=drawAttention;
drawAttention=function(el,t){_drawAttentionOpsCore(el,t);appendCaseLog(el,'ATTENTION',t.object_key)};
const _drawSimCaseOpsCore=drawSimCase;
drawSimCase=function(el,d){_drawSimCaseOpsCore(el,d);const k=d?.case?.sim_case_id;if(k)appendCaseLog(el,'SIMCASE',k)};

const _refreshAllOpsCore=refreshAll;
refreshAll=async function(){await _refreshAllOpsCore();await loadOpsManagement(view==='command')};
const _saveActionOpsCore=saveAction;
saveAction=async function(type,key,action){await _saveActionOpsCore(type,key,action);await loadOpsManagement(false)};
const _assignTaskOpsCore=assignTask;
assignTask=async function(type,key){await _assignTaskOpsCore(type,key);await loadOpsManagement(false)};
const _decideEscalationOpsCore=decideEscalation;
decideEscalation=async function(id,decision){await _decideEscalationOpsCore(id,decision);await loadOpsManagement(false)};
loadOpsManagement(false);