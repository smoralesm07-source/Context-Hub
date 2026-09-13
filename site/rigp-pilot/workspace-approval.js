const _drawSimCaseApprovalCore=drawSimCase;
drawSimCase=function(el,d){
  _drawSimCaseApprovalCore(el,d);
  const pending=(d?.escalations||[]).filter(x=>x.status==='PROPOSED');
  if(!pending.length)return;
  const body=el.querySelector('.dbody');if(!body)return;
  const box=document.createElement('div');box.className='block';box.style.marginTop='8px';
  box.innerHTML='<h4>Decisión administrativa simulada</h4>'+pending.map(x=>'<div class="ev hold"><h4>Escalamiento #'+esc(x.escalation_id)+'</h4><p>'+esc(x.rationale||'Sin fundamento escrito.')+'</p><div class="meta">Propuesto '+dt(x.created_at)+'</div><textarea class="ctrl" id="decisionNote_'+esc(x.escalation_id)+'" style="width:100%;min-height:54px;margin-top:7px" placeholder="Fundamento de la decisión"></textarea><div class="actions"><button class="btn primary" data-decision="APPROVE" data-escalation="'+esc(x.escalation_id)+'">Aprobar simulación</button><button class="btn danger" data-decision="REJECT" data-escalation="'+esc(x.escalation_id)+'">Rechazar</button></div></div>').join('')+'<div class="notice">La aprobación no libera el caso al núcleo. Solo completa el circuito de gobernanza del sandbox.</div>';
  body.appendChild(box);
  box.querySelectorAll('[data-decision]').forEach(b=>b.onclick=()=>decideEscalation(Number(b.dataset.escalation),b.dataset.decision));
};
async function decideEscalation(id,decision){
  const note=document.getElementById('decisionNote_'+id)?.value||'';
  try{
    await rpc('rigp_temp_ops_decide_escalation',{p_token:token,p_escalation_id:id,p_decision:decision,p_note:note});
    if(selected?.object_type==='SIMCASE')cache.simcase[selected.object_key]=await rpc('rigp_temp_ops_simcase',{p_token:token,p_sim_case_id:selected.object_key});
    TASKS=await rpc('rigp_temp_ops_task_queue',{p_token:token});
    render();
  }catch(e){alert(e.message)}
}