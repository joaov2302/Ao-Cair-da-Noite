export class ApiError extends Error {
  constructor(public status:number, message:string, public detail:unknown) {super(message);}
}
export async function api<T>(url:string, method='GET', data?:unknown, signal?:AbortSignal):Promise<T> {
  const csrf = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=').slice(1).join('=') ?? '';
  const response = await fetch('/api' + url,{method,credentials:'same-origin',signal,headers:{'Content-Type':'application/json','X-CSRFToken':decodeURIComponent(csrf)},body:data === undefined ? undefined : JSON.stringify(data)});
  const result = await response.json().catch(() => ({detail:'Resposta indisponível. Confira a conexão com o servidor.'}));
  if (!response.ok) throw new ApiError(response.status, result.detail ?? Object.entries(result).map(([k,v])=>`${k}: ${JSON.stringify(v)}`).join(' · '),result);
  return result as T;
}
