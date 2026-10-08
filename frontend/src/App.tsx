import { useEffect, useRef, useState } from 'react';
import { api, ApiError } from './api';
import { attrKeys, labels, emptyDraft, draftSchema, type Draft, type Character, type Campaign, type Catalog, type Report, type Archetype } from './types';

const steps = ['Conceito','Raça','Atributos','Classe','Arquétipo','Perícias','Técnicas e arma','História e imagem','Conferência','Revisão'];
const marks = ['◇','✧','◉','✺'];

export default function App() {
  const [user,setUser] = useState<{id:number;name:string}|null>(null);
  const [sessionReady,setSessionReady] = useState(false);
  const [campaigns,setCampaigns] = useState<Campaign[]>([]);
  const [campaignId,setCampaignId] = useState<number|null>(null);
  const [catalog,setCatalog] = useState<Catalog|null>(null);
  const [characters,setCharacters] = useState<Character[]>([]);
  const [character,setCharacter] = useState<Character|null>(null);
  const [draft,setDraft] = useState<Draft>(emptyDraft);
  const [report,setReport] = useState<Report|null>(null);
  const [comparison,setComparison] = useState<{archetype:Archetype;report:Report}[]>([]);
  const [view,setView] = useState<'home'|'create'|'compare'>('home');
  const [step,setStep] = useState(0);
  const [error,setError] = useState('');
  const [notice,setNotice] = useState('');
  const [dirty,setDirty] = useState(false);
  const [conflict,setConflict] = useState(false);
  const [saving,setSaving] = useState(false);
  const [saveFailed,setSaveFailed] = useState(false);
  const [compareInputs,setCompareInputs] = useState({VIG:1,PRE:1});
  const [busy,setBusy] = useState(false);
  const [authMode,setAuthMode] = useState<'login'|'register'>('login');
  const [username,setUsername] = useState('');
  const [password,setPassword] = useState('');
  const [campaignName,setCampaignName] = useState('');
  const [invite,setInvite] = useState(new URLSearchParams(location.search).get('convite') ?? '');
  const [comment,setComment] = useState('');
  const [rule,setRule] = useState('R06');
  const [decisionText,setDecisionText] = useState('');
  const [reason,setReason] = useState('');
  const [spendAll,setSpendAll] = useState(true);
  const [mainExtra,setMainExtra] = useState(true);
  const [duplicates,setDuplicates] = useState('');
  const [rollResult,setRollResult] = useState('');
  const [resourceDraft,setResourceDraft] = useState({pv:'',pe:'',san:''});
  const savingRef = useRef(false);
  const edits = useRef(0);
  const campaign = campaigns.find(c => c.id === campaignId);
  const canEdit = character?.ownerId === user?.id;
  const activeReport = report ?? character?.report;

  function showError(e:unknown) {
    if (e instanceof Error && e.name === 'AbortError') return;
    setError(e instanceof Error ? e.message : 'Não foi possível concluir a operação.');
    if (e instanceof ApiError && e.status === 403) setNotice('Se sua sessão expirou, entre novamente. Sua edição permanece nesta tela.');
  }
  async function action(task:()=>Promise<void>) {
    setError(''); setNotice(''); setBusy(true);
    try { await task(); } catch(e) { showError(e); } finally {setBusy(false);}
  }
  async function refresh() {
    const [cs,chs] = await Promise.all([api<Campaign[]>('/campaigns'),api<Character[]>('/characters')]);
    setCampaigns(cs);setCharacters(chs);setCampaignId(current => current ?? cs[0]?.id ?? null);
  }
  useEffect(()=>{ api<{user:typeof user}>('/session').then(result=>setUser(result.user)).catch(showError).finally(()=>setSessionReady(true)); },[]);
  useEffect(()=>{if(user) void refresh().catch(showError);},[user]);
  useEffect(()=>{
    if(campaignId === null) {setCatalog(null);return;}
    setCatalog(null);
    const controller = new AbortController();
    api<Catalog>(`/campaigns/${campaignId}/rules`,'GET',undefined,controller.signal).then(setCatalog).catch(showError);
    return ()=>controller.abort();
  },[campaignId]);
  useEffect(()=>{
    if(campaignId === null || view === 'home') return;
    const controller = new AbortController();
    const timer = setTimeout(()=>{
      if(view === 'create') api<Report>('/characters/preview','POST',{campaignId,data:draft,characterId:character?.id},controller.signal).then(setReport).catch(showError);
      if(view === 'compare' || step === 4) api<typeof comparison>('/comparisons','POST',{campaignId,data:view==='compare'?{...emptyDraft(),attributes:{FOR:3,AGI:3,INT:1,...compareInputs}}:draft},controller.signal).then(setComparison).catch(showError);
    },200);
    return ()=>{clearTimeout(timer);controller.abort();};
  },[draft,campaignId,view,step,compareInputs,character?.id,character?.revision]);

  async function save():Promise<Character|null> {
    if(!character || !canEdit || conflict || savingRef.current) return null;
    if(!dirty) return character;
    const checked = draftSchema.safeParse(draft);
    if(!checked.success) {setError('Confira os atributos: valores inteiros de 0 a 3. Sua edição foi preservada.');return null;}
    const editAtStart = edits.current;
    savingRef.current = true;setSaving(true);setSaveFailed(false);setError('');
    try {
      const saved = await api<Character>(`/characters/${character.id}`,'PATCH',{revision:character.revision,data:checked.data});
      setCharacter(saved);setCharacters(old=>old.map(c=>c.id===saved.id?saved:c));
      if(edits.current === editAtStart) setDirty(false);
      return saved;
    } catch(e) {
      if(e instanceof ApiError && e.status === 409) setConflict(true);
      setSaveFailed(true);
      showError(e);return null;
    } finally {savingRef.current = false;setSaving(false);}
  }
  useEffect(()=>{
    if(!dirty || !canEdit || conflict || saving || saveFailed) return;
    const timer = setTimeout(()=>void save(),1000);
    return ()=>clearTimeout(timer);
  },[draft,dirty,character?.revision,canEdit,conflict,saving,saveFailed]);
  function change<K extends keyof Draft>(key:K,value:Draft[K]) {
    edits.current += 1;setDraft(old=>({...old,[key]:value}));setDirty(true);setReport(null);setSaveFailed(false);
  }
  function open(c:Character) {
    if(dirty && !confirm('Abrir outra ficha descartará a edição ainda não salva. Continuar?')) return;
    setCharacter(c);setDraft(c.data);setReport(c.report);setDirty(false);setConflict(false);setSaveFailed(false);setCampaignId(c.campaignId);setStep(0);setView('create');setError('');
    setResourceDraft({pv:String(c.resources.pv??''),pe:String(c.resources.pe??''),san:String(c.resources.san??'')});
  }
  async function create() {
    if(campaignId === null) return;
    const result = await api<Character>('/characters','POST',{campaignId,data:emptyDraft()});
    setCharacters(old=>[result,...old]);open(result);
  }
  async function send() {
    const editAtStart = edits.current;
    const current = dirty ? await save() : character;
    if(!current || savingRef.current) return;
    if(edits.current !== editAtStart) {setNotice('A ficha foi editada durante o salvamento. Aguarde salvar e envie novamente.');return;}
    const result = await api<Character>(`/characters/${current.id}/submissions`,'POST',{revision:current.revision});
    setCharacter(result);setCharacters(old=>old.map(c=>c.id===result.id?result:c));setNotice('Snapshot enviado ao mestre.');setStep(9);
  }
  async function review(id:number,status:string) {
    const result = await api<Character>(`/submissions/${id}/reviews`,'POST',{status,comment});
    setCharacter(result);setCharacters(old=>old.map(c=>c.id===result.id?result:c));setNotice(status==='approved'?'Revisão aprovada.':'Ajustes enviados.');
  }
  async function recordDecision() {
    if(!campaignId) return;
    const value = rule==='R09'?{spendAll,hybridLimit:decisionText}:rule==='R06'?{mainSkillExtra:mainExtra,duplicates,trainingGrades:decisionText}:rule==='R08'?{eligibility:decisionText}:rule==='ATIRADOR'?{allowRespiration:true}:{validated:true};
    await api(`/campaigns/${campaignId}/decisions`,'POST',{ruleId:rule,value,reason,characterId:character?.id});
    setNotice('Decisão registrada. Envie um novo snapshot para utilizar esta decisão.');setReason('');
    if(character) {const result = await api<Character>(`/characters/${character.id}`);setCharacter(result);setReport(result.report);}
  }
  const field = (key:'name'|'concept'|'race'|'skills'|'equipment'|'techniques'|'uniqueAbility'|'story',label:string,help?:string,multiline=false) =>
    <label className="field">{label}{multiline?<textarea value={draft[key]} onChange={e=>change(key,e.target.value)} disabled={!canEdit} rows={key==='story'?7:4}/>:<input value={draft[key]} maxLength={120} onChange={e=>change(key,e.target.value)} disabled={!canEdit}/>} {help&&<small>{help}</small>}</label>;
  const resources = (r:Report|undefined|null) => <div className="resources">{(['pv','pe','san'] as const).map(k=><div key={k}><span>{k==='san'?'Sanidade':k.toUpperCase()}</span><strong>{r?.maxima[k]??'—'}</strong><small>máximo inicial</small></div>)}</div>;

  return <>
    <header className="topbar"><a href="#" className="brand" onClick={e=>{e.preventDefault();setView('home');}}><span className="moon">◑</span><span>Ao Cair da Noite<small>CADERNO DE PERSONAGENS</small></span></a>{user&&<div className="account"><span>{user.name}</span><button className="text-button" onClick={()=>void action(async()=>{if(dirty&&!confirm('Há uma edição não salva. Sair agora?')) return;await api('/auth/logout','POST');setUser(null);setCharacters([]);setCampaigns([]);setCharacter(null);setCampaignId(null);setDirty(false);setView('home');})}>Sair</button></div>}</header>
    {error&&<div className="banner error" role="alert">{error}<button onClick={()=>setError('')} aria-label="Fechar erro">×</button></div>}
    {notice&&<div className="banner notice" role="status">{notice}</div>}
    {!sessionReady?<main className="auth-layout"><p>Preparando seu caderno…</p></main>:!user?<main className="auth-layout">
      <section className="intro"><p className="eyebrow">UM NOVO CAMINHO COMEÇA AQUI</p><h1>Cada personagem<br/>carrega uma história.</h1><p>Construa sua ficha, entenda suas escolhas e prepare-se para a próxima sessão.</p><div className="intro-detail">◇<span>Criação guiada<br/>Revisão com seu mestre<br/>Seu caderno, sempre à mão</span></div><p className="muted">Perfil do livro Word · criação no nível 1</p></section>
      <section className="paper auth-card"><span className="section-number">01 / ACESSO AO CADERNO</span><h2>{authMode==='login'?'Bem-vindo de volta':'Comece sua jornada'}</h2><form onSubmit={e=>{e.preventDefault();void action(async()=>{const result=await api<{user:NonNullable<typeof user>}>(`/auth/${authMode}`,'POST',{username,password});setUser(result.user);setPassword('');});}}><label className="field">Usuário<input required autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)}/></label><label className="field">Senha<input type="password" required autoComplete={authMode==='login'?'current-password':'new-password'} value={password} onChange={e=>setPassword(e.target.value)}/><small>Na criação da conta, use pelo menos 8 caracteres e evite senhas comuns.</small></label><button className="primary" disabled={busy}>{busy?'Aguarde…':authMode==='login'?'Entrar no caderno →':'Criar minha conta →'}</button></form><button className="text-button" onClick={()=>setAuthMode(m=>m==='login'?'register':'login')}>{authMode==='login'?'Ainda não tenho conta':'Já tenho uma conta'}</button></section>
    </main>:<main className="workspace">
      <nav className="main-nav" aria-label="Navegação principal"><button className={view==='home'?'active':''} onClick={()=>setView('home')}>Meu caderno</button><button className={view==='compare'?'active':''} disabled={!campaignId} onClick={()=>setView('compare')}>Comparar arquétipos</button><div className="campaign-select"><label htmlFor="campaign">Campanha</label><select id="campaign" value={campaignId??''} onChange={e=>{if(dirty){setError('Salve sua edição antes de trocar de campanha.');return;}setCampaignId(Number(e.target.value));setCharacter(null);setDraft(emptyDraft());setReport(null);setView('home');}}><option value="" disabled>Selecione uma campanha</option>{campaigns.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></div></nav>
      {view==='home'?<>
        <section className="page-heading"><div><p className="eyebrow">SEU PRÓXIMO CAPÍTULO</p><h1>Meu caderno</h1><p>Personagens, escolhas e caminhos que ainda estão por vir.</p></div><button className="primary" disabled={!campaignId||busy||dirty} onClick={()=>void action(create)}>＋ Criar personagem</button></section>
        <section className="dashboard"><div className="character-grid">{characters.filter(c=>c.campaignId===campaignId).map(c=><button key={c.id} className="paper character-card" onClick={()=>open(c)}><span className="card-glyph">{marks[catalog?.archetypes.findIndex(a=>a.id===c.data.archetypeId)??0]??'◇'}</span><span className="tag">{c.approved?'Aprovada':c.submissions.length?'Em revisão':'Rascunho'} · nível 1</span><h2>{c.data.name||'Personagem sem nome'}</h2><p>{catalog?.classes.find(x=>x.id===c.data.classId)?.name||'Classe a escolher'} / {catalog?.archetypes.find(x=>x.id===c.data.archetypeId)?.name||'Arquétipo a escolher'}</p><span className="card-footer">Revisão {c.revision}<span>Abrir ficha ↗</span></span></button>)}{!characters.some(c=>c.campaignId===campaignId)&&<div className="paper empty"><span className="card-glyph">◇</span><h2>Uma página em branco.</h2><p>{campaignId?'Sua primeira história começa com um personagem.':'Crie uma campanha ou entre com o convite do mestre.'}</p></div>}</div>
        <aside className="paper campaign-panel"><p className="eyebrow">À MESA</p><h2>{campaign?.name||'Sua campanha'}</h2>{campaign&&<p>{campaign.role==='master'?'Você é o mestre desta campanha.':'Você participa como jogador.'}</p>}<form onSubmit={e=>{e.preventDefault();void action(async()=>{const c=await api<Campaign>('/campaigns','POST',{name:campaignName});await refresh();setCampaignId(c.id);setCampaignName('');});}}><label className="field">Nova campanha<input required maxLength={120} value={campaignName} onChange={e=>setCampaignName(e.target.value)} placeholder="Nome da sua mesa"/></label><button disabled={busy}>Criar como mestre</button></form><hr/><form onSubmit={e=>{e.preventDefault();void action(async()=>{const token=invite.includes('convite=')?new URL(invite).searchParams.get('convite'):invite;const result=await api<{campaignId:number}>('/join','POST',{token});await refresh();setCampaignId(result.campaignId);setInvite('');history.replaceState(null,'',location.pathname);});}}><label className="field">Convite do mestre<input value={invite} onChange={e=>setInvite(e.target.value)} required placeholder="Cole o link ou código"/></label><button disabled={busy}>Entrar na campanha</button></form>{campaign?.role==='master'&&<button className="text-button" disabled={busy} onClick={()=>void action(async()=>{const result=await api<{token:string}>(`/campaigns/${campaignId}/invites`,'POST');setInvite(`${location.origin}/?convite=${result.token}`);setNotice('Convite criado: válido por 7 dias, para uma pessoa. Copie o link no campo acima.');})}>Gerar convite de jogador ↗</button>}</aside></section>
      </>:view==='compare'?<>
        <section className="page-heading"><div><p className="eyebrow">QUATRO CAMINHOS, SUAS ESCOLHAS</p><h1>Encontre seu arquétipo</h1><p>As mesmas entradas para cada caminho. Classe e arquétipo são escolhas distintas.</p></div></section>
        <div className="paper comparison-inputs">{(['VIG','PRE'] as const).map(key=><label className="field" key={key}>{labels[key]}<input type="number" min="0" max="3" value={compareInputs[key]} onChange={e=>setCompareInputs(old=>({...old,[key]:Number(e.target.value)}))}/></label>)}<p>Recursos no nível 1, antes de benefícios raciais.<br/><small>Referências e imagens da campanha aguardam curadoria.</small></p></div>
        <div className="archetype-grid">{comparison.map(({archetype:a,report:r},i)=><article className="paper archetype-card" key={a.id}><span className="section-number">CAMINHO 0{i+1}</span><span className="card-glyph">{marks[i]}</span><h2>{a.name}</h2><p>{a.role}</p>{resources(r)}<h3>Habilidade inicial</h3><p>{a.initial}</p><h3>Trilhas futuras</h3><p>{a.trails.join(' · ')}</p><small>Prévia de progressão; trilhas não concedidas no nível 1.</small><hr/>{r.explanations.map(x=><p className="formula" key={x.field}>{x.field.toUpperCase()}: {x.formula} = {x.value}</p>)}<small>Fonte: Word / {a.name}</small></article>)}</div>
      </>:character?<>
        <section className="page-heading editor-heading"><div><p className="eyebrow">SEU PERSONAGEM / NÍVEL 1</p><h1>{draft.name||'Uma nova história'}</h1><p>{campaign?.name} <span className="tag">{character.approved&&!dirty?'Aprovada':'Em construção'}</span></p></div><div className="save-actions"><span role="status">{conflict?'Conflito de edição':saving?'Salvando…':dirty?'Alterações não salvas':'Salvo'} · revisão {character.revision}</span>{canEdit&&<button disabled={saving||conflict||!dirty} onClick={()=>void save()}>Salvar agora</button>}</div></section>
        {conflict&&<div className="banner error">Sua edição está preservada. Abra a versão salva para comparar antes de editar novamente.<button onClick={()=>void action(async()=>{const server=await api<Character>(`/characters/${character.id}`);setNotice(`Versão no servidor: ${JSON.stringify(server.data)}. Copie sua edição antes de usar a versão salva.`);})}>Ver versão salva</button><button onClick={()=>void action(async()=>{if(confirm('Substituir a edição atual pela versão salva no servidor?')) open(await api<Character>(`/characters/${character.id}`));})}>Usar versão salva</button></div>}
        <div className="editor-layout"><nav className="steps no-print" aria-label="Etapas de criação">{steps.map((s,i)=><button key={s} aria-current={step===i?'step':undefined} className={step===i?'active':''} onClick={()=>setStep(i)}><span>{String(i+1).padStart(2,'0')}</span>{s}</button>)}</nav>
        <section className="paper editor-content no-print"><span className="section-number">ETAPA {String(step+1).padStart(2,'0')} / 10</span><h2>{steps[step]}</h2>
          {step===0&&<>{field('name','Nome do personagem','Pode ser provisório.')}{field('concept','Quem você quer ser?','Descreva sua intenção de jogo e um objetivo.',true)}</>}
          {step===1&&<>{field('race','Raça','Registro manual para revisão do mestre. Benefícios raciais ainda não são aplicados automaticamente.')}<div className="callout">O catálogo racial ainda precisa de validação. Sua escolha ficará registrada como pendente.</div></>}
          {step===2&&<><p>Distribua seus atributos base. Cada um começa em 1; distribua 4 pontos adicionais. Valores entre 0 e 3.</p><div className="attribute-list">{attrKeys.map(k=><label key={k}><span>{labels[k]}<small>{k}</small></span><input aria-label={labels[k]} type="number" min="0" max="3" step="1" value={draft.attributes[k]??''} disabled={!canEdit} onChange={e=>change('attributes',{...draft.attributes,[k]:e.target.value===''?null:Number(e.target.value)})}/><button disabled={draft.attributes[k]===null||busy} onClick={()=>void action(async()=>{const result=await api<{faces:number[];result:number;mode:string}>('/rolls','POST',{attribute:draft.attributes[k]});setRollResult(`${labels[k]}: [${result.faces.join(', ')}] → ${result.result} (${result.mode} resultado)`);})}>Rolar</button></label>)}</div><p className="points">Pontos restantes: <strong>{9-attrKeys.reduce((n,k)=>n+(draft.attributes[k]??0),0)}</strong></p><small>Ao reduzir a 0, ganha um ponto. Atributo 0 rola 2d20 e escolhe o menor. Vantagem e treinamento aguardam definição.</small>{rollResult&&<div className="callout" role="status">{rollResult}</div>}</>}
          {step===3&&<div className="choice-list">{catalog?.classes.map(c=><label key={c.id} className={draft.classId===c.id?'selected':''}><input type="radio" name="class" value={c.id} checked={draft.classId===c.id} disabled={!canEdit} onChange={()=>change('classId',c.id)}/><span><strong>{c.name}</strong><small>Perícia principal: {c.skill}</small></span></label>)}</div>}
          {step===4&&<div className="choice-list">{comparison.map(({archetype:a,report:r},i)=><label key={a.id} className={draft.archetypeId===a.id?'selected':''}><input type="radio" name="archetype" checked={draft.archetypeId===a.id} disabled={!canEdit} onChange={()=>change('archetypeId',a.id)}/><span><strong>{marks[i]} {a.name}</strong><small>{a.role}</small><small>PV {r.maxima.pv??'—'} / PE {r.maxima.pe??'—'} / SAN {r.maxima.san??'—'}</small></span></label>)}</div>}
          {step===5&&<>{field('skills','Perícias e origem do treinamento','Registre cada escolha e sua origem (classe, raça ou escolha livre). Quantidades e graus aguardam R06.',true)}<div className="callout">Nenhum grau de treinamento ou bônus é concedido automaticamente.</div></>}
          {step===6&&<>{field('equipment','Arma e inventário','Informe itens, quantidades e efeitos para revisão.',true)}<label className="field">Tipo de técnica<select value={draft.techniqueKind} disabled={!canEdit} onChange={e=>change('techniqueKind',e.target.value)}><option value="">Não informada</option><option value="respiracao">Respiração</option><option value="sanguinea">Arte sanguínea</option><option value="outra">Outra</option></select></label>{field('techniques','Técnicas','Mantenha requisitos, custo e fonte. O mestre confere a elegibilidade.',true)}{field('uniqueAbility','Habilidade única','Registre a rolagem e a decisão do mestre. 16–19: mestre escolhe pela história; 20: escolha do jogador.',true)}</>}
          {step===7&&<>{field('story','História, aparência e relações',undefined,true)}<label className="field">Token da biblioteca<select value={draft.assetId??''} disabled={!canEdit} onChange={e=>change('assetId',e.target.value?Number(e.target.value):null)}><option value="">Sem imagem</option>{catalog?.assets.map(a=><option key={a.id} value={a.id}>{a.label}</option>)}</select><small>{catalog?.assets.length?'Apenas imagens liberadas para sua campanha.':'A biblioteca está vazia. Aguarda imagens autorizadas pelo mestre.'}</small></label></>}
          {step===8&&<><p>Confira suas escolhas e a origem dos cálculos.</p>{resources(activeReport)}{activeReport?.explanations.map(x=><div className="explanation" key={x.field}><strong>{x.field.toUpperCase()}: {x.formula} = {x.value}</strong><small>Entradas: {Object.entries(x.inputs).map(([k,v])=>`${k}=${v}`).join(' · ')||'valor fixo'}</small><small>{x.sourceDocument} / {x.sourceSection} / parágrafo {x.paragraph}</small></div>)}{canEdit&&<><h3>Recursos atuais durante a sessão</h3><div className="resource-inputs">{(['pv','pe','san'] as const).map(k=><label className="field" key={k}>{k.toUpperCase()} atual<input type="number" min="0" value={resourceDraft[k]} onChange={e=>setResourceDraft(old=>({...old,[k]:e.target.value}))}/></label>)}</div><button disabled={busy} onClick={()=>void action(async()=>{const values=Object.fromEntries(Object.entries(resourceDraft).map(([k,v])=>[k,v===''?null:Number(v)]));const result=await api<Character>(`/characters/${character.id}/resources`,'PATCH',values);setCharacter(result);setNotice('Recursos atuais salvos, separados da revisão mecânica.');})}>Salvar recursos atuais</button></>}<div className="export-actions"><a className="button" href={`/api/characters/${character.id}/export`}>Exportar JSON salvo</a><button onClick={()=>window.print()} disabled={dirty||saving}>Imprimir ficha salva</button></div>{dirty&&<small>Salve antes de exportar ou imprimir a nova revisão.</small>}</>}
          {step===9&&<><p>A aprovação pertence ao snapshot enviado. Você pode enviar com pendências para solicitar orientação.</p>{canEdit&&<button className="primary" disabled={busy||saving||conflict||!!activeReport?.errors.length} onClick={()=>void action(send)}>Enviar ao mestre →</button>}{character.submissions.length===0&&<p className="muted">Nenhuma revisão enviada.</p>}{character.submissions.map(s=><article className="submission" key={s.id}><h3>Revisão {s.revision} · {s.current?'atual':'histórica'}</h3><p>{s.snapshot.name||'Sem nome'} · {s.snapshot.race||'Raça pendente'} · {s.snapshot.classId} / {s.snapshot.archetypeId}</p><details><summary>Conferir snapshot e pendências</summary><p>Atributos: {attrKeys.map(k=>`${k} ${s.snapshot.attributes[k]??'não informado'}`).join(' · ')}</p><p>Perícias: {s.snapshot.skills||'Não informadas'}</p><p>Técnicas: {s.snapshot.techniques||'Não informadas'}</p><p>Equipamento: {s.snapshot.equipment||'Não informado'}</p><p>Habilidade única: {s.snapshot.uniqueAbility||'Não informada'}</p><p className="preserve">História: {s.snapshot.story||'Não informada'}</p>{s.report.pending.map(p=><p key={p.id}>{p.id}: {p.message}</p>)}</details>{s.review?<div className="callout">{s.review.status==='approved'?'Aprovada':'Ajustes solicitados'}<p>{s.review.comment}</p></div>:campaign?.role==='master'&&s.current&&<><label className="field">Comentário do mestre<textarea value={comment} onChange={e=>setComment(e.target.value)} rows={3}/></label><div className="review-actions"><button disabled={busy} onClick={()=>void action(()=>review(s.id,'changes'))}>Solicitar ajustes</button><button className="primary" disabled={busy||!s.report.canApprove} onClick={()=>void action(()=>review(s.id,'approved'))}>Aprovar snapshot</button></div>{!s.report.canApprove&&<small>Resolva as pendências abaixo e solicite um novo envio.</small>}</>}</article>)}
            {campaign?.role==='master'&&<div className="decision-form"><h3>Registrar decisão da mesa</h3><p>A decisão registra sua autoria e motivo. Validações de raça/técnica se aplicam somente à revisão desta ficha.</p><label className="field">Decisão<select aria-label="Decisão" value={rule} onChange={e=>setRule(e.target.value)}><option value="R06">Perícias e treinamento (R06)</option><option value="R08">Elegibilidade de técnicas (R08)</option><option value="R09">Pontos e limite racial (R09)</option><option value="RACE">Conferir raça e benefícios desta ficha</option><option value="TECHNIQUES">Conferir técnicas desta ficha</option><option value="ATIRADOR">Exceção de respiração para este Atirador</option></select></label>{rule==='R06'&&<><label className="check"><input type="checkbox" checked={mainExtra} onChange={e=>setMainExtra(e.target.checked)}/>Perícia principal é adicional</label><label className="field">Como tratar duplicatas<input value={duplicates} onChange={e=>setDuplicates(e.target.value)}/></label></>}{rule==='R09'&&<label className="check"><input type="checkbox" checked={spendAll} onChange={e=>setSpendAll(e.target.checked)}/>Exigir todos os 9 pontos base</label>}{['R06','R08','R09'].includes(rule)&&<label className="field">{rule==='R06'?'Graus de treinamento':rule==='R08'?'Elegibilidade por raça e classe':'Limite após o bônus do Híbrido'}<textarea value={decisionText} onChange={e=>setDecisionText(e.target.value)} rows={3}/></label>}<label className="field">Motivo e seção da fonte<textarea value={reason} onChange={e=>setReason(e.target.value)} rows={3}/></label><button disabled={busy||!reason.trim()} onClick={()=>void action(recordDecision)}>Registrar decisão</button></div>}</>}
          <div className="step-actions"><button disabled={step===0} onClick={()=>setStep(n=>n-1)}>← Voltar</button><span>{step+1} de 10</span><button disabled={step===9} onClick={()=>setStep(n=>n+1)}>Continuar →</button></div>
        </section><aside className="paper sheet-summary no-print"><p className="eyebrow">SUA FICHA</p><h2>{draft.name||'Sem nome, por enquanto'}</h2><p>{draft.race||'Raça a definir'}<br/>{catalog?.classes.find(c=>c.id===draft.classId)?.name||'Classe a definir'} / {catalog?.archetypes.find(a=>a.id===draft.archetypeId)?.name}</p>{resources(activeReport)}<hr/><h3>Antes da aprovação</h3>{activeReport?.errors.map(e=><p className="error-text" key={e}>{e}</p>)}{activeReport?.pending.map(p=><p className="pending" key={p.id}><strong>{p.id}</strong> {p.message}</p>)}{!activeReport?.pending.length&&!activeReport?.errors.length&&<p>Pronta para revisão do mestre.</p>}<details><summary>Limites dos cálculos</summary>{activeReport?.warnings.map(w=><p key={w}>{w}</p>)}</details><small>Regras v{character.rulesetVersion} · Word<br/>Nível 1 / em validação</small></aside></div>
        <section className="print-sheet"><h1>Ao Cair da Noite · {character.data.name||'Personagem'}</h1><p>Regras v{character.rulesetVersion} · nível 1 · revisão {character.revision} · {character.approved?'Aprovada':'Pendente de aprovação'}</p><p>Raça: {character.data.race||'Não informada'} · classe: {character.data.classId||'Não informada'} · arquétipo: {character.data.archetypeId}</p><p>{attrKeys.map(k=>`${labels[k]}: ${character.data.attributes[k]??'Não informado'}`).join(' / ')}</p>{resources(character.report)}<p>Recursos atuais: PV {character.resources.pv??'Não informado'} / PE {character.resources.pe??'Não informado'} / SAN {character.resources.san??'Não informado'}</p>{(['concept','skills','equipment','techniques','uniqueAbility','story'] as const).map((key,i)=><section key={key}><h2>{['Conceito','Perícias','Inventário','Técnicas','Habilidade única','História'][i]}</h2><p className="preserve">{character.data[key]||'Não informado'}</p></section>)}<h2>Fontes e pendências</h2>{character.report.explanations.map(x=><p key={x.field}>{x.field.toUpperCase()} = {x.formula} = {x.value} · {x.sourceDocument} / {x.sourceSection}</p>)}{character.report.pending.map(p=><p key={p.id}>{p.id}: {p.message}</p>)}{character.decisions.map(d=><p key={d.id}>Decisão {d.ruleId}: {d.reason}</p>)}</section>
      </>:<p>Abra uma ficha no caderno.</p>}
      <footer className="footer"><span>AO CAIR DA NOITE</span><span>Uma história de cada vez. ◑</span></footer>
    </main>}
  </>;
}
