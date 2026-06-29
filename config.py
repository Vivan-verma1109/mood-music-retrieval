cluster_tags = {
    0: ['chill', 'acoustic', 'folk', 'mellow', 'cozy', 'soft', 'warm'],
    1: ['happy', 'euphoric', 'party', 'dance', 'excited', 'pumped', 'fun', 'upbeat'],
    2: ['angry', 'rage', 'aggressive', 'intense', 'heavy', 'powerful', 'fierce', 'mad', 'metal', 'hardcore'],
    3: ['moody', 'brooding', 'bittersweet', 'contemplative', 'pensive', 'gloomy', 'mid-tempo', 'melancholic'],
    4: ['sunny', 'peaceful', 'relaxed', 'good vibes', 'uplifting', 'positive'],
    5: ['rap', 'hip hop', 'hiphop', 'energetic', 'hype', 'lit', 'turn up', 'rock', 'alt'],
    6: ['sad', 'lonely', 'introspective', 'heartbreak', 'depressed', 'somber', 'quiet', 'crying'],
    7: ['dark', 'vibe', 'night', 'late night', 'drive', 'r&b', 'rnb', 'trap', 'drill'],
}

_HIP_HOP = ["hip hop", "hiphop", "hip-hop", "rap", "trap", "drill", "boom bap", "conscious hip hop"]
_DRILL = ["uk drill", "drill", "drill music", "chicago drill"]
_ANIME = ["anime", "anisong", "anime ost", "j-pop", "jpop", "visual kei"]
_JPOP = ["j-pop", "jpop", "japanese pop", "city pop"]
_KPOP = ["k-pop", "kpop", "korean pop"]

GENRE_ALIASES = {
    "hiphop":     _HIP_HOP,
    "rap":        _HIP_HOP,
    "drill":      _DRILL,
    "uk drill":   _DRILL,
    "anime":      _ANIME,
    "jpop":       _JPOP,
    "j-pop":      _JPOP,
    "kpop":       _KPOP,
    "k-pop":      _KPOP,
    "lofi":       ["lofi", "lo-fi", "lofi hip hop", "chillhop", "study beats", "chill beats"],
    "pop":        ["pop", "indie pop", "synth pop", "electropop", "dream pop", "art pop"],
    "r&b":        ["r&b", "rnb", "soul", "neo soul", "contemporary r&b"],
    "electronic": ["electronic", "edm", "house", "techno", "trance", "ambient", "electronica"],
    "rock":       ["rock", "indie rock", "alternative", "alt rock", "grunge", "garage rock"],
    "metal":      ["metal", "heavy metal", "death metal", "black metal", "metalcore"],
    "jazz":       ["jazz", "smooth jazz", "bebop", "fusion", "nu jazz"],
    "classical":  ["classical", "orchestral", "contemporary classical", "chamber music"],
    "country":    ["country", "folk", "americana", "bluegrass"],
    "latin":      ["latin", "reggaeton", "salsa", "bachata", "cumbia"],
    "reggae":     ["reggae", "dancehall", "dub"],
    "emo":        ["emo", "emo pop", "post-hardcore", "screamo", "midwest emo"],
    "punk":       ["punk", "punk rock", "pop punk", "hardcore punk", "skate punk"],
}


# add a filter for artist name