var OPS_READINESS=null,OPS_REHEARSALS=[];
const _renderCommandRehearsalCore=renderCommand;
renderCommand=function(){
  _renderCommandRehearsalCore();
  if(!OPS_READINESS)return;
  const main=document.querySelector('.main');if(!main)return;
  const s=OPS_READINESS.summary||{},fails=(OPS_READINESS.checks||[]).filter(x=>x.status!=='PASS');
  const box=document.createElement('div');box.className='card';box.style.marginTop='11px';
  box.innerHTML='<div class="title"><h3>Control del ensayo operacional</h3><span>'+esc(s.readiness_state||'')+'</span></div><div class="pad"><div class="metrics">'
    +metric((s.pass_count||0)+'/'+(s.check_count||0),'Controles PASS',String(s.readiness_pct||0)+'% readiness')
    +metric(fails.length,'Controles pendientes',fails.length?'revisar antes del ensayo':'sin bloqueos')
    +metric(OPS_REHEARSALS.length,'Ensayos archivados','historial preservado')
    +'</div><div class="two" style="margin-top:9px"><div class="block"><h4>Readiness</h4>'+(fails.length?fails.map(x=>'<div class="ev hold"><h4>'+esc(x.check_name)+'</h4><p>'+esc(x.status)+'</p></div>').join(''):'<div class="notice">Todos los controles técnicos están en PASS. Esto habilita ensayo operacional, no producción.</div>')+'</div><div class="block"><h4>Cerrar y archivar ensayo</h4><p>Antes de limpiar el sandbox se guarda un snapshot con métricas, acciones, asignaciones, casos simulados, evidencia y escalaciones.</p><input id="rehearsalLabel" class="ctrl" style="width:100%;margin-bottom:6px" placeholder="Etiqueta del ensayo (ej. Equipo A · ronda 1)"><input id="resetPhrase" class="ctrl" style="width:100%;margin-bottom:6px" placeholder="Escribe REINICIAR RIGP"><button class="btn danger" id="resetRehearsal">Archivar y reiniciar sandbox</button></div></div>'+(OPS_REHEARSALS.length?'<div class="block" style="margin-top:8px"><h4>Historial reciente</h4>'+OPS_REHEARSALS.slice(0,5).map(x=>'<div class="component"><div><div class="name">'+esc(x.label||('Ensayo #'+x.snapshot_id))+'</div><div class="sub">'+dt(x.captured_at)+' · '+esc(x.metrics?.action_count||0)+' acciones · '+esc(x.metrics?.touched_task_count||0)+' tareas tocadas</div></div><span class="tiny muted">#'+esc(x.snapshot_id)+'</span></div>').join('')+'</div>':'')+'</div>';
  main.appendChild(box);
  const b=document.getElementById('resetRehearsal');if(b)b.onclick=resetRehearsal;
};

async function loadRehearsalControl(redraw=true){
  try{
    [OPS_READINESS,OPS_REHEARSALS]=await Promise.all([rpc('rigp_temp_ops_readiness',{p_token:token}),rpc('rigp_temp_ops_rehearsal_history',{p_token:token})]);
    if(redraw&&D&&view==='command')renderCommand();
  }catch(e){console.warn('RIGP rehearsal control',e)}
}

async function resetRehearsal(){
  const phrase=document.getElementById('resetPhrase')?.value||'',labelText=document.getElementById('rehearsalLabel')?.value||'';
  if(phrase!=='REINICIAR RIGP'){alert('Para evitar reinicios accidentales, escribe exactamente REINICIAR RIGP.');return;}
  if(!confirm('Se archivará el ensayo actual y se limpiará únicamente el sandbox operacional. El núcleo RIGP no se modifica. ¿Continuar?'))return;
  try{
    await rpc('rigp_temp_ops_reset_rehearsal',{p_token:token,p_confirmation:phrase,p_label:labelText});
    cache.case={};cache.intake={};cache.graph={};cache.replay={};if(cache.simcase)cache.simcase={};
    await refreshAll();
    await loadRehearsalControl(false);
    render();
  }catch(e){alert(e.message)}
}

const _refreshAllRehearsalCore=refreshAll;
refreshAll=async function(){await _refreshAllRehearsalCore();await loadRehearsalControl(view==='command')};
loadRehearsalControl(false);