(function(){
 const _shellAuditNav=shell;
 shell=function(body){
   _shellAuditNav(body);
   const h=document.querySelector('.brand h1');if(h)h.textContent='RIGP · Auditoría Inteligente de Compras Públicas';
   const p=document.querySelector('.brand p');if(p)p.textContent='Hipótesis · hechos críticos · líneas de tiempo · evidencia fundante';
   document.querySelectorAll('.nav').forEach(b=>{const t=(b.querySelector('span')?.textContent||'').trim();if(t==='Hallazgos')b.querySelector('span').textContent='Auditoría de procesos';if(t==='Casos')b.querySelector('span').textContent='Expedientes';if(t==='Fuentes')b.querySelector('span').textContent='Fuentes y cobertura';if(t==='Trazabilidad')b.querySelector('span').textContent='Trazabilidad técnica'});
   document.querySelectorAll('.group').forEach(g=>{if(g.textContent.trim()==='Auditoría')g.textContent='Control técnico'});
 }
 const _renderHomeAuditNav=typeof renderHomeFocus==='function'?renderHomeFocus:null;
 if(_renderHomeAuditNav)renderHomeFocus=function(){_renderHomeAuditNav();const h=document.querySelector('.head h2');if(h)h.textContent='Centro de auditoría';const sub=document.querySelector('.head p');if(sub)sub.textContent='Dónde existen procesos que ameritan revisión, qué hipótesis están abiertas y qué falta acreditar.';const hero=document.querySelector('.focus-hero h2');if(hero)hero.textContent='¿Qué procesos requieren auditoría y por qué?';const hp=document.querySelector('.focus-hero p');if(hp)hp.textContent='RIGP ordena hechos críticos, contrapesos y brechas documentales para que el analista pueda auditar la lógica de una licitación antes de formular cualquier hipótesis penal.'}
})();
