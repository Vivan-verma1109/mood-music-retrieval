// main app component — all UI logic lives here
import { useState, useEffect } from 'react'
import './App.css'
import Bubbles from './Bubbles'

function SongCard({ r, rated, onFeedback }) {
    const [img, setImg] = useState(r.image || null)

    useEffect(() => {
        if (!img) {
            fetch(`https://open.spotify.com/oembed?url=https://open.spotify.com/track/${r.spotify_id}`)
                .then(res => res.json())
                .then(data => setImg(data.thumbnail_url))
                .catch(() => {})
        }
    }, [])

    return (
        <div className="card">
            <div className="card-feedback">
                <button onClick={() => onFeedback(r.song_id, 'great')} disabled={rated.has(r.song_id)}>🔥</button>
                <button onClick={() => onFeedback(r.song_id, 'good')} disabled={rated.has(r.song_id)}>👍</button>
                <button onClick={() => onFeedback(r.song_id, 'bad')} disabled={rated.has(r.song_id)}>👎</button>
                <button onClick={() => onFeedback(r.song_id, 'terrible')} disabled={rated.has(r.song_id)}>🗑️</button>
            </div>
            <a href={`https://open.spotify.com/track/${r.spotify_id}`} target="_blank" rel="noreferrer" className="card-body">
                {img
                    ? <img src={img} alt={r.name} className="card-img" />
                    : <div className="card-img-placeholder" />
                }
                <div className="card-text">
                    <div className="card-name">{r.name}</div>
                    <div className="card-artist">{r.artists}</div>
                </div>
            </a>
        </div>
    )
}

function App() {
    const [mood, setMood] = useState("I'm feeling ")
    const [genre, setGenre] = useState('')
    const [language, setLanguage] = useState('en')
    const [artist, setArtist] = useState('')
    
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [requestId, setRequestId] = useState(null)
    const [rated, setRated] = useState(new Set())

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
                body: JSON.stringify({ mood, top_k: 10, genre, language, artist }),
                signal: controller.signal,
            })
            const data = await res.json()
            setRequestId(data.request_id)
            setResults(data.results)
            setRated(new Set())
        } finally {
            // always re-enable the button, whether request succeeded, failed, or timed out
            clearTimeout(timeout)
            setLoading(false)
        }
    }

    async function submitFeedback(songId, rating) {
        setRated(prev => new Set(prev).add(songId))
        fetch('http://localhost:8000/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId, song_id: songId, rating }),
        })
    }

    return (
        <>
        <Bubbles />
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
                <div className="results-grid">
                    {results.map((r, i) => (
                        <SongCard key={i} r={r} rated={rated} onFeedback={submitFeedback} />
                    ))}
                </div>
            )}
        </div>
        </>
    )
}

export default App
