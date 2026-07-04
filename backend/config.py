# Shared config — cluster descriptions for semantic routing, genre alias lists, and genre→cluster mappings.
# cluster_descriptions are embedded at startup in loader.py and used for cosine-sim cluster routing in fusion.py.

cluster_descriptions = {
    0:  "hip-hop and rap, trap and urban, modern beats and rhythmic flow, drake and kendrick energy",
    1:  "reggae, latin, and r&b grooves, warm and danceable, laid-back energy",
    2:  "classic acoustic and country, folk and blues, storytelling and warm, old-school songwriting",
    3:  "dark electronic and post-punk, club and dance, brooding and rhythmic, underground groove",
    4:  "metal and hardcore, aggressive and loud, fast and heavy, punk and extreme music",
    5:  "latin and world music, warm and celebratory, danceable and feel-good, reggae and tropical",
    6:  "soft pop and soul ballads, emotional and warm, mid-tempo, romantic and heartfelt",
    7:  "extreme metal and black metal, dark and intense, aggressive instrumentals, doom and death",
    8:  "world music and latin folk, acoustic and warm, diverse and rootsy, organic feel",
    9:  "jazz and classical, quiet and instrumental, introspective and sophisticated, ambient and acoustic",
    10: "indie rock and alternative, guitar-driven, mid-energy, punchy and melodic",
    11: "acoustic ballads and soft folk, intimate and gentle, classical vocals, quiet and beautiful",
    12: "upbeat pop and indie pop, light and catchy, feel-good electronic, bright and energetic",
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