var OPS_LENS={name:'smorales316',role:'ADMIN'},OPS_LENS_MEMBERS=[];
function lensKey(){return 'rigp_ops_lens'}
function loadStoredLens(){try{return JSON.parse(sessionStorage.getItem(lensKey())||'null')}catch{return null}}
function saveLens(x){sessionStorage.setItem(lensKey(),JSON.stringify(x))}
function lensCanWrite(){return OPS_LENS.role!=='VIEWER'}

async function loadRoleLens(redraw=true){
  try{
    const members=await rpc('rigp_temp_ops_role_lens',{p_token:token});
    OPS_LENS_MEMBERS=[...(members||[]),{display_name:'Viewer simulado',role:'VIEWER',active:true}];
    const stored=loadStoredLens();
    if(stored&&OPS_LENS_MEMBERS.some(x=>x.display_name===stored.name&&x.role===stored.role))OPS_LENS=stored;
    else{
      const a=OPS_LENS_MEMBERS.find(x=>x.role==='ADMIN')||OPS_LENS_MEMBERS[0];
      if(a)OPS_LENS={name:a.display_name,role:a.role};saveLens(OPS_LENS);
    }
    if(redraw&&D)render();
  }catch(e){console.warn('RIGP role lens',e)}
}

const _shellLensCore=shell;
shell=function(body){
  _shellLensCore(body);
  const top=document.querySelector('.topmeta');if(!top)return;
  const wrap=document.createElement('span');wrap.className='badge';wrap.style.gap='6px';
  wrap.innerHTML='<span>Perspectiva</span><select id="roleLens" style="background:#0a141e;color:#ecf3f8;border:1px solid #33485b;border-radius:6px;padding:3px 5px">'+OPS_LENS_MEMBERS.map(x=>'<option value="'+esc(x.display_name)+'|'+esc(x.role)+'" '+(x.display_name===OPS_LENS.name&&x.role===OPS_LENS.role?'selected':'')+'>'+esc(x.display_name)+' · '+esc(x.role)+'</option>').join('')+'</select>';
  top.appendChild(wrap);
  const sel=document.getElementById('roleLens');if(sel)sel.onchange=()=>{const i=sel.value.lastIndexOf('|');OPS_LENS={name:sel.value.slice(0,i),role:sel.value.slice(i+1)};saveLens(OPS_LENS);selected=null;render()};
};

const _taskItemLensCore=taskItem;
taskItem=function(x){
  if(OPS_LENS.role==='ANALYST'&&x.assignee_name&&x.assignee_name!==OPS_LENS.name)return '';
  return _taskItemLensCore(x);
};

const _renderCommandLensCore=renderCommand;
renderCommand=function(){
  _renderCommandLensCore();
  const main=document.querySelector('.main');if(!main)return;
  const n=document.createElement('div');n.className='notice';n.style.marginTop='11px';
  n.innerHTML='<b>Perspectiva simulada: '+esc(OPS_LENS.name)+' · '+esc(OPS_LENS.role)+'</b><br>'+(OPS_LENS.role==='ANALYST'?'La mesa prioriza tareas libres y propias. Debe tomar una tarea antes de decidir sobre ella.':OPS_LENS.role==='VIEWER'?'Modo solo lectura: navegación sin acciones de workflow.':'Administrador: vista global, asignación y decisiones de escalamiento.')+'<br><span class="tiny">Esta perspectiva reproduce comportamiento de roles; la frontera de seguridad definitiva volverá con autenticación.</span>';
  main.insertBefore(n,main.firstChild);
  if(OPS_LENS.role!=='ADMIN'){
    const reset=document.getElementById('resetRehearsal');if(reset)reset.closest('.block').style.display='none';
  }
};

const _wireDrawerLensCore=wireDrawer;
wireDrawer=function(){
  _wireDrawerLensCore();
  setTimeout(applyLensRestrictions,0);
};
function applyLensRestrictions(){
  if(OPS_LENS.role==='ADMIN')return;
  document.querySelectorAll('[data-assign],[data-decision]').forEach(x=>{x.disabled=true;x.style.display='none'});
  if(OPS_LENS.role==='VIEWER'){
    document.querySelectorAll('[data-action],[data-resolve-request],[data-close-task],[data-reopen-task]').forEach(x=>{x.disabled=true;x.style.display='none'});
    document.querySelectorAll('#actionNote,#assignMember,#closeReason,#reopenReason,[id^="resolveNote_"]').forEach(x=>{x.disabled=true});
  }
}

const _saveActionLensAdmin=saveAction;
saveAction=async function(type,key,action){
  if(OPS_LENS.role==='VIEWER'){alert('Viewer es solo lectura.');return;}
  if(OPS_LENS.role==='ADMIN')return _saveActionLensAdmin(type,key,action);
  const note=document.getElementById('actionNote')?.value||'';
  try{
    const result=await rpc('rigp_temp_ops_save_action_as',{p_token:token,p_actor_name:OPS_LENS.name,p_object_type:type,p_object_key:key,p_action_type:action,p_note:note});
    [TASKS,ACTIONS]=await Promise.all([rpc('rigp_temp_ops_task_queue',{p_token:token}),rpc('rigp_temp_ops_get_actions',{p_token:token})]);
    if(type==='SIMCASE'&&cache.simcase)cache.simcase[key]=await rpc('rigp_temp_ops_simcase',{p_token:token,p_sim_case_id:key});
    if(type==='INTAKE'&&action==='PROPOSE'&&result?.effect?.sim_case_id){cache.simcase[result.effect.sim_case_id]=await rpc('rigp_temp_ops_simcase',{p_token:token,p_sim_case_id:result.effect.sim_case_id});selected=TASKS.find(x=>x.object_type==='SIMCASE'&&x.object_key===result.effect.sim_case_id)||selected;}
    if(typeof refreshOpsMetrics==='function')await refreshOpsMetrics(false);
    if(typeof loadOpsManagement==='function')await loadOpsManagement(false);
    render();
  }catch(e){alert(e.message)}
};

const _resolveEvidenceLensAdmin=resolveEvidence;
resolveEvidence=async function(id,type,key,block){
  if(OPS_LENS.role==='VIEWER'){alert('Viewer es solo lectura.');return;}
  if(OPS_LENS.role==='ADMIN')return _resolveEvidenceLensAdmin(id,type,key,block);
  const note=document.getElementById('resolveNote_'+id)?.value||'';
  try{
    await rpc('rigp_temp_ops_resolve_evidence_as',{p_token:token,p_actor_name:OPS_LENS.name,p_request_id:id,p_resolution_note:note});
    await refreshLifecycleData(type,key);loadLifecycle(block,type,key,TASKS.find(x=>x.object_type===type&&x.object_key===key));
  }catch(e){alert(e.message)}
};

const _closeOpsTaskLensAdmin=closeOpsTask;
closeOpsTask=async function(type,key,block){
  if(OPS_LENS.role==='VIEWER'){alert('Viewer es solo lectura.');return;}
  if(OPS_LENS.role==='ADMIN')return _closeOpsTaskLensAdmin(type,key,block);
  const reason=document.getElementById('closeReason')?.value||'';if(reason.trim().length<3){alert('Indica un motivo de cierre.');return;}
  try{
    await rpc('rigp_temp_ops_close_task_as',{p_token:token,p_actor_name:OPS_LENS.name,p_object_type:type,p_object_key:key,p_reason:reason});
    await refreshLifecycleData(type,key);render();
  }catch(e){alert(e.message)}
};

const _reopenOpsTaskLensAdmin=reopenOpsTask;
reopenOpsTask=async function(type,key,block){if(OPS_LENS.role!=='ADMIN'){alert('La reapertura queda reservada al Administrador en esta simulación.');return;}return _reopenOpsTaskLensAdmin(type,key,block)};
const _assignTaskLensAdmin=assignTask;
assignTask=async function(type,key){if(OPS_LENS.role!=='ADMIN'){alert('La reasignación queda reservada al Administrador.');return;}return _assignTaskLensAdmin(type,key)};
const _decideEscalationLensAdmin=decideEscalation;
decideEscalation=async function(id,decision){if(OPS_LENS.role!=='ADMIN'){alert('La decisión de escalamiento corresponde al Administrador.');return;}return _decideEscalationLensAdmin(id,decision)};
const _resetRehearsalLensAdmin=resetRehearsal;
resetRehearsal=async function(){if(OPS_LENS.role!=='ADMIN'){alert('Solo el Administrador puede archivar/reiniciar el ensayo.');return;}return _resetRehearsalLensAdmin()};

loadRoleLens(false);