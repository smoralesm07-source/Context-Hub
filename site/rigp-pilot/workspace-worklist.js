var OPS_QUEUE_MODE='AUTO';
function opsQueueCounts(){
  const mine=TASKS.filter(x=>x.assignee_name===OPS_LENS.name&&x.workflow_state!=='CLOSED_SIMULATION').length;
  const free=TASKS.filter(x=>!x.assignee_name&&x.workflow_state!=='CLOSED_SIMULATION').length;
  const fresh=TASKS.filter(x=>Number(x.new_simulation_event_count||0)>0&&x.workflow_state!=='CLOSED_SIMULATION').length;
  const evidence=TASKS.filter(x=>x.workflow_state==='WAITING_EVIDENCE').length;
  const due=TASKS.filter(x=>['DUE_SOON','OVERDUE'].includes(x.sla_state)&&x.workflow_state!=='CLOSED_SIMULATION').length;
  const returned=TASKS.filter(x=>x.requires_supervisor_rework===true&&x.workflow_state!=='CLOSED_SIMULATION').length;
  return {mine,free,fresh,evidence,due,returned};
}
function opsQueueAccept(x,mode){
  if(mode==='MINE')return x.assignee_name===OPS_LENS.name;
  if(mode==='FREE')return !x.assignee_name;
  if(mode==='NEW_INFO')return Number(x.new_simulation_event_count||0)>0;
  if(mode==='EVIDENCE')return x.workflow_state==='WAITING_EVIDENCE';
  if(mode==='DUE')return ['DUE_SOON','OVERDUE'].includes(x.sla_state);
  if(mode==='RETURNED')return x.requires_supervisor_rework===true;
  if(mode==='OPEN')return x.workflow_state!=='CLOSED_SIMULATION';
  return true;
}
function worklistToolbar(){
  const c=opsQueueCounts();
  const current=OPS_QUEUE_MODE==='AUTO'?(OPS_LENS.role==='ANALYST'?'OPEN':'ALL'):OPS_QUEUE_MODE;
  const buttons=[['ALL','Todas',TASKS.length],['MINE','Mías',c.mine],['FREE','Libres',c.free],['RETURNED','Devueltos',c.returned],['NEW_INFO','Nueva info',c.fresh],['EVIDENCE','Evidencia',c.evidence],['DUE','Por vencer',c.due]];
  return '<div class="card pad" style="margin-bottom:9px"><div class="r"><div><b>Mi bandeja operacional</b><div class="tiny muted">Perspectiva '+esc(OPS_LENS.name)+' · '+esc(OPS_LENS.role)+'</div></div><div style="display:flex;gap:5px;flex-wrap:wrap">'+buttons.map(b=>'<button class="btn '+(current===b[0]?'primary':'')+'" data-qmode="'+b[0]+'">'+b[1]+' · '+b[2]+'</button>').join('')+'</div></div></div>';
}
const _taskItemWorklistReworkCore=taskItem;
taskItem=function(x){
  let html=_taskItemWorklistReworkCore(x);if(!html||!x.requires_supervisor_rework)return html;
  return html.replace('</div>','<span class="chip red" style="margin-left:6px">DEVUELTO POR SUPERVISIÓN</span></div>');
};
const _renderQueueWorklistCore=renderQueue;
renderQueue=function(){
  _renderQueueWorklistCore();
  const main=document.querySelector('.main');if(!main)return;
  const head=main.querySelector('.head');if(!head)return;
  const wrap=document.createElement('div');wrap.innerHTML=worklistToolbar();head.insertAdjacentElement('afterend',wrap.firstChild);
  document.querySelectorAll('[data-qmode]').forEach(b=>b.onclick=()=>{OPS_QUEUE_MODE=b.dataset.qmode;renderQueue()});
  const current=OPS_QUEUE_MODE==='AUTO'?(OPS_LENS.role==='ANALYST'?'OPEN':'ALL'):OPS_QUEUE_MODE;
  const body=document.getElementById('qbody');if(!body)return;
  const search=document.getElementById('qq'),type=document.getElementById('qt'),state=document.getElementById('qs');
  const redraw=()=>{
    const q=(search?.value||'').toLowerCase(),t=type?.value||'',s=state?.value||'';
    let rows=TASKS.filter(x=>opsQueueAccept(x,current)&&(!t||x.object_type===t)&&(!s||x.workflow_state===s)&&(!q||JSON.stringify(x).toLowerCase().includes(q)));
    if(OPS_LENS.role==='ANALYST')rows=rows.filter(x=>!x.assignee_name||x.assignee_name===OPS_LENS.name);
    body.innerHTML='<div class="rowlist">'+(rows.map(taskItem).join('')||'<div class="empty">No hay tareas en esta bandeja.</div>')+'</div>';bind();
  };
  if(search)search.oninput=redraw;if(type)type.oninput=redraw;if(state)state.oninput=redraw;redraw();
  if(selected)renderDrawer();
};
const _renderCommandWorklistCore=renderCommand;
renderCommand=function(){
  _renderCommandWorklistCore();
  const c=opsQueueCounts(),main=document.querySelector('.main');if(!main)return;
  const box=document.createElement('div');box.className='card';box.style.marginTop='11px';
  box.innerHTML='<div class="title"><h3>Bandeja de la perspectiva actual</h3><span>'+esc(OPS_LENS.name)+'</span></div><div class="pad"><div class="metrics">'+metric(c.mine,'Mías','responsabilidad activa')+metric(c.free,'Libres','disponibles para tomar')+metric(c.returned,'Devueltos','requieren nueva versión')+metric(c.fresh,'Nueva info','requieren relectura')+metric(c.evidence,'Esperando evidencia','solicitudes abiertas')+metric(c.due,'Por vencer','SLA operacional')+'</div></div>';
  main.appendChild(box);
};
