var OPS_DRILL=null;
const _renderCommandDrillCore=renderCommand;
renderCommand=function(){
  _renderCommandDrillCore();
  if(!OPS_DRILL)return;
  const main=document.querySelector('.main');if(!main)return;
  const active=OPS_DRILL.active_run,packs=OPS_DRILL.packs||[],history=OPS_DRILL.history||[];
  const box=document.createElement('div');box.className='card';box.style.marginTop='11px';
  let body='<div class="title"><h3>Rondas guiadas de ensayo</h3><span>información sintética · scoring intacto</span></div><div class="pad">';
  if(active){
    const n=active.next_step;
    body+='<div class="notice"><b>'+esc(active.name)+'</b><br>Paso '+esc(active.current_step)+' de '+esc(active.step_count)+' completado.</div>';
    if(n){
      body+='<div class="block" style="margin-top:8px"><h4>Próximo estímulo</h4><p>'+esc(n.headline)+'<br><span class="tiny muted">'+esc(label(n.event_type))+' · '+esc(n.learning_focus||'')+'</span></p>'+(OPS_LENS.role==='ADMIN'?'<button class="btn primary" id="launchDrillStep">Lanzar paso '+esc(n.step_order)+'</button>':'<div class="tiny muted">Solo el Administrador puede lanzar el siguiente paso.</div>')+'</div>';
    }
  }else{
    body+='<div class="notice">No hay una ronda activa. Las rondas inyectan cambios sintéticos, nunca hechos nuevos ni señales productivas.</div>';
    if(OPS_LENS.role==='ADMIN'&&packs.length){
      body+='<div class="block" style="margin-top:8px"><h4>Iniciar ronda</h4><select id="drillPack" class="ctrl" style="width:100%;margin-bottom:6px">'+packs.map(p=>'<option value="'+esc(p.pack_code)+'">'+esc(p.name)+' · '+esc(p.step_count)+' pasos</option>').join('')+'</select><button class="btn" id="startDrill">Iniciar ensayo guiado</button></div>';
    }
  }
  if(history.length){body+='<div class="block" style="margin-top:8px"><h4>Historial de rondas</h4>'+history.slice(0,5).map(r=>'<div class="component"><div><div class="name">'+esc(r.pack_code)+'</div><div class="sub">'+esc(label(r.status))+' · '+esc(r.current_step)+' pasos · '+dt(r.started_at)+'</div></div><span class="tiny muted">#'+esc(r.run_id)+'</span></div>').join('')+'</div>'}
  body+='<div class="tiny muted" style="margin-top:8px">Cada estímulo está marcado como SIMULADO y `does_not_change_scoring=true`.</div></div>';
  box.innerHTML=body;main.appendChild(box);
  const start=document.getElementById('startDrill');if(start)start.onclick=startGuidedDrill;
  const next=document.getElementById('launchDrillStep');if(next)next.onclick=launchNextDrillStep;
};

async function loadDrillState(redraw=true){
  try{OPS_DRILL=await rpc('rigp_temp_ops_drill_state',{p_token:token});if(redraw&&D&&view==='command')renderCommand()}catch(e){console.warn('RIGP drill',e)}
}
async function startGuidedDrill(){
  if(OPS_LENS.role!=='ADMIN'){alert('Solo el Administrador puede iniciar una ronda guiada.');return;}
  const pack=document.getElementById('drillPack')?.value;if(!pack)return;
  try{await rpc('rigp_temp_ops_start_drill',{p_token:token,p_pack_code:pack});await loadDrillState(false);render()}catch(e){alert(e.message)}
}
async function launchNextDrillStep(){
  if(OPS_LENS.role!=='ADMIN'){alert('Solo el Administrador puede lanzar estímulos.');return;}
  try{
    const result=await rpc('rigp_temp_ops_launch_next_drill_step',{p_token:token});
    TASKS=await rpc('rigp_temp_ops_task_queue',{p_token:token});
    if(typeof loadOpsManagement==='function')await loadOpsManagement(false);
    if(typeof refreshOpsMetrics==='function')await refreshOpsMetrics(false);
    await loadDrillState(false);
    render();
    const target=TASKS.find(x=>x.object_type===result.target?.object_type&&x.object_key===result.target?.object_key);
    if(target&&confirm('Paso lanzado: '+result.headline+'\n\n¿Abrir ahora el expediente afectado?'))openTask(target.task_id);
  }catch(e){alert(e.message)}
}
const _refreshAllDrillCore=refreshAll;
refreshAll=async function(){await _refreshAllDrillCore();await loadDrillState(view==='command')};
loadDrillState(false);