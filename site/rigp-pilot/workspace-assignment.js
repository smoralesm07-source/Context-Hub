const _taskItemCore=taskItem;
taskItem=function(x){
  return '<div class="item" data-task="'+esc(x.task_id)+'"><div class="r"><div>'+chip(x.object_type,x.object_type==='INTAKE'?'blue':x.object_type==='ATTENTION'?'amber':x.object_type==='SIMCASE'?'green':'violet')+' '+workflow(x.workflow_state)+'</div><span class="tiny muted">P'+esc(x.priority_score)+'</span></div><h4>'+esc(x.title)+'</h4><p>'+esc(label(x.system_state))+' · '+(x.assignee_name?'Responsable: '+esc(x.assignee_name):'Sin asignar')+'</p></div>';
};
const _actionBoxCore=actionBox;
actionBox=function(type,key){
  const members=(P?.participants||[]).filter(x=>x.active&&['ADMIN','ANALYST'].includes(x.participant_role));
  const opts=members.map(x=>'<option value="'+esc(x.display_name)+'">'+esc(x.display_name)+' · '+esc(x.participant_role)+'</option>').join('');
  const current=TASKS.find(x=>x.object_type===type&&x.object_key===key);
  return _actionBoxCore(type,key)+'<div class="block" style="margin-top:8px"><h4>Responsable</h4><p style="margin-bottom:7px">'+(current?.assignee_name?'Asignado a <b>'+esc(current.assignee_name)+'</b>.':'Tarea sin asignar.')+'</p><div style="display:flex;gap:6px"><select id="assignMember" class="ctrl" style="flex:1"><option value="">Seleccionar participante</option>'+opts+'</select><button class="btn" data-assign="1" data-type="'+esc(type)+'" data-key="'+esc(key)+'">Asignar</button></div></div>';
};
const _wireDrawerAssignCore=wireDrawer;
wireDrawer=function(){
  _wireDrawerAssignCore();
  document.querySelectorAll('[data-assign]').forEach(b=>b.onclick=()=>assignTask(b.dataset.type,b.dataset.key));
};
async function assignTask(type,key){
  const name=document.getElementById('assignMember')?.value;if(!name)return;
  try{
    await rpc('rigp_temp_ops_assign_task',{p_token:token,p_object_type:type,p_object_key:key,p_assignee_name:name});
    TASKS=await rpc('rigp_temp_ops_task_queue',{p_token:token});
    render();
  }catch(e){alert(e.message)}
}