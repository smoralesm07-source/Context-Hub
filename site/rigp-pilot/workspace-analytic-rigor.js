const _investigationBodyRigorCore=investigationBody;
investigationBody=function(inv,id){
  let html=_investigationBodyRigorCore(inv,id);
  const d=inv?.case||{},c=d.candidate||{},mechanism=d.mechanism||[],facts=d.facts||[],evidence=d.evidence||[],award=d.award||{};
  const stageOrder=['AWARD','EXTRACTION','BENEFICIARY','CAPTURE','CONCEALMENT'];
  const stages=stageOrder.map(code=>mechanism.find(x=>x.mechanism_stage===code)||{mechanism_stage:code,assessment_status:'NOT_ASSESSED',strength:0,confidence:null,rationale:'Sin evaluación estructurada para esta etapa.'});
  const ladder='<div class="block" style="margin-top:8px"><div class="inv-section-title"><h4>Cadena de mecanismo</h4><span class="tiny muted">hipótesis, no imputación</span></div><div>'+stages.map(x=>'<div class="component"><div><div class="name">'+esc(label(x.mechanism_stage))+'</div><div class="sub">'+esc(x.rationale||'')+'</div></div><div style="text-align:right">'+chip(x.assessment_status||'NOT_ASSESSED',invStatusColor(x.assessment_status))+'<div class="tiny muted" style="margin-top:3px">fuerza '+esc(Math.round(Number(x.strength||0)*100))+'%</div></div></div>').join('')+'</div><div class="inv-guard">Una etapa fuerte no completa las demás. RIGP debe explicar mecanismo, beneficio y relación antes de escalar una anomalía.</div></div>';
  const controlFacts=facts.filter(x=>['FALSE_POSITIVE_CONTROL','GOVERNANCE','DOCUMENT_CONTROL'].includes(String(x.fact_family||'')));
  const removed=evidence.filter(x=>String(x.impact_on_case||'').includes('REMOVE')||String(x.validation_status||'').includes('NOT_SUPPORTED'));
  const suppress=(c.suppression_reasons||[]).map(x=>({title:'Señal suprimida',text:label(x),source:'RIGP'}));
  const controls=[...controlFacts.map(x=>({title:x.fact_code,text:x.interpretation||x.value_text||'',source:x.source_code})),...removed.map(x=>({title:x.signal_code||x.evidence_id,text:x.validation_summary||x.summary||'',source:x.primary_source_code||x.source_code})),...suppress].slice(0,8);
  const counter='<div class="block" style="margin-top:8px"><div class="inv-section-title"><h4>Contrapesos y control de falso positivo</h4><span>'+esc(controls.length)+'</span></div>'+(controls.length?controls.map(x=>'<div class="ev"><h4>'+esc(label(x.title))+'</h4><p>'+esc(x.text)+'</p><div class="meta">'+esc(x.source||'')+'</div></div>').join(''):'<div class="notice">No hay contrapesos estructurados adicionales. La ausencia de contrapesos no equivale a confirmación de la hipótesis.</div>')+(award.analyst_question?'<div class="inv-question"><b>Pregunta crítica de adjudicación</b><br>'+esc(award.analyst_question)+'</div>':'')+'<div class="inv-guard">Las declaraciones, criterios no-precio, trayectoria del proveedor o señales removidas deben usarse activamente para intentar refutar la hipótesis.</div></div>';
  const pivot='<div class="inv-three"';
  if(html.includes(pivot))html=html.replace(pivot,ladder+counter+pivot);
  else html=ladder+counter+html;
  return html;
};
