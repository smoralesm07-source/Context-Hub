var OPS_LIVE=null,OPS_LIVE_TIMER=null;
const _renderCommandLiveCore=renderCommand;
renderCommand=function(){
  _renderCommandLiveCore();
  if(!OPS_LIVE)return;
  const main=document.querySelector('.main');if(!main)return;
  const items=OPS_LIVE.items||[],s=OPS_LIVE.summary||{};
  const box=document.createElement('div');box.className='card';box.style.marginTop='11px';
  box.innerHTML='<div class="title"><h3>Pulso en vivo</h3><span>refresco ~60 s</span></div><div class="pad"><div class="metrics">'
    +metric(s.new_sim_events||0,'Nueva información','simulada pendiente')+metric(s.open_evidence_requests||0,'Evidencia abierta','solicitudes')+metric(s.pending_escalations||0,'Escalaciones','decisión pendiente')+metric(s.pending_shadow_reviews||0,'Cambios shadow','revisión pendiente')
    +'</div><div class="rowlist" style="margin-top:9px">'+(items.length?items.slice(0,12).map(feedItem).join(''):'<div class="empty">Sin actividad reciente.</div>')+'</div><div class="tiny muted" style="margin-top:7px">No contiene escenarios ciegos ni respuestas esperadas. Los eventos de simulación nunca cambian scoring.</div></div>';
  main.appendChild(box);
  box.querySelectorAll('[data-live-task]').forEach(b=>b.onclick=()=>{const t=TASKS.find(x=>x.object_type===b.dataset.type&&x.object_key===b.dataset.key);if(t)openTask(t.task_id)});
};
function feedItem(x){
  const c=x.severity==='HIGH'?'red':x.severity==='MEDIUM'?'amber':'blue';
  const canOpen=TASKS.some(t=>t.object_type===x.object_type&&t.object_key===x.object_key);
  return '<div class="item"><div class="r"><div>'+chip(x.feed_type,c)+' '+chip(x.state||'',x.state==='NEW'||x.state==='PROPOSED'?'red':'')+'</div><span class="tiny muted">'+dt(x.occurred_at)+'</span></div><h4>'+esc(x.title)+'</h4><p>'+esc(x.detail||'')+(x.actor?' · '+esc(x.actor):'')+'</p>'+(canOpen?'<button class="btn" data-live-task="1" data-type="'+esc(x.object_type)+'" data-key="'+esc(x.object_key)+'">Abrir expediente</button>':'')+'</div>';
}
async function refreshLiveFeed(redraw=true){
  try{OPS_LIVE=await rpc('rigp_temp_ops_live_feed',{p_token:token,p_limit:30});if(redraw&&D&&view==='command')renderCommand()}catch(e){console.warn('RIGP live feed',e)}
}
const _refreshAllLiveCore=refreshAll;
refreshAll=async function(){await _refreshAllLiveCore();await refreshLiveFeed(view==='command')};
refreshLiveFeed(false);
if(!OPS_LIVE_TIMER)OPS_LIVE_TIMER=setInterval(()=>refreshLiveFeed(view==='command'),60000);