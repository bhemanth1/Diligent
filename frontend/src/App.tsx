import React, { useState } from 'react'

const API_BASE: string = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8000'

type Msg = { role: 'user' | 'assistant', content: string }

type Source = { source: string, score: number }

export default function App() {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sources, setSources] = useState<Source[]>([])

  const send = async () => {
    const q = input.trim()
    if (!q || loading) return
    setMessages((prev: Msg[]) => [...prev, { role: 'user', content: q }])
    setInput('')
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q, top_k: 4 })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setMessages((prev: Msg[]) => [...prev, { role: 'assistant', content: data.answer }])
      setSources((data.sources || []) as Source[])
    } catch (e: any) {
      setMessages((prev: Msg[]) => [...prev, { role: 'assistant', content: `Error: ${e.message || e}` }])
    } finally {
      setLoading(false)
    }
  }

  const onKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') send()
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b bg-white">
        <div className="max-w-4xl mx-auto p-4">
          <h1 className="text-2xl font-semibold">Jarvis Assistant</h1>
          <p className="text-sm text-slate-500">Self-hosted LLM + Pinecone RAG</p>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full p-4 space-y-4">
        <div className="bg-white border rounded-lg p-4 h-[60vh] overflow-y-auto space-y-3">
          {messages.length === 0 && (
            <div className="text-slate-500">Ask anything about your ingested docs.</div>
          )}
          {messages.map((m: Msg, i: number) => (
            <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
              <div className={`inline-block px-3 py-2 rounded-lg ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-100'}`}>
                {m.content}
              </div>
            </div>
          ))}
          {loading && <div className="text-slate-400">Thinking…</div>}
        </div>

        {sources.length > 0 && (
          <div className="bg-white border rounded-lg p-3">
            <div className="font-medium mb-2">Sources</div>
            <ul className="list-disc ml-6">
              {sources.map((s: Source, i: number) => (
                <li key={i} className="text-sm text-slate-600">{s.source} <span className="text-slate-400">(score {s.score.toFixed(3)})</span></li>
              ))}
            </ul>
          </div>
        )}
      </main>

      <div className="border-t bg-white">
        <div className="max-w-4xl mx-auto p-4 flex gap-2">
          <input
            className="flex-1 border rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-400"
            placeholder="Type your message and press Enter"
            value={input}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
            onKeyDown={onKey}
          />
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg" onClick={send} disabled={loading}>Send</button>
        </div>
      </div>
    </div>
  )
}
