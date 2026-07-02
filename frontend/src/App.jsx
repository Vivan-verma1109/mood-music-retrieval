// main app component — all UI logic lives here
import { useState } from 'react'
import './App.css'

function App() {
    const [mood, setMood] = useState("I'm feeling ")
    const [genre, setGenre] = useState('')
    const [language, setLanguage] = useState('')
    const [artist, setArtist] = useState('')
    
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)

    async function handleSubmit(e) {
        e.preventDefault()
        setLoading(true)
        // abort the request if it takes longer than 2 minutes
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), 120000)
        try {
            const res = await fetch('http://localhost:8000/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mood, top_k: 20, genre, language, artist }),
                signal: controller.signal,
            })
            const data = await res.json()
            setResults(data)
        } finally {
            // always re-enable the button, whether request succeeded, failed, or timed out
            clearTimeout(timeout)
            setLoading(false)
        }
    }

    return (
        <div className="container">
            <h1>Mood Moosic</h1>
            <form onSubmit={handleSubmit}>
                <input
                    type="text"
                    value={mood}
                    onChange={e => setMood(e.target.value)}
                />
                <select value={genre} onChange={e => setGenre(e.target.value)}>
                    <option value="">Any genre</option>
                    <option value="hiphop">Hip Hop</option>
                    <option value="pop">Pop</option>
                    <option value="rock">Rock</option>
                    <option value="rnb">R&B</option>
                    <option value="electronic">Electronic</option>
                    <option value="jazz">Jazz</option>
                    <option value="classical">Classical</option>
                    <option value="metal">Metal</option>
                    <option value="lofi">Lo-Fi</option>
                    <option value="kpop">K-Pop</option>
                    <option value="anime">Anime</option>
                    <option value="latin">Latin</option>
                </select>
                <select value={language} onChange={e => setLanguage(e.target.value)}>
                    <option value="">Any language</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                    <option value="ko">Korean</option>
                    <option value="ja">Japanese</option>
                    <option value="hi">Hindi</option>
                    <option value="pt">Portuguese</option>
                </select>
                <input
                    type="text"
                    placeholder="Artist (optional)"
                    value={artist}
                    onChange={e => setArtist(e.target.value)}
                />
                <button type="submit" disabled={loading}>
                    {loading ? 'Finding...' : 'Find Songs'}
                </button>
            </form>

            {results.length > 0 && (
                <table>
                    <thead>
                        <tr>
                            <th>Song</th>
                            <th>Artist</th>
                        </tr>
                    </thead>
                    <tbody>
                        {results.map((r, i) => (
                            <tr key={i}>
                                <td>{r.name}</td>
                                <td>{r.artists}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    )
}

export default App
