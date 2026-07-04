cluster_descriptions = {
    0: "acoustic and mellow, warm and intimate, background music for relaxing or studying, folk and singer-songwriter, cozy and unhurried",
    1: "happy and euphoric, high energy dance music, upbeat pop, feel-good and celebratory, electronic and bright",
    2: "aggressive and intense, hard rock and metal, dark and powerful, driving and relentless, raw and heavy",
    3: "moody and brooding, mid-tempo and atmospheric, bittersweet, neither loud nor quiet, contemplative and cloudy",
    4: "upbeat and warm, feel-good acoustic pop, sunny and optimistic, half-acoustic half-electronic, easy and light",
    5: "high energy and driving, electric and hard-hitting, hip-hop and rock energy, intense without being dark, urgent and forward-moving",
    6: "quiet and deeply sad, acoustic and sparse, lonely and introspective, slow and somber, heartbreak and grief",
    7: "dark and groovy, late-night electronic, trap and R&B, brooding with a steady pulse, atmospheric and nocturnal",
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

                                
GENRE_CLUSTERS = {
    "hiphop": [5, 7],
    "rap":    [5, 7],
    "pop":    [1, 4],
    "lofi":   [0],
    "rnb":    [7],
    "electronic": [1, 7],
    "rock":   [2, 5],
    "metal":  [2],
    "jazz":   [0, 3],
    "classical": [0],
    "country": [0, 4],
    "latin":  [1, 4],
    "reggae": [4],
    "emo":    [3, 6],
    "punk":   [2, 5],
    "kpop":   [1, 4],
    "anime":  [1, 3],
}