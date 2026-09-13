cache.handoff=cache.handoff||{};
const _investigationBodyHandoffCore=investigationBody;
investigationBody=function(inv,id){
  let html=_investigationBodyHandoffCore(inv,id);
  const block='<div class="block" style="margin-top:8px"><div class="inv-section-title"><h4>Brief de traspaso</h4><span class="tiny muted">supervisión administrativa</span></div><div id="handoff_'+esc(id)+'"><div class="tiny muted">Carga bajo demanda para revisar síntesis, evidencia y brechas sin recorrer todo el expediente.</div><button class="btn" data-load-handoff="'+esc(id)+'" style="margin-top:6px">Generar brief</button></div></div>';
  const marker='<div class="block" style="margin-top:8px"><div class="inv-section-title"><h4>Workflow</h4>';
  if(html.includes(marker))html=html.replace(marker,block+marker);else html+=block;
  return html;
};
const _wireInvestigationHandoffCore=wireInvestigation;
wireInvestigation=function(id,el){
  _wireInvestigationHandoffCore(id,el);
  const b=el.querySelector('[data-load-handoff="'+CSS.escape(id)+'"]');if(b)b.onclick=()=>loadHandoffBrief(id,el);
};
function handoffCheckRow(x){return '<div class="component"><div><div class="name">'+esc(label(x.check))+'</div></div>'+chip(x.pass?'PASS':'PENDIENTE',x.pass?'green':'amber')+'</div>'}
function handoffReviewBlock(d){
  const r=d.latest_review;if(r)return '<div class="notice" style="margin-top:8px"><b>Última revisión supervisora: '+esc(label(r.decision))+'</b><br>'+esc(r.review_note||'Sin observación adicional.')+'<br><span class="tiny">'+esc(r.reviewer_label||'ADMIN')+' · '+dt(r.created_at)+'</span></div>';
  if(OPS_LENS.role!=='ADMIN'||!d.hypothesis)return '';
  return '<div class="block" style="margin-top:8px"><h4>Decisión de supervisión</h4><textarea id="handoffReviewNote" class="ctrl" style="width:100%;min-height:55px" placeholder="Observación de jefatura / instrucciones al analista"></textarea><div class="actions"><button class="btn primary" data-handoff-decision="ACCEPTED_SIMULATION" '+(d.handoff_ready?'':'disabled')+'>Aceptar traspaso</button><button class="btn" data-handoff-decision="RETURNED_FOR_ANALYSIS">Devolver para profundización</button><button class="btn" data-handoff-decision="HOLD_SUPERVISOR">Mantener en revisión</button></div><div class="inv-guard">Aceptar significa que el brief es suficiente para revisión supervisora dentro del ensayo. No aprueba el caso, no activa scoring y no libera a producción.</div></div>';
}
function renderHandoffBrief(d){
  const c=d.candidate||{},t=d.task||{},h=d.hypothesis,s=d.supporting_evidence||[],contra=d.contradicting_evidence||[],gaps=d.open_gaps||[],mech=d.mechanism||[],checks=d.handoff_checks||[];
  const hyp=h?'<div class="notice"><b>Hipótesis v'+esc(h.version_no)+' · '+esc(h.actor_label)+'</b><br>'+esc(h.thesis)+'<br><span class="tiny">'+esc(label(h.recommendation))+' · confianza '+esc(Math.round(Number(h.confidence||0)*100))+'%</span></div>':'<div class="notice">No existe todavía una hipótesis versionada. El brief no está listo para traspaso.</div>';
  const evidence=(arr,title)=>'<div><div class="tiny muted" style="margin-bottom:4px">'+title+' · '+arr.length+'</div>'+(arr.length?arr.map(x=>'<div class="ev"><h4>'+esc(x.signal_code||x.evidence_id)+'</h4><p>'+esc(x.summary||'')+'</p><div class="meta">'+esc(x.source_code||'')+'</div></div>').join(''):'<div class="empty">Sin evidencia seleccionada.</div>')+'</div>';
  const m=mech.map(x=>'<div class="component"><div><div class="name">'+esc(label(x.mechanism_stage))+'</div><div class="sub">'+esc(x.rationale||'')+'</div></div>'+chip(x.assessment_status||'NOT_ASSESSED',invStatusColor(x.assessment_status))+'</div>').join('');
  return '<div class="r" style="margin-bottom:7px"><div>'+chip(d.handoff_ready?'LISTO PARA TRASPASO':'NO LISTO',d.handoff_ready?'green':'amber')+'</div><div class="tiny muted">'+esc(c.tender_id||c.candidate_id||'')+'</div></div>'+hyp+
    '<div class="inv-grid" style="margin-top:8px">'+evidence(s,'Evidencia a favor')+evidence(contra,'Evidencia en contra')+'</div>'+
    '<div class="inv-grid" style="margin-top:8px"><div><div class="tiny muted" style="margin-bottom:4px">Brechas abiertas · '+gaps.length+'</div>'+(gaps.length?gaps.map(x=>'<div class="ev"><h4>'+esc(x.gap_code)+'</h4><p>'+esc(x.description||'')+'</p><div class="meta">'+esc(label(x.importance))+' · '+esc(x.required_source_code||'')+'</div></div>').join(''):'<div class="empty">Sin brechas abiertas.</div>')+'</div><div><div class="tiny muted" style="margin-bottom:4px">Checklist de traspaso</div>'+checks.map(handoffCheckRow).join('')+'</div></div>'+
    '<div style="margin-top:8px"><div class="tiny muted" style="margin-bottom:4px">Cadena de mecanismo</div>'+m+'</div>'+
    '<div class="notice" style="margin-top:8px"><b>Próxima acción de workflow:</b> '+esc(label(t.recommended_workflow_action||t.workflow_state||''))+'<br>'+esc(t.workflow_reason||'')+'</div>'+handoffReviewBlock(d)+
    '<div class="inv-guard">Este brief resume una simulación de revisión administrativa. No libera el caso a producción, no cambia scoring y no sustituye la revisión del expediente.</div>';
}
async function loadHandoffBrief(id,el){
  const out=el.querySelector('#handoff_'+CSS.escape(id));if(!out)return;out.innerHTML='<div class="tiny muted">Generando brief…</div>';
  try{const d=await rpc('rigp_temp_ops_handoff',{p_token:token,p_candidate_id:id});cache.handoff[id]=d;out.innerHTML=renderHandoffBrief(d);out.querySelectorAll('[data-handoff-decision]').forEach(b=>b.onclick=()=>decideHandoff(id,b.dataset.handoffDecision,el))}catch(e){out.innerHTML='<div class="error">'+esc(e.message)+'</div>'}
}
async function decideHandoff(id,decision,el){
  if(OPS_LENS.role!=='ADMIN'){alert('La revisión de traspaso corresponde al Administrador.');return;}
  const note=document.getElementById('handoffReviewNote')?.value||'';
  try{await rpc('rigp_temp_ops_decide_handoff_as',{p_token:token,p_actor_name:OPS_LENS.name,p_candidate_id:id,p_decision:decision,p_note:note});if(typeof loadLivePulse==='function')await loadLivePulse(false);await loadHandoffBrief(id,el)}catch(e){alert(e.message)}
}
