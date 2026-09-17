"""First customer surface: same-origin assets, no dependencies or persistent chat storage."""
HTML = """<!doctype html>
<html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Share4AI</title><link rel="stylesheet" href="/chat.css">
<body><main><header><h1>Share4AI</h1><button id="language" type="button">English</button></header>
<p id="intro"></p><p id="privacy"></p><p id="status" role="status" aria-live="polite"></p>
<section id="messages" aria-label="المحادثة / Conversation"></section>
<form id="form"><label id="label" for="prompt"></label><textarea id="prompt" rows="3" maxlength="6000" required></textarea>
<div class="actions"><button id="send" type="submit"></button><button id="stop" type="button" disabled></button>
<button id="clear" type="button"></button></div></form></main><script src="/chat.js" defer></script></body></html>"""
CSS = """
:root{color-scheme:dark;font-family:Segoe UI,Tahoma,sans-serif;background:#111318;color:#eee}
*{box-sizing:border-box}body{margin:0}main{max-width:820px;margin:auto;padding:24px}
header,.actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap}header{justify-content:space-between}
h1{font-size:26px}p{line-height:1.8}#privacy{color:#aeb6c5;font-size:14px}
#status{padding:12px;background:#252c3a;border-radius:10px}
#messages{min-height:25vh}.message{white-space:pre-wrap;overflow-wrap:anywhere;background:#202633;padding:18px;margin:12px 0;border-radius:12px;line-height:1.8}
.message.user{background:#17374a}textarea{width:100%;resize:vertical;margin:10px 0;background:#202633;color:#fff;border:1px solid #768197;border-radius:10px;padding:14px;font:inherit}
button{font:inherit;padding:10px 20px;border-radius:9px;border:1px solid #768197;background:#263348;color:white;cursor:pointer}
button:disabled{opacity:.45;cursor:default}#send{background:#b8e3fb;color:#10202b}
:focus-visible{outline:3px solid #79c9ff;outline-offset:3px}
"""
JS = r"""
'use strict';
const $ = id => document.getElementById(id);
const text = {
 ar: {intro:'اسأل، وستصلك الإجابة من جهاز المزود.',privacy:'تجربة على هذا الجهاز. تمر الرسالة عبر خدمة المشاركة إلى النموذج. لا تُحفظ المحادثة بعد إغلاق الصفحة.',
 ready:'جاهز للمحادثة',waiting:'بانتظار جاهزية المزود. شغّل الذكاء المحلي واختبر الأداء ثم ابدأ التجربة.',
 connecting:'جارٍ الاتصال…',writing:'جارٍ كتابة الإجابة…',done:'اكتملت الإجابة',stopped:'توقف الطلب؛ الإجابة غير مكتملة.',
 failed:'تعذر إكمال الطلب. تحقق من جاهزية المزود ثم أعد المحاولة.',offline:'تعذر الاتصال. أعد فتح التجربة من التطبيق.',
 expired:'انتهت جلسة الوصول. افتح تجربة المحادثة من التطبيق مرة أخرى.',limit:'المحادثة طويلة. ابدأ محادثة جديدة.',
 label:'رسالتك',send:'إرسال',stop:'إيقاف',clear:'محادثة جديدة'},
 en: {intro:'Ask a question and receive an answer from the provider.',privacy:'Trial on this computer. Messages pass through the sharing service to the model. Chat is not saved after closing this page.',
 ready:'Ready to chat',waiting:'Waiting for the provider. Start Local AI, pass the performance test, then start the trial.',
 connecting:'Connecting…',writing:'Writing the answer…',done:'Answer complete',stopped:'Request stopped; the answer is incomplete.',
 failed:'Could not finish. Check provider readiness and retry.',offline:'Cannot connect. Reopen the trial from the app.',
 expired:'Access session ended. Reopen the chat trial from the app.',limit:'Conversation is too long. Start a new chat.',
 label:'Your message',send:'Send',stop:'Stop',clear:'New chat'}
};
let language='ar', state='connecting', pending=null, conversation=[], ready=false;
const token = new URLSearchParams(location.hash.slice(1)).get('access') || '';
history.replaceState(null,'',location.pathname);
function render(){
 document.documentElement.lang=language; document.documentElement.dir=language==='ar'?'rtl':'ltr';
 for(const id of ['intro','privacy','label','send','stop','clear']) $(id).textContent=text[language][id];
 $('language').textContent=language==='ar'?'English':'العربية';
 $('status').textContent=text[language][state];
 $('send').disabled=!!pending || !ready; $('stop').disabled=!pending;
 $('clear').disabled=!!pending; $('prompt').disabled=!!pending;
}
function setState(value){state=value;render();}
function bubble(content, role){
 const el=document.createElement('div');el.className='message '+role;el.dir='auto';el.textContent=content;
 $('messages').append(el);return el;
}
async function availability(){
 if(pending)return;
 if(!token){ready=false;setState('expired');return;}
 try{
  const response=await fetch('/v1/client/status',{headers:{Authorization:'Bearer '+token},cache:'no-store'});
  if(!response.ok){ready=false;setState(response.status===401?'expired':'offline');return;}
  const value=await response.json();ready=value.ready===true;
  if(!['done','stopped','failed','limit'].includes(state))state=ready?'ready':'waiting';
  render();
 }catch{ready=false;setState('offline');}
}
$('language').onclick=()=>{language=language==='ar'?'en':'ar';render();};
$('clear').onclick=()=>{conversation=[];$('messages').replaceChildren();setState(ready?'ready':'waiting');};
$('stop').onclick=()=>pending?.abort();
$('form').onsubmit=async event=>{
 event.preventDefault();if(pending||!ready)return;
 const prompt=$('prompt').value.trim();if(!prompt)return;
 const messages=[...conversation,{role:'user',content:prompt}];
 if(messages.length>39||messages.reduce((n,m)=>n+m.content.length,0)>12000){setState('limit');return;}
 pending=new AbortController();setState('connecting');bubble(prompt,'user');const answer=bubble('','assistant');
 let complete=false, buffer='', generated='';
 try{
  const response=await fetch('/v1/chat/stream',{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},
   body:JSON.stringify({messages,max_tokens:512}),signal:pending.signal});
  if(!response.ok)throw new Error('request');
  setState('writing');const reader=response.body.getReader(), decoder=new TextDecoder();
  while(true){
   const chunk=await reader.read();if(chunk.done)break;
   buffer+=decoder.decode(chunk.value,{stream:true});
   let boundary;
   while((boundary=buffer.indexOf('\n\n'))>=0){
    const frame=buffer.slice(0,boundary);buffer=buffer.slice(boundary+2);
    for(const line of frame.split('\n')){
     if(!line.startsWith('data: '))continue;
     const item=JSON.parse(line.slice(6));
     if(item.kind==='error')throw new Error('provider');
     if(item.kind==='token'){generated+=item.text;answer.textContent=generated;}
     if(item.kind==='done')complete=true;
    }
   }
  }
  if(!complete)throw new Error('incomplete');
  conversation=[...messages,{role:'assistant',content:generated}];$('prompt').value='';setState('done');
 }catch(error){pending.abort();setState(error.name==='AbortError'?'stopped':'failed');}
 finally{pending=null;render();availability();$('prompt').focus();}
};
window.addEventListener('pagehide',()=>pending?.abort());
render();availability();setInterval(availability,3000);
"""
ASSETS = {
    '/': ('text/html; charset=utf-8', HTML),
    '/chat.css': ('text/css; charset=utf-8', CSS),
    '/chat.js': ('text/javascript; charset=utf-8', JS),
}

