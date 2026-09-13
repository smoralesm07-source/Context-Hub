cache.investigation=cache.investigation||{};
(function(){
  if(!document.getElementById('rigp-investigation-style')){
    const s=document.createElement('style');s.id='rigp-investigation-style';s.textContent=`
      .investigation-detail{min-width:0}.inv-hero{display:grid;grid-template-columns:1.5fr .9fr;gap:8px}.inv-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.inv-three{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.inv-stat{background:#0a141e;border:1px solid #26394a;border-radius:8px;padding:9px}.inv-stat .n{font-size:19px;font-weight:700}.inv-stat .k{font-size:10px;color:#91a7b8;margin-top:2px}.inv-question{border-left:3px solid #547da0;padding:7px 9px;background:#0a141e;margin:5px 0;border-radius:0 7px 7px 0}.inv-evidence{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:6px;align-items:start;padding:7px 0;border-bottom:1px solid #203242}.inv-evidence:last-child{border-bottom:0}.inv-evidence label{font-size:10px;display:flex;gap:3px;align-items:center;white-space:nowrap}.inv-timeline{position:relative;padding-left:13px}.inv-timeline:before{content:'';position:absolute;left:3px;top:4px;bottom:4px;width:1px;background:#33485b}.inv-time{position:relative;padding:0 0 9px 8px}.inv-time:before{content:'';position:absolute;left:-13px;top:5px;width:7px;height:7px;border-radius:50%;background:#678eaa}.inv-time b{font-size:11px}.inv-time p{font-size:10px;margin:2px 0;color:#a8bac7}.hyp-form textarea,.hyp-form select,.hyp-form input{width:100%}.hyp-history{max-height:220px;overflow:auto}.hyp-ver{padding:7px 0;border-bottom:1px solid #203242}.hyp-ver:last-child{border-bottom:0}.inv-guard{font-size:9px;color:#839aaa;margin-top:5px}.inv-mini-node{display:inline-block;padding:4px 6px;border:1px solid #33485b;border-radius:999px;margin:2px;font-size:9px}.inv-muted{color:#8da3b4}.inv-section-title{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:7px}.inv-section-title h4{margin:0}.inv-change{border:1px solid #704248;background:#21161a;border-radius:8px;padding:9px}.inv-change.clean{border-color:#294338;background:#101c18}
      @media(min-width:1180px){.split:has(.investigation-detail){grid-template-columns:minmax(280px,.72fr) minmax(650px,1.75fr)}}
      @media(max-width:900px){.inv-hero,.inv-grid,.inv-three{grid-template-columns:1fr}}
    `;document.head.appendChild(s);
  }
})();

const _loadCaseInvestigationCore=loadCase;
loadCase=async function(id){
  await _loadCaseInvestigationCore(id);
  cache.investigation[id]=await rpc('rigp_temp_ops_investigation',{p_token:token,p_candidate_id:id});
};

function invStatusColor(v){return /HIGH|CRITICAL|OVERDUE|PROPOSED/i.test(String(v||''))?'red':/PARTIAL|WAIT|DUE_SOON|REVIEW/i.test(String(v||''))?'amber':/SUPPORTED|COMPLETE|ON_TRACK|VERIFIED/i.test(String(v||''))?'green':'blue'}
function invEvidenceStatus(e){return e.validation_status||e.impact_on_case||'SIN_VALIDAR'}
function invCanSaveHypothesis(task){if(OPS_LENS.role==='VIEWER')return false;if(OPS_LENS.role==='ADMIN')return true;return OPS_LENS.role==='ANALYST'&&task?.assignee_name===OPS_LENS.name&&task?.workflow_state!=='CLOSED_SIMULATION'}
function invLatestEvents(replay,n=6){return (replay?.events||[]).slice().sort((a,b)=>String(b.event_date).localeCompare(String(a.event_date))).slice(0,n)}

function investigationBody(inv,id){
  const d=inv?.case||{},c=d.candidate||{},task=TASKS.find(x=>x.object_type==='CASE'&&x.object_key===id)||inv?.task||{};
  const ev=d.evidence||[],components=d.decision_components||[],rels=d.relationships||[],graph=inv?.graph||{},replay=inv?.replay||{},latest=inv?.hypothesis_latest,hist=inv?.hypothesis_history||[];
  const supported=ev.filter(x=>x.validation_status==='SUPPORTED').length,partial=ev.filter(x=>String(x.validation_status||'').includes('PARTIAL')).length,usable=components.filter(x=>x.usable).length,persons=(graph.nodes||[]).filter(x=>x.type==='PERSON'),signals=(graph.nodes||[]).filter(x=>x.type==='SIGNAL');
  const newInfo=Number(task.new_simulation_event_count||0)>0;
  const changeBox=newInfo?'<div class="inv-change"><div class="r"><b>Nueva información pendiente</b>'+chip(task.latest_new_event_type||'NUEVO','red')+'</div><p>'+esc(task.latest_new_event_headline||'Existe un antecedente nuevo que requiere revisión.')+'</p><div class="tiny muted">'+dt(task.latest_new_event_at)+'</div></div>':'<div class="inv-change clean"><b>Sin nueva información pendiente</b><p class="tiny muted">El expediente está sincronizado con el estado conocido del sandbox.</p></div>';
  const questions=(inv?.investigation_questions||[]).map(q=>'<div class="inv-question">'+esc(q)+'</div>').join('');
  const compHtml=components.map(x=>'<div class="component"><div><div class="name">'+esc(x.component_name||x.component_code)+'</div><div class="sub">'+esc(label(x.evidence_mode||''))+'</div></div>'+chip(x.usable?'USABLE':'PENDIENTE',x.usable?'green':'amber')+'</div>').join('')||'<div class="empty">Sin componentes.</div>';
  const relHtml=rels.length?rels.slice(0,6).map(x=>'<div class="component"><div><div class="name">'+esc(x.person_name||x.person_rut||'Persona')+'</div><div class="sub">'+esc(label(x.relationship_type))+(x.ownership_pct!=null?' · '+esc(x.ownership_pct)+'%':'')+'</div></div>'+chip(x.verification_status||'UNVERIFIED',invStatusColor(x.verification_status))+'</div>').join(''):'<div class="notice">No hay relaciones personales graph-ready para este caso.</div>';
  const graphHtml='<div><span class="inv-mini-node">Comprador · '+esc(c.buyer_rut||'—')+'</span><span class="inv-mini-node">Proveedor · '+esc(c.supplier_rut||'—')+'</span>'+signals.map(x=>'<span class="inv-mini-node">'+esc(x.label)+'</span>').join('')+persons.map(x=>'<span class="inv-mini-node">'+esc(x.label)+'</span>').join('')+'</div><div class="inv-guard">'+esc((graph.nodes||[]).length)+' nodos · '+esc((graph.edges||[]).length)+' aristas. Solo relaciones verificadas pueden promoverse como identidad.</div>';
  const replayHtml='<div class="inv-timeline">'+invLatestEvents(replay).map(x=>'<div class="inv-time"><b>'+esc(date(x.event_date))+' · '+esc(label(x.event_type))+'</b><p>'+esc(x.title||x.summary||'Evento')+'</p><span class="tiny muted">'+esc(x.source_code||'')+'</span></div>').join('')+'</div>';
  const latestHtml=latest?'<div class="notice"><b>Hipótesis v'+esc(latest.version_no)+' · '+esc(latest.actor_label)+'</b><br>'+esc(latest.thesis)+'<br><span class="tiny">'+esc(label(latest.recommendation))+' · confianza '+esc(Math.round(Number(latest.confidence||0)*100))+'% · '+dt(latest.created_at)+'</span></div>':'<div class="notice">Aún no existe una hipótesis estructurada para esta ronda.</div>';
  const latestSupport=new Set(latest?.supporting_evidence_ids||[]),latestContra=new Set(latest?.contradicting_evidence_ids||[]);
  const evSelect=ev.map(e=>'<div class="inv-evidence"><div><b>'+esc(e.signal_code||e.evidence_id)+'</b><div class="tiny muted">'+esc(e.summary||'')+'</div><div class="tiny">'+chip(invEvidenceStatus(e),invStatusColor(invEvidenceStatus(e)))+' '+esc(e.evidence_id)+'</div></div><label><input type="checkbox" data-hyp-support="'+esc(e.evidence_id)+'" '+(latestSupport.has(e.evidence_id)?'checked':'')+'> A favor</label><label><input type="checkbox" data-hyp-contra="'+esc(e.evidence_id)+'" '+(latestContra.has(e.evidence_id)?'checked':'')+'> En contra</label></div>').join('')||'<div class="empty">Sin evidencias seleccionables.</div>';
  const canSave=invCanSaveHypothesis(task),why=!canSave?(OPS_LENS.role==='VIEWER'?'Viewer solo lectura.':'El analista debe tomar este caso antes de versionar una hipótesis.'):'La recomendación documenta criterio; no ejecuta acciones de workflow.';
  const hypForm='<div class="hyp-form"><textarea id="hypThesis" class="ctrl" style="min-height:84px" placeholder="Hipótesis de trabajo: qué mecanismo podría explicar los hechos y qué evidencia la sostiene">'+esc(latest?.thesis||'')+'</textarea><div class="inv-grid" style="margin-top:6px"><div><div class="tiny muted">Recomendación operacional</div><select id="hypRecommendation" class="ctrl"><option value="CONTINUE_REVIEW">Continuar revisión</option><option value="REQUEST_MORE_EVIDENCE">Solicitar más evidencia</option><option value="WATCH">Mantener en observación</option><option value="PROPOSE_ESCALATION">Proponer escalamiento</option><option value="CLOSE_SIMULATION">Proponer cierre simulado</option></select></div><div><div class="tiny muted">Confianza · <span id="hypConfidenceLabel">'+esc(Math.round(Number(latest?.confidence??0.5)*100))+'%</span></div><input id="hypConfidence" type="range" min="0" max="100" value="'+esc(Math.round(Number(latest?.confidence??0.5)*100))+'"></div></div><textarea id="hypUncertainties" class="ctrl" style="min-height:58px;margin-top:6px" placeholder="Incertidumbres y hechos que podrían refutar la hipótesis">'+esc(latest?.uncertainties||'')+'</textarea><div style="margin-top:7px"><div class="tiny muted">Evidencia vinculada a esta versión</div>'+evSelect+'</div><button class="btn primary" id="saveHypothesis" style="margin-top:8px" '+(canSave?'':'disabled')+'>Guardar nueva versión de hipótesis</button><div class="inv-guard">'+esc(why)+'</div></div>';
  const histHtml=hist.length?'<div class="hyp-history">'+hist.map(h=>'<div class="hyp-ver"><div class="r"><b>v'+esc(h.version_no)+' · '+esc(h.actor_label)+'</b>'+chip(h.recommendation,invStatusColor(h.recommendation))+'</div><p>'+esc(h.thesis)+'</p><div class="tiny muted">Confianza '+esc(Math.round(Number(h.confidence||0)*100))+'% · '+dt(h.created_at)+'</div></div>').join('')+'</div>':'<div class="empty">Sin versiones anteriores.</div>';
  return changeBox+
    '<div class="block" style="margin-top:8px"><div class="inv-section-title"><h4>Preguntas que debe resolver el analista</h4><span class="tiny muted">no son conclusiones</span></div>'+questions+'</div>'+
    '<div class="inv-three" style="margin-top:8px"><div class="inv-stat"><div class="n">'+esc(supported)+'/'+esc(ev.length)+'</div><div class="k">Evidencias soportadas</div></div><div class="inv-stat"><div class="n">'+esc(usable)+'/'+esc(components.length)+'</div><div class="k">Componentes de decisión utilizables</div></div><div class="inv-stat"><div class="n">'+esc(persons.length)+'</div><div class="k">Personas verificadas en grafo</div></div></div>'+
    '<div class="inv-grid" style="margin-top:8px"><div class="block"><div class="inv-section-title"><h4>Explicación de la decisión</h4><span>'+esc(c.coverage_pct??'—')+'%</span></div>'+compHtml+'</div><div class="block"><div class="inv-section-title"><h4>Relaciones verificadas</h4><span>'+esc(rels.length)+'</span></div>'+relHtml+'</div></div>'+
    '<div class="inv-grid" style="margin-top:8px"><div class="block"><div class="inv-section-title"><h4>Grafo relacional</h4><span>'+esc((graph.nodes||[]).length)+' nodos</span></div>'+graphHtml+'</div><div class="block"><div class="inv-section-title"><h4>Replay temporal</h4><span>'+esc(replay?.state?.event_count||0)+' eventos</span></div>'+replayHtml+'</div></div>'+
    '<div class="block" style="margin-top:8px"><div class="inv-section-title"><h4>Hipótesis de trabajo</h4><span>versionada · sandbox</span></div>'+latestHtml+'<div style="margin-top:8px">'+hypForm+'</div></div>'+
    '<div class="block" style="margin-top:8px"><div class="inv-section-title"><h4>Historial de hipótesis</h4><span>'+esc(hist.length)+' versiones</span></div>'+histHtml+'</div>'+
    '<div class="block" style="margin-top:8px"><div class="inv-section-title"><h4>Workflow</h4><span>'+esc(label(task.recommended_workflow_action||task.workflow_state||''))+'</span></div><div class="notice">'+esc(task.workflow_reason||'Gestiona el caso según la evidencia disponible.')+'</div>'+actionBox('CASE',id)+'</div>';
}

const _drawCaseInvestigationFallback=drawCase;
drawCase=function(el,d,id){
  const inv=cache.investigation?.[id];
  if(!inv)return _drawCaseInvestigationFallback(el,d,id);
  const c=inv.case?.candidate||d?.candidate||{},task=TASKS.find(x=>x.object_type==='CASE'&&x.object_key===id)||inv.task||{};
  el.classList.add('investigation-detail');
  el.innerHTML='<div class="dhead"><button class="close" id="xclose">×</button><div class="r"><div><div class="tiny mono muted">'+esc(c.tender_id||id)+'</div><h3>'+esc(c.title||'Expediente RIGP')+'</h3></div><div>'+workflow(task.workflow_state||'NEW')+' '+chip(task.sla_state||'ON_TRACK',invStatusColor(task.sla_state))+'</div></div><p>'+esc(c.hypothesis_summary||'')+'</p><div class="tiny muted">Responsable: '+esc(task.assignee_name||'Sin asignar')+' · Gate analítico: '+esc(c.validated_case_gate_passed?'VALIDADO':'NO ACTIVO')+' · Cobertura documental: '+esc(c.coverage_pct??'—')+'%</div></div><div class="dbody">'+investigationBody(inv,id)+'</div>';
  wireDrawer();
  wireInvestigation(id,el);
  if(typeof appendCaseLog==='function')appendCaseLog(el,'CASE',id);
};

function wireInvestigation(id,el){
  const conf=document.getElementById('hypConfidence'),lab=document.getElementById('hypConfidenceLabel');if(conf&&lab)conf.oninput=()=>lab.textContent=conf.value+'%';
  const latest=cache.investigation?.[id]?.hypothesis_latest;if(latest){const sel=document.getElementById('hypRecommendation');if(sel)sel.value=latest.recommendation||'CONTINUE_REVIEW'}
  document.querySelectorAll('[data-hyp-support]').forEach(x=>x.onchange=()=>{if(x.checked){const y=document.querySelector('[data-hyp-contra="'+CSS.escape(x.dataset.hypSupport)+'"]');if(y)y.checked=false}});
  document.querySelectorAll('[data-hyp-contra]').forEach(x=>x.onchange=()=>{if(x.checked){const y=document.querySelector('[data-hyp-support="'+CSS.escape(x.dataset.hypContra)+'"]');if(y)y.checked=false}});
  const save=document.getElementById('saveHypothesis');if(save)save.onclick=()=>saveInvestigationHypothesis(id,el);
}

async function saveInvestigationHypothesis(id,el){
  if(OPS_LENS.role==='VIEWER'){alert('Viewer es solo lectura.');return;}
  const thesis=document.getElementById('hypThesis')?.value||'',uncertainties=document.getElementById('hypUncertainties')?.value||'',recommendation=document.getElementById('hypRecommendation')?.value||'CONTINUE_REVIEW',confidence=Number(document.getElementById('hypConfidence')?.value||50)/100;
  const supporting=[...document.querySelectorAll('[data-hyp-support]:checked')].map(x=>x.dataset.hypSupport),contradicting=[...document.querySelectorAll('[data-hyp-contra]:checked')].map(x=>x.dataset.hypContra);
  if(thesis.trim().length<10){alert('Describe una hipótesis de trabajo con al menos 10 caracteres.');return;}
  try{
    await rpc('rigp_temp_ops_save_hypothesis_as',{p_token:token,p_actor_name:OPS_LENS.name,p_candidate_id:id,p_thesis:thesis,p_supporting_evidence_ids:supporting,p_contradicting_evidence_ids:contradicting,p_uncertainties:uncertainties,p_recommendation:recommendation,p_confidence:confidence});
    cache.investigation[id]=await rpc('rigp_temp_ops_investigation',{p_token:token,p_candidate_id:id});
    if(typeof loadLivePulse==='function')await loadLivePulse(false);
    drawCase(el,cache.case[id],id);
  }catch(e){alert(e.message)}
}
