const _investigationBodySupervisionCore=investigationBody;
investigationBody=function(inv,id){
  let html=_investigationBodySupervisionCore(inv,id),task=TASKS.find(x=>x.object_type==='CASE'&&x.object_key===id)||inv?.task||{};
  if(task.requires_supervisor_rework){
    const note='<div class="inv-change" style="margin-bottom:8px"><div class="r"><b>Devuelto por supervisión</b>'+chip('REVISAR HIPÓTESIS','red')+'</div><p>'+esc(task.supervisor_review_note||'La jefatura solicitó profundizar el análisis antes de un nuevo traspaso.')+'</p><div class="tiny muted">'+esc(task.supervisor_reviewer_label||'ADMIN')+' · '+dt(task.supervisor_reviewed_at)+'</div><div class="inv-guard">La devolución no modifica scoring. Crea una obligación de workflow: revisar evidencia y guardar una nueva versión de hipótesis.</div></div>';
    html=note+html;
  }
  return html;
};
