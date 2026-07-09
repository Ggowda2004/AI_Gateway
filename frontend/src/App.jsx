import { useEffect, useState } from 'react'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

export default function App() {
  const [view, setView] = useState(() => (localStorage.getItem('ai-gateway-token') ? 'landing' : 'auth'))
  const [authMode, setAuthMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem('ai-gateway-token') || '')
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('ai-gateway-api-key') || '')
  const [newApiKeyName, setNewApiKeyName] = useState('frontend-key')
  const [generatedKey, setGeneratedKey] = useState('')
  const [model, setModel] = useState('gemini-2.5-flash')
  const [prompt, setPrompt] = useState('Explain the difference between a REST API and a WebSocket connection.')
  const [conversation, setConversation] = useState([])
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState('Welcome. Sign in or create an account to get started.')
  const [error, setError] = useState('')

  useEffect(() => {
    if (accessToken) {
      localStorage.setItem('ai-gateway-token', accessToken)
    } else {
      localStorage.removeItem('ai-gateway-token')
    }
  }, [accessToken])

  useEffect(() => {
    if (apiKey) {
      localStorage.setItem('ai-gateway-api-key', apiKey)
    } else {
      localStorage.removeItem('ai-gateway-api-key')
    }
  }, [apiKey])

  const handleAuth = async () => {
    setError('')

    if (authMode === 'register') {
      setStatus('Registering account...')
      try {
        const response = await fetch(`${BACKEND_URL}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })
        const data = await response.json()
        if (!response.ok) throw new Error(data.detail || JSON.stringify(data))
        setStatus(`Account created for ${data.email}. Please sign in now.`)
        setAuthMode('login')
      } catch (err) {
        setError(err.message)
        setStatus('Registration failed.')
      }
      return
    }

    setStatus('Signing in...')
    try {
      const form = new URLSearchParams()
      form.set('username', email)
      form.set('password', password)
      const response = await fetch(`${BACKEND_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString()
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || JSON.stringify(data))
      setAccessToken(data.access_token)
      setView('landing')
      setStatus('Signed in successfully. Choose a feature to continue.')
    } catch (err) {
      setError(err.message)
      setStatus('Login failed.')
    }
  }

  const handleCreateApiKey = async () => {
    setError('')
    setStatus('Creating API key...')
    try {
      if (!accessToken) throw new Error('Please sign in first.')
      const response = await fetch(`${BACKEND_URL}/key/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${accessToken}`
        },
        body: JSON.stringify({ name: newApiKeyName })
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.detail || JSON.stringify(data))
      setGeneratedKey(data.raw_key)
      setApiKey(data.raw_key)
      setStatus('API key created and ready for chat requests.')
      setView('api-key')
    } catch (err) {
      setError(err.message)
      setStatus('Creating the API key failed.')
    }
  }

  const handleSendMessage = async () => {
    setError('')
    if (!apiKey) {
      setError('Create or paste an API key before sending a request.')
      return
    }
    if (!prompt.trim()) {
      setError('Please enter a prompt before sending.')
      return
    }

    const userMessage = { role: 'user', content: prompt.trim() }
    const assistantMessage = { role: 'assistant', content: '', streaming: true }
    const assistantIndex = conversation.length + 1
    const requestMessages = [...conversation, userMessage]
    setConversation([...conversation, userMessage, assistantMessage])
    setLoading(true)
    setStatus('Streaming response from the gateway...')

    try {
      const response = await fetch(`${BACKEND_URL}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey
        },
        body: JSON.stringify({
          model,
          temperature: 0.7,
          messages: requestMessages
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Gateway request failed.')
      }

      const contentType = response.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        const data = await response.json()
        const botText = data.content || data.error || 'No response content received.'
        setConversation((prev) =>
          prev.map((item, index) => (index === assistantIndex ? { ...item, content: botText, streaming: false } : item))
        )
        setStatus('Response received from the AI gateway.')
        return
      }

      if (!response.body) throw new Error('Streaming is not available from the backend.')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let streamedText = ''
      let streamError = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          const lines = part.split('\n')
          let data = ''
          for (const line of lines) {
            if (line.startsWith('data:')) {
              data += line.slice(5).trim()
            }
          }
          if (!data) continue

          try {
            const payload = JSON.parse(data)
            if (payload.error) {
              streamError = payload.error
              break
            }
            if (payload.content) {
              streamedText += payload.content
              setConversation((prev) =>
                prev.map((item, index) => (index === assistantIndex ? { ...item, content: item.content + payload.content } : item))
              )
            }
          } catch {
            streamedText += data
            setConversation((prev) =>
              prev.map((item, index) => (index === assistantIndex ? { ...item, content: item.content + data } : item))
            )
          }
        }

        if (streamError) break
      }

      buffer += decoder.decode()
      const trailingParts = buffer.split('\n\n')
      for (const part of trailingParts) {
        const lines = part.split('\n')
        let data = ''
        for (const line of lines) {
          if (line.startsWith('data:')) data += line.slice(5).trim()
        }
        if (!data) continue
        try {
          const payload = JSON.parse(data)
          if (payload.error) {
            streamError = payload.error
            break
          }
          if (payload.content) {
            streamedText += payload.content
            setConversation((prev) =>
              prev.map((item, index) => (index === assistantIndex ? { ...item, content: item.content + payload.content } : item))
            )
          }
        } catch {
          streamedText += data
          setConversation((prev) =>
            prev.map((item, index) => (index === assistantIndex ? { ...item, content: item.content + data } : item))
          )
        }
      }

      if (streamError) throw new Error(streamError)
      if (!streamedText.trim()) {
        setConversation((prev) => prev.map((item, index) => (index === assistantIndex ? { ...item, content: 'No response content received.' } : item)))
      }
      setConversation((prev) => prev.map((item, index) => (index === assistantIndex ? { ...item, streaming: false } : item)))
      setStatus('Response received from the AI gateway.')
    } catch (err) {
      setError(err.message || 'Chat request failed.')
      setConversation((prev) => prev.map((item, index) => (index === assistantIndex ? { ...item, streaming: false, content: item.content || 'The response failed.' } : item)))
      setStatus('Chat request failed.')
    } finally {
      setLoading(false)
      setPrompt('')
    }
  }

  const handleLogout = () => {
    setAccessToken('')
    setApiKey('')
    setGeneratedKey('')
    setConversation([])
    setView('auth')
    setStatus('Signed out. You can sign in again whenever you want.')
    setError('')
  }

  return (
    <div className="app-shell">
      {!accessToken ? (
        <>
          <section className="hero-card">
            <div>
              <p className="eyebrow">AI Gateway UI</p>
              <h1>Log in, create a key, and chat with your gateway</h1>
              <p className="subtitle">
                This interface connects your React app to the FastAPI backend for authentication, API-key creation, and model chat requests.
              </p>
            </div>
            <div className="pill-row">
              <span className="pill">Backend: {BACKEND_URL}</span>
              <span className="pill">Auth: not signed in</span>
            </div>
          </section>

          <div className="grid-layout single-column">
            <section className="card auth-card">
              <div className="card-header">
                <div>
                  <p className="section-label">Step 1</p>
                  <h2>{authMode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
                </div>
                <div className="segmented">
                  <button className={authMode === 'login' ? 'secondary active' : 'secondary'} onClick={() => setAuthMode('login')}>
                    Login
                  </button>
                  <button className={authMode === 'register' ? 'secondary active' : 'secondary'} onClick={() => setAuthMode('register')}>
                    Register
                  </button>
                </div>
              </div>
              <label>Email</label>
              <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
              <label>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" />
              <div className="button-group">
                <button onClick={handleAuth}>{authMode === 'login' ? 'Login' : 'Register'}</button>
                {authMode === 'register' ? (
                  <button className="secondary" onClick={() => setAuthMode('login')}>
                    Switch to login
                  </button>
                ) : null}
              </div>
              <p className="hint">
                {authMode === 'login'
                  ? 'Sign in to continue to your dashboard.'
                  : 'Register a new account and then sign in to continue.'}
              </p>
            </section>
          </div>
        </>
      ) : (
        <div className="workspace-shell">
          <aside className="sidebar">
            <div>
              <p className="eyebrow">AI Gateway</p>
              <h2>Workspace</h2>
            </div>
            <div className="sidebar-links">
              <button className={view === 'landing' ? 'nav-button active' : 'nav-button'} onClick={() => setView('landing')}>
                Overview
              </button>
              <button className={view === 'api-key' ? 'nav-button active' : 'nav-button'} onClick={() => setView('api-key')}>
                Create Key
              </button>
              <button className={view === 'chat' ? 'nav-button active' : 'nav-button'} onClick={() => setView('chat')}>
                Chat
              </button>
            </div>
            <button className="secondary logout-button" onClick={handleLogout}>
              Logout
            </button>
          </aside>

          <main className="main-panel">
            {view === 'landing' ? (
              <div className="landing-grid">
                <section className="card landing-card">
                  <p className="section-label">Welcome back</p>
                  <h2>Everything you need is here</h2>
                  <p className="subtitle compact">
                    Create a key, validate it in the chat panel, and talk to your gateway model in a cleaner, streaming experience.
                  </p>
                  <div className="button-group">
                    <button onClick={() => setView('api-key')}>Create API key</button>
                    <button className="secondary" onClick={() => setView('chat')}>
                      Open chat
                    </button>
                  </div>
                </section>

                <section className="card">
                  <h3>Quick start</h3>
                  <ul className="feature-list">
                    <li>Generate a new API key for the gateway.</li>
                    <li>Paste the key into the chat panel for validation.</li>
                    <li>Select a model and send prompts that stream in real time.</li>
                  </ul>
                </section>
              </div>
            ) : view === 'api-key' ? (
              <section className="card">
                <div className="card-header">
                  <div>
                    <p className="section-label">Step 2</p>
                    <h2>Create an API key</h2>
                  </div>
                </div>
                <label>Key name</label>
                <input value={newApiKeyName} onChange={(e) => setNewApiKeyName(e.target.value)} placeholder="frontend-key" />
                <div className="button-group">
                  <button onClick={handleCreateApiKey}>Create key</button>
                  <button className="secondary" onClick={() => setView('chat')} disabled={!apiKey}>
                    Open chat
                  </button>
                </div>
                {generatedKey ? (
                  <div className="result-box">
                    <p className="small-label">Generated key</p>
                    <code>{generatedKey}</code>
                  </div>
                ) : null}
                <p className="hint">The key is saved locally and will be used for chat validation.</p>
              </section>
            ) : (
              <div className="chat-layout">
                <section className="card composer-card">
                  <div className="card-header">
                    <div>
                      <p className="section-label">Step 3</p>
                      <h2>Chat with your gateway</h2>
                    </div>
                  </div>
                  <label>API key</label>
                  <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Paste your API key here" />
                  <label>Model</label>
                  <select value={model} onChange={(e) => setModel(e.target.value)}>
                    <option value="gemini-2.5-flash">gemini-2.5-flash</option>
                    <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
                  </select>
                  <label>Prompt</label>
                  <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows="4" />
                  <button onClick={handleSendMessage} disabled={loading}>
                    {loading ? 'Streaming...' : 'Send message'}
                  </button>
                </section>

                <section className="card conversation-card">
                  <h3>Conversation</h3>
                  <div className="conversation-panel">
                    {conversation.length === 0 ? (
                      <p className="empty-state">No messages yet. Create a key and start chatting.</p>
                    ) : (
                      conversation.map((item, index) => (
                        <div key={`${item.role}-${index}`} className={`message ${item.role}`}>
                          <span className="message-role">{item.role}</span>
                          <p className="message-content">{item.content || (item.streaming ? 'Streaming…' : '…')}</p>
                        </div>
                      ))
                    )}
                  </div>
                </section>
              </div>
            )}
          </main>
        </div>
      )}

      <div className="status-bar">
        <span>{status}</span>
        {error ? <strong className="error">{error}</strong> : null}
      </div>
    </div>
  )
}
