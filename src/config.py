"""
Configuration for Nigerian News Twitter Scraper
"""

# Accounts to track by category
ACCOUNTS = {
    "news_outlets": [
        "channelstv", "guardian", "PremiumTimesNG", "SaharaReporters", 
        "TheCablNG", "LegitNG", "DailyPostNGR", "thenationonline", 
        "NgNewsAgency", "dailytrust", "BunchNews", "pointblanknewsnigeria", 
        "informationng"
    ],
    "journalists": [
        "DavidHundeyin", "ToluOgunlesi", "ZainabUsman", "Chidinmaiwueze", 
        "irenecnwoye", "OseniRufai", "KemiOlunloyo", "Omojuwa"
    ],
    "activists": [
        "AishaYesufu", "RinuOduala", "Letter_to_Jack", "falzthebadhguy", 
        "DJ_Switch_", "MaziIbe"
    ],
    "grassroots": [
        "Adenike_Oladosu", "TreeWithTunde", "ChidiOdinkalu", "AyoSogunro", 
        "DrJoeAbah", "Ikeoluwa", "PeaceItimi", "Nenne_Adora", 
        "Bolarinwa_Debo", "FisayoFosudo", "TosinOlaseinde", "NaijaFlyingDr", 
        "Aunty_Ada", "OneJoblessBoy"
    ],
    "commentary": [
        "Mr_Macaroni", "LayiWasabi", "KusssmanTV", "arojinle1", 
        "Morris_Monye", "Wizarab", "Ebuka_Obi_Uchendu"
    ]
}

# Keywords for relevance scoring
KEYWORDS = [
    "breaking", "urgent", "news", "confirmed",
    "government", "president", "minister", "parliament",
    "security", "protest", "strike", "arrested",
    "economy", "inflation", "business", "deal",
    "health", "hospital", "disease", "outbreak",
    "election", "vote", "campaign", "politics",
    "police", "army", "kidnap", "bandit", "attack"
]

# Scraper settings
MAX_TWEETS_PER_ACCOUNT = 50
MIN_ENGAGEMENT = 30
HEADLESS = True
DB_PATH = "data/nigerian_news.db"
JSON_PATH = "nigerian_news.json"
