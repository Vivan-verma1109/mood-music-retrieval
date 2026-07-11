# Shared config — cluster descriptions for semantic routing, genre alias lists, and genre→cluster mappings.
# cluster_descriptions are embedded at startup in loader.py and used for cosine-sim cluster routing in fusion.py.

cluster_descriptions = {
    0:  "Mixed moody popular music. A broad blend of downcast pop, alternative, and atmospheric rock without one defining sound. Subdued and mid tempo. No specific activity or setting.",
    1:  "Laid back grooves and rhythms. Reggae, hip hop, rap, funk, soul, and smooth R&B with relaxed danceable rhythms and easygoing swagger. Cruising with the windows down, kicking back with friends, smoke sessions, chill evening hangouts.",
    2:  "Warm vintage acoustic classics. Crooners, classic country, oldies, tango, and timeless standards with a relaxed, nostalgic, easygoing feel. Sunday morning coffee, cooking dinner, lazy afternoons, music your grandparents loved.",
    3:  "Energetic instrumental electronic. Techno, trance, house, and synth-driven dance music with pulsing beats and few or no vocals. Night driving, raves, coding sessions with driving beats, late night energy.",
    4:  "Aggressive mainstream metal and hard rock. Distorted guitars, pounding drums, powerful sung or shouted vocals, dark and intense. Lifting heavy at the gym, hard workouts, blowing off steam, rage energy.",
    5:  "Euphoric party pop and dance. Upbeat reggaeton, dance pop, kpop, and feel-good hits with high energy and maximum positivity. Pregaming, house parties, clubbing, dancing with friends, getting hyped.",
    6:  "Melancholy modern songs with feeling. Wistful singer-songwriter, emotional pop, and bittersweet ballads, sad but not silent. Rainy days, processing a breakup, up late in your feelings, journaling.",
    7:  "Extreme and harsh heavy music. Death metal, grindcore, black metal, and industrial with growled vocals, blast beats, and crushing intensity. The heaviest end of heavy, mosh pits, pure aggression.",
    8:  "Feel-good roots and tropical grooves. Salsa, forró, classic rock and roll, and sunny acoustic music that makes you move. Backyard bbq, cookouts, beach days, summer hangouts, family gatherings.",
    9:  "Calm quiet instrumental. Ambient, solo piano, gentle acoustic instrumentals, and meditative soundscapes with little or no singing. Studying, deep focus, reading, meditation, falling asleep.",
    10: "Fast loud punk and ska. Pop punk, skate punk, and high tempo rock with shouted choruses and relentless speed. Running, cardio, skateboarding, driving fast on the highway.",
    11: "Hushed timeless ballads and torch songs. Quiet jazz standards, sad country, opera, and intimate vocal performances, slow and sparse. Candlelit evenings, slow dancing, quiet heartbreak, winding down alone.",
    12: "High energy mainstream rock and pop crossover. Energetic radio rock, pop rock, and upbeat anthems with big production. Keeping momentum going, upbeat background energy.",
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
    "hiphop":     [0, 3],
    "rap":        [0, 3],
    "pop":        [6, 12],
    "lofi":       [0, 3],
    "rnb":        [1, 6],
    "electronic": [3, 12],
    "rock":       [4, 10],
    "metal":      [4, 7],
    "jazz":       [9],
    "classical":  [9, 11],
    "country":    [2],
    "latin":      [1, 5],
    "reggae":     [1, 5],
    "emo":        [4, 10],
    "punk":       [4, 10],
    "kpop":       [6, 12],
    "anime":      [6, 12],
}