import React, {useEffect, useRef, useState} from 'react'
import {createRoot} from 'react-dom/client'
import {Bot, FileText, Send, Sparkles, Upload, X, Database, Network} from 'lucide-react'
import './styles.css'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
type Doc={id:string,filename:string,chunks:number,category:string}
type Citation={number:number,filename:string,page?:number,excerpt:string,score:number}
type Message={role:'user'|'assistant',content:string,agent?:string,citations?:Citation[]}

function App(){
 const [docs,setDocs]=useState<Doc[]>([]),[selected,setSelected]=useState<string[]>([]),[messages,setMessages]=useState<Message[]>([{role:'assistant',content:'Upload documents or ask about the demo corpus. I’ll route your question to the right specialist and cite the evidence I use.',agent:'coordinator'}]),[question,setQuestion]=useState(''),[busy,setBusy]=useState(false),[uploading,setUploading]=useState(false)
 const fileRef=useRef<HTMLInputElement>(null)
 const load=()=>fetch(`${API}/api/documents`).then(r=>r.json()).then(setDocs).catch(()=>{})
 useEffect(()=>{void load()},[])
 async function upload(files:FileList|null){if(!files)return;setUploading(true);for(const file of Array.from(files)){const form=new FormData();form.append('file',file);form.append('category','general');await fetch(`${API}/api/documents`,{method:'POST',body:form})}await load();setUploading(false)}
 async function remove(id:string){await fetch(`${API}/api/documents/${id}`,{method:'DELETE'});setSelected(s=>s.filter(x=>x!==id));load()}
 async function ask(e:React.FormEvent){e.preventDefault();if(!question.trim()||busy)return;const q=question;const next=[...messages,{role:'user' as const,content:q}];setMessages(next);setQuestion('');setBusy(true);try{const r=await fetch(`${API}/api/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,document_ids:selected,history:messages.map(({role,content})=>({role,content}))})});if(!r.ok)throw new Error();const d=await r.json();setMessages([...next,{role:'assistant',content:d.answer,agent:d.agent,citations:d.citations}])}catch{setMessages([...next,{role:'assistant',content:'The API is unavailable. Start the backend and try again.'}])}finally{setBusy(false)}}
 return <main>
  <aside><div className="brand"><div className="mark"><Network size={20}/></div><div><strong>Atlas RAG</strong><small>Agent workspace</small></div></div>
   <section className="upload" onClick={()=>fileRef.current?.click()}><Upload size={22}/><b>{uploading?'Indexing…':'Add knowledge'}</b><span>PDF, DOCX, TXT or MD</span><input ref={fileRef} hidden type="file" multiple accept=".pdf,.docx,.txt,.md" onChange={e=>upload(e.target.files)}/></section>
   <div className="sidehead"><span>Knowledge base</span><em>{docs.length}</em></div><div className="docs">{docs.map(d=><article className={selected.includes(d.id)?'chosen':''} onClick={()=>setSelected(s=>s.includes(d.id)?s.filter(x=>x!==d.id):[...s,d.id])} key={d.id}><FileText size={18}/><div><b>{d.filename}</b><span>{d.chunks} chunks · {d.category}</span></div><button aria-label="Delete" onClick={e=>{e.stopPropagation();remove(d.id)}}><X size={15}/></button></article>)}</div>
   <div className="status"><Database size={15}/><span>Vector index connected</span></div>
  </aside>
  <section className="workspace"><header><div><h1>Document intelligence</h1><p>{selected.length?`${selected.length} document${selected.length>1?'s':''} selected`:'Searching all documents'}</p></div><span className="live"><i/>Multi-agent online</span></header>
   <div className="chat">{messages.map((m,i)=><div key={i} className={`message ${m.role}`}><div className="avatar">{m.role==='assistant'?<Bot size={18}/>: 'II'}</div><div className="bubble">{m.agent&&<label><Sparkles size={13}/>{m.agent} agent</label>}<p>{m.content}</p>{m.citations&&m.citations.length>0&&<div className="sources"><b>Sources</b>{m.citations.slice(0,3).map(c=><details key={c.number}><summary>[{c.number}] {c.filename}{c.page?` · page ${c.page}`:''}<span>{Math.round(c.score*100)}% match</span></summary><p>{c.excerpt}</p></details>)}</div>}</div></div>)}{busy&&<div className="thinking"><i/><i/><i/> Routing and retrieving</div>}</div>
   <form onSubmit={ask}><textarea value={question} onChange={e=>setQuestion(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();ask(e)}}} placeholder="Ask a question about your documents…"/><button disabled={busy||!question.trim()} aria-label="Send"><Send size={19}/></button><span>Enter to send · Shift + Enter for new line</span></form>
  </section>
 </main>
}
createRoot(document.getElementById('root')!).render(<App/>)
