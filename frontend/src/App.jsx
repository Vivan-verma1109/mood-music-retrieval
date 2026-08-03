// main app component — all UI logic lives here
import { useState, useEffect } from 'react'
import './App.css'
import Bubbles from './Bubbles'

function SongCard({ r, rated, onFeedback, onLike }) {
    const [img, setImg] = useState(r.image || null)
    const [liked, setLiked] = useState(false)

    // handles heart click — likes if not liked, unlikes if already liked
    async function handleHeartClick() {
        if (liked) {
            await fetch('http://127.0.0.1:8000/unlike', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ spotify_id: r.spotify_id }),
            })
            setLiked(false)
        } else {
            await onLike(r.spotify_id)
            setLiked(true)
        }
    }

    useEffect(() => {
        setImg(r.image || null)
        if (!r.image) {
            fetch(`https://open.spotify.com/oembed?url=https://open.spotify.com/track/${r.spotify_id}`)
                .then(res => res.json())
                .then(data => setImg(data.thumbnail_url))
                .catch(() => {})
        }
    }, [r.spotify_id])

    return (
        <div className="card">
            <div className="card-feedback">
                <button className="feedback-btn" onClick={() => onFeedback(r.song_id, 'great')} disabled={rated.has(r.song_id)}>🔥</button>
                <button className="feedback-btn" onClick={() => onFeedback(r.song_id, 'good')} disabled={rated.has(r.song_id)}>👍</button>
                <button className="feedback-btn" onClick={() => onFeedback(r.song_id, 'bad')} disabled={rated.has(r.song_id)}>👎</button>
                <button className="feedback-btn" onClick={() => onFeedback(r.song_id, 'terrible')} disabled={rated.has(r.song_id)}>🗑️</button>
            </div>
            <button className="like-btn" onClick={handleHeartClick}>{liked ? '♥' : '♡'}</button>
            <a href={`https://open.spotify.com/track/${r.spotify_id}`} target="_blank" rel="noreferrer" className="card-body">
                <div className="card-img-wrapper">
                    {img
                        ? <img src={img} alt={r.name} className="card-img" />
                        : <div className="card-img-placeholder" />
                    }
                </div>
                <div className="card-text">
                    <div className="card-name">{r.name}</div>
                    <div className="card-artist">{r.artists}</div>
                </div>
            </a>
        </div>
    )
}

function App() {
    const [mood, setMood] = useState('')
    const [genre, setGenre] = useState('')
    const [language, setLanguage] = useState('en')
    const [artist, setArtist] = useState('')
    
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [requestId, setRequestId] = useState(null)
    const [rated, setRated] = useState(new Set())

    const [offset, setOffset] = useState(0)
    const [refreshCount, setRefreshCount] = useState(0)
    const [cd, setCd] = useState(false)

    const [spotifyConnected, setSpotifyConnected] = useState(false)
    const [spotifyUser, setSpotifyUser] = useState(null)
    const [spotifyAvatar, setSpotifyAvatar] = useState(null)

    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        if (params.get("spotify") === 'connected'){
            setSpotifyConnected(true)
            setSpotifyUser(params.get('spotify_user'))
            setSpotifyAvatar(params.get('spotify_avatar'))
            window.history.replaceState({}, '', '/') // cleanup URL
        }
    }, [])

    useEffect(() => {
        if (!spotifyConnected) return
        const pendingId = localStorage.getItem('pending_like')
        if (!pendingId) return
        localStorage.removeItem('pending_like')
        fetch('http://127.0.0.1:8000/like', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ spotify_id: pendingId }),
        })
    }, [spotifyConnected])

  // handles heart click — likes directly if connected, otherwise saves id and redirects to spotify login
  async function handleLike(spotify_id) {
      if (spotifyConnected) {
          await fetch('http://127.0.0.1:8000/like', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ spotify_id }),
          })
      } else {
          localStorage.setItem('pending_like', spotify_id)
          window.location.href = 'http://127.0.0.1:8000/auth/spotify'
      }
  }

    // called when the form is submitted — runs the full query and resets all pagination state
    async function handleSubmit(e) {
        if (e)
            e.preventDefault()
        setLoading(true)
        // abort the request if it takes longer than 2 minutes
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), 120000)
        try {
            const res = await fetch('http://localhost:8000/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mood, top_k: 50, genre, language, artist }),
                signal: controller.signal,
            })
            const data = await res.json()
            setRequestId(data.request_id)
            setResults(data.results)
            setRated(new Set())
            setOffset(0)
            setRefreshCount(0)
            setCd(false)
        } finally {
            // always re-enable the button, whether request succeeded, failed, or timed out
            clearTimeout(timeout)
            
            setLoading(false)
        }
    }

    // sends a rating for a song to the backend and marks it as rated so buttons disable
    async function submitFeedback(songId, rating) {
        setRated(prev => new Set(prev).add(songId))
        const res = await fetch('http://localhost:8000/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId, song_id: songId, rating }),
        })
    }
    // fetches the next 10 songs from the cached pool and replaces the current grid
    async function nextTen(){
        const newOffset = offset + 10
        setCd(true)
        const res = await fetch('http://localhost:8000/page', {
            method: "POST",
            headers: { 'Content-Type': 'application/json' },
            body:  JSON.stringify({ request_id: requestId, offset: newOffset}),
        })
        if (res.status === 410){
            handleSubmit()
            setCd(false)
            return
        }
        const data = await res.json()
        setResults(data.results)
        setOffset(newOffset)
        const newCount = refreshCount + 1
        setRefreshCount(newCount)
        setTimeout(() => setCd(false), 3000)
    }

    return (
        <>
        <Bubbles />
        <div className="spotify-connect-wrapper">
            {spotifyConnected && spotifyAvatar && (
                <img src={spotifyAvatar} className="spotify-avatar" alt="profile" />
            )}
            {spotifyConnected ? (
                <>
                    <span className="spotify-connect-btn" style={{cursor: 'default'}}>
                        Connected: {spotifyUser}
                    </span>
                    <button
                        className="spotify-connect-btn"
                        onClick={async () => {
                            await fetch('http://127.0.0.1:8000/auth/logout', { method: 'POST' })
                            setSpotifyConnected(false)
                            setSpotifyUser(null)
                            setSpotifyAvatar(null)
                        }}
                    >
                        Log out
                    </button>
                </>
            ) : (
                <button
                    className="spotify-connect-btn"
                    onClick={() => window.location.href = 'http://127.0.0.1:8000/auth/spotify'}
                >
                    Connect Spotify
                </button>
            )}
        </div>
        <div className="container">
            <h1>Mood Moosic</h1>
            <form onSubmit={handleSubmit}>
                {/* mood query gets its own full-width row */}
                <div className="form-mood">
                    <input
                        type="text"
                        placeholder="Describe a mood, vibe, or activity..."
                        value={mood}
                        onChange={e => setMood(e.target.value)}
                    />
                </div>
                {/* filters and action buttons sit on the second row */}
                <div className="form-filters">
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
                    <button type="button" className="refresh-btn" onClick={nextTen} disabled={cd || refreshCount >= 4 || results.length === 0}>
                        Refresh
                    </button>
                </div>
            </form>

              {results.length > 0 && (
                  <div className="results-grid">
                      {results.map((r, i) => (
                          <SongCard key={r.song_id} r={r} rated={rated} onFeedback={submitFeedback} onLike={handleLike} />
                      ))}
                  </div>
              )}
              {refreshCount >= 4 && (
                  <p className="sorry-msg">Sorry thats all this query has, if you do not like the results try another!</p>
              )}
        </div>
        </>
    )
}

export default App
