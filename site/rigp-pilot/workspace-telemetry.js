var OPS_METRICS=null;
const _renderCommandTelemetryCore=renderCommand;
renderCommand=function(){
  _renderCommandTelemetryCore();
  if(!OPS_METRICS?.summary)return;
  const s=OPS_METRICS.summary,actors=OPS_METRICS.actors||[],main=document.querySelector('.main');if(!main)return;
  const box=document.createElement('div');box.className='card';box.style.marginTop='11px';
  box.innerHTML='<div class="title"><h3>Telemetría del piloto operacional</h3><span>RIGP-OPS-SIM-001</span></div><div class="pad"><div class="metrics">'
    +metric(s.touched_task_count+'/'+s.total_task_count,'Tareas tocadas',String(s.task_touch_pct)+'% del universo')
    +metric(s.assigned_task_count,'Asignadas','responsable visible')
    +metric(s.in_review_count,'En revisión','tomadas por analista')
    +metric(s.waiting_evidence_count,'Esperando evidencia','solicitudes abiertas')
    +metric(s.simulated_case_count,'Casos simulados','creados desde intake')
    +metric(s.pending_escalation_count,'Escalamiento pendiente','requiere decisión admin')
    +'</div><div class="two" style="margin-top:9px"><div class="block"><h4>Velocidad del ensayo</h4><p>Mediana hasta primera acción desde entrada al ensayo: <b>'+(s.median_minutes_to_first_action==null?'sin datos aún':fmtN(s.median_minutes_to_first_action)+' min')+'</b><br>Antigüedad mediana de la señal al actuar: <b>'+(s.median_source_age_hours_at_first_action==null?'sin datos aún':fmtN(s.median_source_age_hours_at_first_action)+' h')+'</b><br>Acciones registradas: '+esc(s.action_count)+'<br>Solicitudes satisfechas: '+esc(s.satisfied_evidence_request_count||0)+' · tareas cerradas: '+esc(s.closed_task_count||0)+'</p><div class="notice">El reloj de respuesta comienza cuando la tarea entra al ensayo; la antigüedad de la señal se informa por separado.</div></div><div class="block"><h4>Actividad por usuario</h4>'+(actors.length?actors.map(a=>'<div class="component"><div><div class="name">'+esc(a.actor_label)+'</div><div class="sub">'+esc(a.pilot_role||'')+' · '+esc(a.touched_task_count)+' tareas</div></div><span class="small">'+esc(a.action_count)+' acciones</span></div>').join(''):'<p>La sesión todavía no registra actividad humana.</p>')+'</div></div></div>';
  main.appendChild(box);
};
async function refreshOpsMetrics(redraw=true){
  try{OPS_METRICS=await rpc('rigp_temp_ops_metrics',{p_token:token});if(redraw&&D&&view==='command')renderCommand()}catch(e){console.warn('RIGP telemetry',e)}
}
const _refreshAllTelemetryCore=refreshAll;
refreshAll=async function(){await _refreshAllTelemetryCore();await refreshOpsMetrics(view==='command')};
const _saveActionTelemetryCore=saveAction;
saveAction=async function(type,key,action){await _saveActionTelemetryCore(type,key,action);await refreshOpsMetrics(false)};
const _assignTaskTelemetryCore=assignTask;
assignTask=async function(type,key){await _assignTaskTelemetryCore(type,key);await refreshOpsMetrics(false)};
const _decideEscalationTelemetryCore=decideEscalation;
decideEscalation=async function(id,decision){await _decideEscalationTelemetryCore(id,decision);await refreshOpsMetrics(false)};
refreshOpsMetrics(false);