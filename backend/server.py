from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import random
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class Suggestion(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    name_ar: str
    category: str
    year: Optional[int] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    external_url: Optional[str] = None

class SuggestionResponse(BaseModel):
    suggestion: Suggestion
    total_in_category: int

class FavoriteCreate(BaseModel):
    item_id: str
    category: str

class Favorite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    category: str
    name: str
    name_ar: str
    year: Optional[int] = None
    genre: Optional[str] = None
    external_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Large database of real entertainment items
# Helper function to generate external URLs
def get_external_url(name: str, category: str) -> str:
    encoded_name = name.replace(" ", "+")
    if category == "games":
        return f"https://www.google.com/search?q={encoded_name}+game"
    elif category == "movies":
        return f"https://www.imdb.com/find/?q={encoded_name}"
    elif category == "series":
        return f"https://www.imdb.com/find/?q={encoded_name}+tv+series"
    elif category == "youtube":
        return f"https://www.youtube.com/results?search_query={encoded_name}"
    return f"https://www.google.com/search?q={encoded_name}"

ENTERTAINMENT_DATA = {
    "games": [
        {"name": "The Legend of Zelda: Breath of the Wild", "name_ar": "أسطورة زيلدا: نفس البرية", "year": 2017, "genre": "مغامرات"},
        {"name": "Red Dead Redemption 2", "name_ar": "ريد ديد ريدمبشن 2", "year": 2018, "genre": "أكشن/مغامرات"},
        {"name": "God of War", "name_ar": "إله الحرب", "year": 2018, "genre": "أكشن/مغامرات"},
        {"name": "The Witcher 3: Wild Hunt", "name_ar": "الساحر 3: الصيد البري", "year": 2015, "genre": "RPG"},
        {"name": "Elden Ring", "name_ar": "إلدن رينج", "year": 2022, "genre": "RPG/أكشن"},
        {"name": "Grand Theft Auto V", "name_ar": "جراند ثفت أوتو 5", "year": 2013, "genre": "أكشن/مغامرات"},
        {"name": "Minecraft", "name_ar": "ماينكرافت", "year": 2011, "genre": "بناء/مغامرات"},
        {"name": "Fortnite", "name_ar": "فورتنايت", "year": 2017, "genre": "باتل رويال"},
        {"name": "Call of Duty: Warzone", "name_ar": "كول أوف ديوتي: وارزون", "year": 2020, "genre": "باتل رويال/FPS"},
        {"name": "FIFA 24", "name_ar": "فيفا 24", "year": 2023, "genre": "رياضة"},
        {"name": "Hogwarts Legacy", "name_ar": "إرث هوجوورتس", "year": 2023, "genre": "RPG/مغامرات"},
        {"name": "Spider-Man 2", "name_ar": "سبايدرمان 2", "year": 2023, "genre": "أكشن/مغامرات"},
        {"name": "Baldur's Gate 3", "name_ar": "بوابة بالدور 3", "year": 2023, "genre": "RPG"},
        {"name": "Cyberpunk 2077", "name_ar": "سايبربانك 2077", "year": 2020, "genre": "RPG/أكشن"},
        {"name": "Horizon Forbidden West", "name_ar": "هورايزن فوربيدن ويست", "year": 2022, "genre": "أكشن/مغامرات"},
        {"name": "Ghost of Tsushima", "name_ar": "شبح تسوشيما", "year": 2020, "genre": "أكشن/مغامرات"},
        {"name": "Sekiro: Shadows Die Twice", "name_ar": "سيكيرو: الظلال تموت مرتين", "year": 2019, "genre": "أكشن/مغامرات"},
        {"name": "Hades", "name_ar": "هاديس", "year": 2020, "genre": "روجلايك/أكشن"},
        {"name": "Stardew Valley", "name_ar": "ستاردو فالي", "year": 2016, "genre": "محاكاة/زراعة"},
        {"name": "Among Us", "name_ar": "أمونج أس", "year": 2018, "genre": "اجتماعية/خداع"},
        {"name": "Valorant", "name_ar": "فالورانت", "year": 2020, "genre": "FPS/تكتيكية"},
        {"name": "League of Legends", "name_ar": "ليج أوف ليجندز", "year": 2009, "genre": "MOBA"},
        {"name": "Apex Legends", "name_ar": "أبيكس ليجندز", "year": 2019, "genre": "باتل رويال"},
        {"name": "Overwatch 2", "name_ar": "أوفرواتش 2", "year": 2022, "genre": "FPS/فريقي"},
        {"name": "The Last of Us Part II", "name_ar": "ذا لاست أوف أس الجزء 2", "year": 2020, "genre": "أكشن/مغامرات"},
        {"name": "Animal Crossing: New Horizons", "name_ar": "أنيمال كروسينج: نيو هورايزنز", "year": 2020, "genre": "محاكاة"},
        {"name": "Dark Souls III", "name_ar": "دارك سولز 3", "year": 2016, "genre": "RPG/أكشن"},
        {"name": "Resident Evil Village", "name_ar": "ريزدنت إيفل فيليج", "year": 2021, "genre": "رعب/أكشن"},
        {"name": "Final Fantasy XVI", "name_ar": "فاينال فانتسي 16", "year": 2023, "genre": "RPG/أكشن"},
        {"name": "Diablo IV", "name_ar": "ديابلو 4", "year": 2023, "genre": "RPG/أكشن"},
        {"name": "Monster Hunter: World", "name_ar": "مونستر هنتر: وورلد", "year": 2018, "genre": "أكشن/RPG"},
        {"name": "Persona 5 Royal", "name_ar": "بيرسونا 5 رويال", "year": 2020, "genre": "RPG"},
        {"name": "Death Stranding", "name_ar": "ديث ستراندينج", "year": 2019, "genre": "أكشن/مغامرات"},
        {"name": "Control", "name_ar": "كونترول", "year": 2019, "genre": "أكشن/مغامرات"},
        {"name": "It Takes Two", "name_ar": "إت تيكس تو", "year": 2021, "genre": "مغامرات/تعاوني"},
        {"name": "Hollow Knight", "name_ar": "هولو نايت", "year": 2017, "genre": "ميتروديفانيا"},
        {"name": "Celeste", "name_ar": "سيليست", "year": 2018, "genre": "منصات"},
        {"name": "Terraria", "name_ar": "تيراريا", "year": 2011, "genre": "بناء/مغامرات"},
        {"name": "Rocket League", "name_ar": "روكت ليج", "year": 2015, "genre": "رياضة/سيارات"},
        {"name": "Subnautica", "name_ar": "سابنوتيكا", "year": 2018, "genre": "مغامرات/بقاء"},
        {"name": "Dead Cells", "name_ar": "ديد سيلز", "year": 2018, "genre": "روجلايك/أكشن"},
        {"name": "Ori and the Will of the Wisps", "name_ar": "أوري وإرادة الأشباح", "year": 2020, "genre": "منصات/مغامرات"},
        {"name": "Disco Elysium", "name_ar": "ديسكو إليسيوم", "year": 2019, "genre": "RPG"},
        {"name": "Halo Infinite", "name_ar": "هالو إنفينيت", "year": 2021, "genre": "FPS"},
        {"name": "Genshin Impact", "name_ar": "جينشن إمباكت", "year": 2020, "genre": "RPG/أكشن"},
        {"name": "Sea of Thieves", "name_ar": "سي أوف ثيفز", "year": 2018, "genre": "مغامرات/متعدد"},
        {"name": "No Man's Sky", "name_ar": "نو مانز سكاي", "year": 2016, "genre": "استكشاف/بقاء"},
        {"name": "Destiny 2", "name_ar": "ديستني 2", "year": 2017, "genre": "FPS/MMO"},
        {"name": "Doom Eternal", "name_ar": "دوم إيترنال", "year": 2020, "genre": "FPS"},
        {"name": "Ratchet & Clank: Rift Apart", "name_ar": "راتشت وكلانك: ريفت أبارت", "year": 2021, "genre": "أكشن/منصات"},
        {"name": "Returnal", "name_ar": "ريترنال", "year": 2021, "genre": "روجلايك/TPS"},
        {"name": "Deathloop", "name_ar": "ديثلوب", "year": 2021, "genre": "أكشن/FPS"},
        {"name": "Psychonauts 2", "name_ar": "سايكونوتس 2", "year": 2021, "genre": "منصات/مغامرات"},
        {"name": "Metroid Dread", "name_ar": "ميترويد دريد", "year": 2021, "genre": "ميتروديفانيا"},
        {"name": "Tales of Arise", "name_ar": "تيلز أوف أرايز", "year": 2021, "genre": "RPG"},
        {"name": "Guilty Gear Strive", "name_ar": "جيلتي جير سترايف", "year": 2021, "genre": "قتال"},
        {"name": "Street Fighter 6", "name_ar": "ستريت فايتر 6", "year": 2023, "genre": "قتال"},
        {"name": "Mortal Kombat 1", "name_ar": "مورتال كومبات 1", "year": 2023, "genre": "قتال"},
        {"name": "Tekken 8", "name_ar": "تيكن 8", "year": 2024, "genre": "قتال"},
        {"name": "Palworld", "name_ar": "بال وورلد", "year": 2024, "genre": "بقاء/مغامرات"},
        {"name": "Lethal Company", "name_ar": "ليثال كومباني", "year": 2023, "genre": "رعب/تعاوني"},
        {"name": "Alan Wake 2", "name_ar": "آلان ويك 2", "year": 2023, "genre": "رعب/أكشن"},
        {"name": "Lies of P", "name_ar": "أكاذيب بي", "year": 2023, "genre": "RPG/أكشن"},
        {"name": "Starfield", "name_ar": "ستارفيلد", "year": 2023, "genre": "RPG/فضاء"},
        {"name": "Armored Core VI", "name_ar": "أرمورد كور 6", "year": 2023, "genre": "أكشن/ميكا"},
        {"name": "Remnant 2", "name_ar": "ريمنانت 2", "year": 2023, "genre": "أكشن/RPG"},
        {"name": "Dave the Diver", "name_ar": "ديف الغواص", "year": 2023, "genre": "مغامرات/محاكاة"},
        {"name": "Pikmin 4", "name_ar": "بيكمين 4", "year": 2023, "genre": "استراتيجية/مغامرات"},
        {"name": "Super Mario Bros. Wonder", "name_ar": "سوبر ماريو برذرز وندر", "year": 2023, "genre": "منصات"},
        {"name": "The Legend of Zelda: Tears of the Kingdom", "name_ar": "زيلدا: دموع المملكة", "year": 2023, "genre": "مغامرات"},
        {"name": "Assassin's Creed Mirage", "name_ar": "أساسنز كريد ميراج", "year": 2023, "genre": "أكشن/مغامرات"},
        {"name": "Lords of the Fallen", "name_ar": "لوردز أوف ذا فولن", "year": 2023, "genre": "RPG/أكشن"},
        {"name": "Cocoon", "name_ar": "كوكون", "year": 2023, "genre": "ألغاز/مغامرات"},
        {"name": "Sea of Stars", "name_ar": "سي أوف ستارز", "year": 2023, "genre": "RPG"},
        {"name": "Splatoon 3", "name_ar": "سبلاتون 3", "year": 2022, "genre": "TPS/متعدد"},
        {"name": "Xenoblade Chronicles 3", "name_ar": "زينوبليد كرونيكلز 3", "year": 2022, "genre": "RPG"},
        {"name": "Sifu", "name_ar": "سيفو", "year": 2022, "genre": "أكشن/قتال"},
        {"name": "Cult of the Lamb", "name_ar": "كلت أوف ذا لامب", "year": 2022, "genre": "روجلايك/محاكاة"},
        {"name": "Stray", "name_ar": "ستراي", "year": 2022, "genre": "مغامرات"},
        {"name": "Neon White", "name_ar": "نيون وايت", "year": 2022, "genre": "أكشن/FPS"},
        {"name": "Vampire Survivors", "name_ar": "فامباير سيرفايفرز", "year": 2022, "genre": "روجلايك"},
        {"name": "Pokemon Scarlet and Violet", "name_ar": "بوكيمون سكارليت وفايولت", "year": 2022, "genre": "RPG"},
        {"name": "A Plague Tale: Requiem", "name_ar": "قصة طاعون: ريكويم", "year": 2022, "genre": "مغامرات"},
        {"name": "God of War Ragnarök", "name_ar": "إله الحرب راجناروك", "year": 2022, "genre": "أكشن/مغامرات"},
        {"name": "Call of Duty: Modern Warfare II", "name_ar": "كول أوف ديوتي: مودرن وورفير 2", "year": 2022, "genre": "FPS"},
        {"name": "Gran Turismo 7", "name_ar": "جران توريزمو 7", "year": 2022, "genre": "سباق"},
        {"name": "PUBG: BATTLEGROUNDS", "name_ar": "ببجي", "year": 2017, "genre": "باتل رويال"},
        {"name": "Dota 2", "name_ar": "دوتا 2", "year": 2013, "genre": "MOBA"},
        {"name": "Counter-Strike 2", "name_ar": "كاونتر سترايك 2", "year": 2023, "genre": "FPS"},
        {"name": "World of Warcraft", "name_ar": "وورلد أوف ووركرافت", "year": 2004, "genre": "MMORPG"},
        {"name": "Path of Exile", "name_ar": "باث أوف إكزايل", "year": 2013, "genre": "RPG/أكشن"},
        {"name": "Escape from Tarkov", "name_ar": "إسكيب فروم تاركوف", "year": 2017, "genre": "FPS/بقاء"},
        {"name": "Rust", "name_ar": "رست", "year": 2018, "genre": "بقاء/متعدد"},
        {"name": "ARK: Survival Evolved", "name_ar": "آرك: سيرفايفل إيفولفد", "year": 2017, "genre": "بقاء/مغامرات"},
        {"name": "The Forest", "name_ar": "ذا فورست", "year": 2018, "genre": "بقاء/رعب"},
        {"name": "Sons of the Forest", "name_ar": "أبناء الغابة", "year": 2023, "genre": "بقاء/رعب"},
        {"name": "Phasmophobia", "name_ar": "فازموفوبيا", "year": 2020, "genre": "رعب/تعاوني"},
        {"name": "Dead by Daylight", "name_ar": "ديد باي دايلايت", "year": 2016, "genre": "رعب/متعدد"},
        {"name": "Fall Guys", "name_ar": "فول جايز", "year": 2020, "genre": "حفلة/باتل رويال"},
        {"name": "Stumble Guys", "name_ar": "ستمبل جايز", "year": 2021, "genre": "حفلة/باتل رويال"},
    ],
    "movies": [
        {"name": "The Shawshank Redemption", "name_ar": "الخلاص من شاوشانك", "year": 1994, "genre": "دراما"},
        {"name": "The Godfather", "name_ar": "العراب", "year": 1972, "genre": "جريمة/دراما"},
        {"name": "The Dark Knight", "name_ar": "فارس الظلام", "year": 2008, "genre": "أكشن/جريمة"},
        {"name": "Pulp Fiction", "name_ar": "خيال رخيص", "year": 1994, "genre": "جريمة/دراما"},
        {"name": "Fight Club", "name_ar": "نادي القتال", "year": 1999, "genre": "دراما"},
        {"name": "Inception", "name_ar": "استهلال", "year": 2010, "genre": "خيال علمي/أكشن"},
        {"name": "The Matrix", "name_ar": "ذا ماتريكس", "year": 1999, "genre": "خيال علمي/أكشن"},
        {"name": "Interstellar", "name_ar": "بين النجوم", "year": 2014, "genre": "خيال علمي/دراما"},
        {"name": "Forrest Gump", "name_ar": "فورست جامب", "year": 1994, "genre": "دراما/رومانسي"},
        {"name": "The Lord of the Rings: The Fellowship of the Ring", "name_ar": "سيد الخواتم: رفقة الخاتم", "year": 2001, "genre": "فانتازيا/مغامرات"},
        {"name": "The Lord of the Rings: The Two Towers", "name_ar": "سيد الخواتم: البرجان", "year": 2002, "genre": "فانتازيا/مغامرات"},
        {"name": "The Lord of the Rings: Return of the King", "name_ar": "سيد الخواتم: عودة الملك", "year": 2003, "genre": "فانتازيا/مغامرات"},
        {"name": "Star Wars: A New Hope", "name_ar": "حرب النجوم: أمل جديد", "year": 1977, "genre": "خيال علمي/مغامرات"},
        {"name": "Star Wars: The Empire Strikes Back", "name_ar": "حرب النجوم: الإمبراطورية ترد", "year": 1980, "genre": "خيال علمي/مغامرات"},
        {"name": "Gladiator", "name_ar": "المصارع", "year": 2000, "genre": "أكشن/دراما"},
        {"name": "The Prestige", "name_ar": "الهيبة", "year": 2006, "genre": "غموض/دراما"},
        {"name": "Memento", "name_ar": "تذكار", "year": 2000, "genre": "غموض/إثارة"},
        {"name": "Se7en", "name_ar": "سبعة", "year": 1995, "genre": "جريمة/غموض"},
        {"name": "The Silence of the Lambs", "name_ar": "صمت الحملان", "year": 1991, "genre": "إثارة/جريمة"},
        {"name": "Schindler's List", "name_ar": "قائمة شندلر", "year": 1993, "genre": "تاريخي/دراما"},
        {"name": "Saving Private Ryan", "name_ar": "إنقاذ الجندي رايان", "year": 1998, "genre": "حرب/دراما"},
        {"name": "The Green Mile", "name_ar": "الميل الأخضر", "year": 1999, "genre": "دراما/فانتازيا"},
        {"name": "Goodfellas", "name_ar": "رفاق طيبون", "year": 1990, "genre": "جريمة/دراما"},
        {"name": "The Departed", "name_ar": "المغادرون", "year": 2006, "genre": "جريمة/إثارة"},
        {"name": "Django Unchained", "name_ar": "جانغو طليقًا", "year": 2012, "genre": "ويسترن/دراما"},
        {"name": "Inglourious Basterds", "name_ar": "أوغاد مجهولون", "year": 2009, "genre": "حرب/دراما"},
        {"name": "The Wolf of Wall Street", "name_ar": "ذئب وول ستريت", "year": 2013, "genre": "سيرة/كوميديا"},
        {"name": "Joker", "name_ar": "الجوكر", "year": 2019, "genre": "جريمة/دراما"},
        {"name": "Parasite", "name_ar": "طفيلي", "year": 2019, "genre": "إثارة/دراما"},
        {"name": "Whiplash", "name_ar": "ويبلاش", "year": 2014, "genre": "دراما/موسيقى"},
        {"name": "The Social Network", "name_ar": "الشبكة الاجتماعية", "year": 2010, "genre": "دراما/سيرة"},
        {"name": "Shutter Island", "name_ar": "جزيرة شاتر", "year": 2010, "genre": "غموض/إثارة"},
        {"name": "Gone Girl", "name_ar": "الفتاة المفقودة", "year": 2014, "genre": "غموض/إثارة"},
        {"name": "The Revenant", "name_ar": "العائد", "year": 2015, "genre": "مغامرات/دراما"},
        {"name": "Mad Max: Fury Road", "name_ar": "ماد ماكس: طريق الغضب", "year": 2015, "genre": "أكشن/مغامرات"},
        {"name": "John Wick", "name_ar": "جون ويك", "year": 2014, "genre": "أكشن/إثارة"},
        {"name": "John Wick: Chapter 4", "name_ar": "جون ويك: الفصل 4", "year": 2023, "genre": "أكشن/إثارة"},
        {"name": "Avengers: Endgame", "name_ar": "أفنجرز: نهاية اللعبة", "year": 2019, "genre": "أكشن/خيال علمي"},
        {"name": "Avengers: Infinity War", "name_ar": "أفنجرز: حرب اللانهاية", "year": 2018, "genre": "أكشن/خيال علمي"},
        {"name": "Spider-Man: No Way Home", "name_ar": "سبايدرمان: لا طريق للوطن", "year": 2021, "genre": "أكشن/مغامرات"},
        {"name": "Black Panther", "name_ar": "النمر الأسود", "year": 2018, "genre": "أكشن/خيال علمي"},
        {"name": "Guardians of the Galaxy", "name_ar": "حراس المجرة", "year": 2014, "genre": "أكشن/كوميدي"},
        {"name": "Iron Man", "name_ar": "الرجل الحديدي", "year": 2008, "genre": "أكشن/خيال علمي"},
        {"name": "Thor: Ragnarok", "name_ar": "ثور: راجناروك", "year": 2017, "genre": "أكشن/كوميدي"},
        {"name": "Captain America: The Winter Soldier", "name_ar": "كابتن أمريكا: جندي الشتاء", "year": 2014, "genre": "أكشن/خيال علمي"},
        {"name": "The Batman", "name_ar": "باتمان", "year": 2022, "genre": "أكشن/جريمة"},
        {"name": "Dune", "name_ar": "كثيب", "year": 2021, "genre": "خيال علمي/مغامرات"},
        {"name": "Dune: Part Two", "name_ar": "كثيب: الجزء الثاني", "year": 2024, "genre": "خيال علمي/مغامرات"},
        {"name": "Oppenheimer", "name_ar": "أوبنهايمر", "year": 2023, "genre": "سيرة/تاريخي"},
        {"name": "Barbie", "name_ar": "باربي", "year": 2023, "genre": "كوميدي/فانتازيا"},
        {"name": "Everything Everywhere All at Once", "name_ar": "كل شيء في كل مكان دفعة واحدة", "year": 2022, "genre": "خيال علمي/كوميدي"},
        {"name": "Top Gun: Maverick", "name_ar": "توب غان: مافريك", "year": 2022, "genre": "أكشن/دراما"},
        {"name": "The Northman", "name_ar": "الشمالي", "year": 2022, "genre": "أكشن/مغامرات"},
        {"name": "Avatar: The Way of Water", "name_ar": "أفاتار: طريق الماء", "year": 2022, "genre": "خيال علمي/مغامرات"},
        {"name": "Avatar", "name_ar": "أفاتار", "year": 2009, "genre": "خيال علمي/مغامرات"},
        {"name": "Titanic", "name_ar": "تايتانيك", "year": 1997, "genre": "رومانسي/دراما"},
        {"name": "The Lion King", "name_ar": "الأسد الملك", "year": 1994, "genre": "رسوم متحركة/مغامرات"},
        {"name": "Spirited Away", "name_ar": "المخطوفة", "year": 2001, "genre": "رسوم متحركة/فانتازيا"},
        {"name": "Your Name", "name_ar": "اسمك", "year": 2016, "genre": "رسوم متحركة/رومانسي"},
        {"name": "Demon Slayer: Mugen Train", "name_ar": "قاتل الشياطين: قطار موغين", "year": 2020, "genre": "رسوم متحركة/أكشن"},
        {"name": "A Silent Voice", "name_ar": "صوت صامت", "year": 2016, "genre": "رسوم متحركة/دراما"},
        {"name": "Princess Mononoke", "name_ar": "الأميرة مونونوكي", "year": 1997, "genre": "رسوم متحركة/فانتازيا"},
        {"name": "Howl's Moving Castle", "name_ar": "قلعة هاول المتحركة", "year": 2004, "genre": "رسوم متحركة/فانتازيا"},
        {"name": "Akira", "name_ar": "أكيرا", "year": 1988, "genre": "رسوم متحركة/خيال علمي"},
        {"name": "Ghost in the Shell", "name_ar": "الشبح في الصدفة", "year": 1995, "genre": "رسوم متحركة/خيال علمي"},
        {"name": "Blade Runner 2049", "name_ar": "بليد رنر 2049", "year": 2017, "genre": "خيال علمي/إثارة"},
        {"name": "Arrival", "name_ar": "الوصول", "year": 2016, "genre": "خيال علمي/دراما"},
        {"name": "Ex Machina", "name_ar": "إكس ماكينا", "year": 2014, "genre": "خيال علمي/إثارة"},
        {"name": "Her", "name_ar": "هي", "year": 2013, "genre": "خيال علمي/رومانسي"},
        {"name": "Gravity", "name_ar": "جاذبية", "year": 2013, "genre": "خيال علمي/إثارة"},
        {"name": "The Martian", "name_ar": "المريخي", "year": 2015, "genre": "خيال علمي/مغامرات"},
        {"name": "Edge of Tomorrow", "name_ar": "حافة الغد", "year": 2014, "genre": "خيال علمي/أكشن"},
        {"name": "Get Out", "name_ar": "اخرج", "year": 2017, "genre": "رعب/إثارة"},
        {"name": "Us", "name_ar": "نحن", "year": 2019, "genre": "رعب/إثارة"},
        {"name": "A Quiet Place", "name_ar": "مكان هادئ", "year": 2018, "genre": "رعب/إثارة"},
        {"name": "Hereditary", "name_ar": "وراثي", "year": 2018, "genre": "رعب/دراما"},
        {"name": "Midsommar", "name_ar": "منتصف الصيف", "year": 2019, "genre": "رعب/دراما"},
        {"name": "The Conjuring", "name_ar": "الشعوذة", "year": 2013, "genre": "رعب"},
        {"name": "It", "name_ar": "إنه", "year": 2017, "genre": "رعب"},
        {"name": "The Exorcist", "name_ar": "طارد الأرواح", "year": 1973, "genre": "رعب"},
        {"name": "The Shining", "name_ar": "البريق", "year": 1980, "genre": "رعب"},
        {"name": "Psycho", "name_ar": "سايكو", "year": 1960, "genre": "رعب/إثارة"},
        {"name": "The Grand Budapest Hotel", "name_ar": "فندق بودابست الكبير", "year": 2014, "genre": "كوميدي/دراما"},
        {"name": "The Royal Tenenbaums", "name_ar": "عائلة تينينباوم الملكية", "year": 2001, "genre": "كوميدي/دراما"},
        {"name": "Moonrise Kingdom", "name_ar": "مملكة ضوء القمر", "year": 2012, "genre": "كوميدي/رومانسي"},
        {"name": "La La Land", "name_ar": "لا لا لاند", "year": 2016, "genre": "موسيقي/رومانسي"},
        {"name": "1917", "name_ar": "1917", "year": 2019, "genre": "حرب/دراما"},
        {"name": "Dunkirk", "name_ar": "دنكيرك", "year": 2017, "genre": "حرب/أكشن"},
        {"name": "Hacksaw Ridge", "name_ar": "نتوء منشار", "year": 2016, "genre": "حرب/دراما"},
        {"name": "No Country for Old Men", "name_ar": "لا بلد للعجائز", "year": 2007, "genre": "جريمة/إثارة"},
        {"name": "There Will Be Blood", "name_ar": "سيكون هناك دم", "year": 2007, "genre": "دراما"},
        {"name": "12 Years a Slave", "name_ar": "12 سنة عبداً", "year": 2013, "genre": "تاريخي/دراما"},
        {"name": "The Truman Show", "name_ar": "عرض ترومان", "year": 1998, "genre": "كوميدي/دراما"},
        {"name": "Eternal Sunshine of the Spotless Mind", "name_ar": "إشراقة أبدية لعقل نظيف", "year": 2004, "genre": "رومانسي/خيال علمي"},
        {"name": "Oldboy", "name_ar": "أولدبوي", "year": 2003, "genre": "أكشن/إثارة"},
        {"name": "The Handmaiden", "name_ar": "الخادمة", "year": 2016, "genre": "إثارة/رومانسي"},
        {"name": "Train to Busan", "name_ar": "قطار إلى بوسان", "year": 2016, "genre": "أكشن/رعب"},
        {"name": "Memories of Murder", "name_ar": "ذكريات جريمة", "year": 2003, "genre": "جريمة/دراما"},
        {"name": "Killers of the Flower Moon", "name_ar": "قتلة قمر الزهرة", "year": 2023, "genre": "جريمة/دراما"},
        {"name": "Poor Things", "name_ar": "أشياء مسكينة", "year": 2023, "genre": "كوميدي/دراما"},
        {"name": "The Holdovers", "name_ar": "المتبقون", "year": 2023, "genre": "كوميدي/دراما"},
    ],
    "series": [
        {"name": "Breaking Bad", "name_ar": "بريكنج باد", "year": 2008, "genre": "جريمة/دراما"},
        {"name": "Game of Thrones", "name_ar": "صراع العروش", "year": 2011, "genre": "فانتازيا/دراما"},
        {"name": "The Wire", "name_ar": "السلك", "year": 2002, "genre": "جريمة/دراما"},
        {"name": "The Sopranos", "name_ar": "عائلة سوبرانو", "year": 1999, "genre": "جريمة/دراما"},
        {"name": "Friends", "name_ar": "فريندز", "year": 1994, "genre": "كوميدي"},
        {"name": "The Office", "name_ar": "المكتب", "year": 2005, "genre": "كوميدي"},
        {"name": "Stranger Things", "name_ar": "أشياء غريبة", "year": 2016, "genre": "خيال علمي/رعب"},
        {"name": "The Crown", "name_ar": "التاج", "year": 2016, "genre": "تاريخي/دراما"},
        {"name": "Chernobyl", "name_ar": "تشيرنوبل", "year": 2019, "genre": "تاريخي/دراما"},
        {"name": "True Detective", "name_ar": "المحقق الحقيقي", "year": 2014, "genre": "جريمة/دراما"},
        {"name": "Sherlock", "name_ar": "شيرلوك", "year": 2010, "genre": "جريمة/دراما"},
        {"name": "Black Mirror", "name_ar": "المرآة السوداء", "year": 2011, "genre": "خيال علمي/إثارة"},
        {"name": "Money Heist", "name_ar": "البروفيسور", "year": 2017, "genre": "جريمة/أكشن"},
        {"name": "Narcos", "name_ar": "ناركوس", "year": 2015, "genre": "جريمة/دراما"},
        {"name": "Peaky Blinders", "name_ar": "بيكي بلايندرز", "year": 2013, "genre": "جريمة/دراما"},
        {"name": "The Mandalorian", "name_ar": "الماندالوريان", "year": 2019, "genre": "خيال علمي/أكشن"},
        {"name": "The Witcher", "name_ar": "الساحر", "year": 2019, "genre": "فانتازيا/أكشن"},
        {"name": "Squid Game", "name_ar": "لعبة الحبار", "year": 2021, "genre": "إثارة/دراما"},
        {"name": "Succession", "name_ar": "الخلافة", "year": 2018, "genre": "دراما"},
        {"name": "House of the Dragon", "name_ar": "بيت التنين", "year": 2022, "genre": "فانتازيا/دراما"},
        {"name": "The Last of Us", "name_ar": "ذا لاست أوف أس", "year": 2023, "genre": "دراما/أكشن"},
        {"name": "The Boys", "name_ar": "ذا بويز", "year": 2019, "genre": "أكشن/كوميدي"},
        {"name": "Arcane", "name_ar": "أركين", "year": 2021, "genre": "رسوم متحركة/أكشن"},
        {"name": "Attack on Titan", "name_ar": "هجوم العمالقة", "year": 2013, "genre": "أنمي/أكشن"},
        {"name": "Death Note", "name_ar": "مذكرة الموت", "year": 2006, "genre": "أنمي/إثارة"},
        {"name": "Fullmetal Alchemist: Brotherhood", "name_ar": "الخيميائي المعدني", "year": 2009, "genre": "أنمي/أكشن"},
        {"name": "One Piece", "name_ar": "ون بيس", "year": 1999, "genre": "أنمي/مغامرات"},
        {"name": "Naruto Shippuden", "name_ar": "ناروتو شيبودن", "year": 2007, "genre": "أنمي/أكشن"},
        {"name": "Demon Slayer", "name_ar": "قاتل الشياطين", "year": 2019, "genre": "أنمي/أكشن"},
        {"name": "Jujutsu Kaisen", "name_ar": "جوجوتسو كايسن", "year": 2020, "genre": "أنمي/أكشن"},
        {"name": "Hunter x Hunter", "name_ar": "القناص", "year": 2011, "genre": "أنمي/مغامرات"},
        {"name": "My Hero Academia", "name_ar": "أكاديمية بطلي", "year": 2016, "genre": "أنمي/أكشن"},
        {"name": "Steins;Gate", "name_ar": "ستاينز جيت", "year": 2011, "genre": "أنمي/خيال علمي"},
        {"name": "Cowboy Bebop", "name_ar": "كاوبوي بيبوب", "year": 1998, "genre": "أنمي/خيال علمي"},
        {"name": "Neon Genesis Evangelion", "name_ar": "نيون جينيسيس إيفانجيليون", "year": 1995, "genre": "أنمي/ميكا"},
        {"name": "Vinland Saga", "name_ar": "فينلاند ساجا", "year": 2019, "genre": "أنمي/أكشن"},
        {"name": "Spy x Family", "name_ar": "سباي × فاميلي", "year": 2022, "genre": "أنمي/كوميدي"},
        {"name": "Chainsaw Man", "name_ar": "رجل المنشار", "year": 2022, "genre": "أنمي/أكشن"},
        {"name": "The Walking Dead", "name_ar": "الموتى السائرون", "year": 2010, "genre": "رعب/دراما"},
        {"name": "Better Call Saul", "name_ar": "اتصل بسول", "year": 2015, "genre": "جريمة/دراما"},
        {"name": "Ozark", "name_ar": "أوزارك", "year": 2017, "genre": "جريمة/دراما"},
        {"name": "Mindhunter", "name_ar": "صائد العقول", "year": 2017, "genre": "جريمة/إثارة"},
        {"name": "Fargo", "name_ar": "فارجو", "year": 2014, "genre": "جريمة/دراما"},
        {"name": "Mr. Robot", "name_ar": "مستر روبوت", "year": 2015, "genre": "إثارة/دراما"},
        {"name": "Westworld", "name_ar": "عالم الغرب", "year": 2016, "genre": "خيال علمي/ويسترن"},
        {"name": "Dark", "name_ar": "دارك", "year": 2017, "genre": "خيال علمي/إثارة"},
        {"name": "The Haunting of Hill House", "name_ar": "منزل التل المسكون", "year": 2018, "genre": "رعب/دراما"},
        {"name": "Wednesday", "name_ar": "ويدنزداي", "year": 2022, "genre": "كوميدي/غموض"},
        {"name": "The Umbrella Academy", "name_ar": "أكاديمية المظلة", "year": 2019, "genre": "أكشن/خيال علمي"},
        {"name": "Loki", "name_ar": "لوكي", "year": 2021, "genre": "أكشن/خيال علمي"},
        {"name": "WandaVision", "name_ar": "واندا فيجن", "year": 2021, "genre": "أكشن/كوميدي"},
        {"name": "Andor", "name_ar": "أندور", "year": 2022, "genre": "خيال علمي/أكشن"},
        {"name": "The Bear", "name_ar": "الدب", "year": 2022, "genre": "دراما/كوميدي"},
        {"name": "Severance", "name_ar": "سيفرنس", "year": 2022, "genre": "خيال علمي/إثارة"},
        {"name": "Yellowstone", "name_ar": "يلوستون", "year": 2018, "genre": "ويسترن/دراما"},
        {"name": "Ted Lasso", "name_ar": "تيد لاسو", "year": 2020, "genre": "كوميدي/دراما"},
        {"name": "The White Lotus", "name_ar": "اللوتس الأبيض", "year": 2021, "genre": "دراما/كوميدي"},
        {"name": "Euphoria", "name_ar": "يوفوريا", "year": 2019, "genre": "دراما"},
        {"name": "Fleabag", "name_ar": "فليباج", "year": 2016, "genre": "كوميدي/دراما"},
        {"name": "Atlanta", "name_ar": "أتلانتا", "year": 2016, "genre": "كوميدي/دراما"},
        {"name": "Barry", "name_ar": "باري", "year": 2018, "genre": "كوميدي/جريمة"},
        {"name": "What We Do in the Shadows", "name_ar": "ما نفعله في الظل", "year": 2019, "genre": "كوميدي/رعب"},
        {"name": "Only Murders in the Building", "name_ar": "جرائم في المبنى فقط", "year": 2021, "genre": "كوميدي/غموض"},
        {"name": "Invincible", "name_ar": "لا يُقهر", "year": 2021, "genre": "رسوم متحركة/أكشن"},
        {"name": "The Wheel of Time", "name_ar": "عجلة الزمن", "year": 2021, "genre": "فانتازيا"},
        {"name": "Foundation", "name_ar": "الأساس", "year": 2021, "genre": "خيال علمي"},
        {"name": "Rings of Power", "name_ar": "حلقات القوة", "year": 2022, "genre": "فانتازيا"},
        {"name": "House of Cards", "name_ar": "بيت من ورق", "year": 2013, "genre": "دراما سياسية"},
        {"name": "Homeland", "name_ar": "الوطن", "year": 2011, "genre": "إثارة/دراما"},
        {"name": "24", "name_ar": "24", "year": 2001, "genre": "أكشن/إثارة"},
        {"name": "Lost", "name_ar": "لوست", "year": 2004, "genre": "مغامرات/دراما"},
        {"name": "Prison Break", "name_ar": "الهروب من السجن", "year": 2005, "genre": "أكشن/إثارة"},
        {"name": "Vikings", "name_ar": "الفايكنج", "year": 2013, "genre": "أكشن/تاريخي"},
        {"name": "The 100", "name_ar": "المائة", "year": 2014, "genre": "خيال علمي/دراما"},
        {"name": "Lucifer", "name_ar": "لوسيفر", "year": 2016, "genre": "فانتازيا/جريمة"},
        {"name": "The Good Place", "name_ar": "المكان الجيد", "year": 2016, "genre": "كوميدي/فانتازيا"},
        {"name": "Brooklyn Nine-Nine", "name_ar": "بروكلين ناين ناين", "year": 2013, "genre": "كوميدي"},
        {"name": "Parks and Recreation", "name_ar": "حدائق وترفيه", "year": 2009, "genre": "كوميدي"},
        {"name": "Community", "name_ar": "كومينيتي", "year": 2009, "genre": "كوميدي"},
        {"name": "How I Met Your Mother", "name_ar": "كيف قابلت أمكم", "year": 2005, "genre": "كوميدي/رومانسي"},
        {"name": "Seinfeld", "name_ar": "ساينفيلد", "year": 1989, "genre": "كوميدي"},
        {"name": "The Big Bang Theory", "name_ar": "نظرية الانفجار العظيم", "year": 2007, "genre": "كوميدي"},
        {"name": "Dexter", "name_ar": "ديكستر", "year": 2006, "genre": "جريمة/دراما"},
        {"name": "The Blacklist", "name_ar": "القائمة السوداء", "year": 2013, "genre": "جريمة/إثارة"},
        {"name": "Suits", "name_ar": "سوتس", "year": 2011, "genre": "دراما/قانوني"},
        {"name": "Billions", "name_ar": "بيليونز", "year": 2016, "genre": "دراما"},
        {"name": "The Morning Show", "name_ar": "برنامج الصباح", "year": 2019, "genre": "دراما"},
        {"name": "Shogun", "name_ar": "شوغن", "year": 2024, "genre": "تاريخي/دراما"},
        {"name": "Fallout", "name_ar": "فولاوت", "year": 2024, "genre": "خيال علمي/أكشن"},
        {"name": "3 Body Problem", "name_ar": "مشكلة الأجسام الثلاثة", "year": 2024, "genre": "خيال علمي"},
        {"name": "Baby Reindeer", "name_ar": "بيبي رينديير", "year": 2024, "genre": "دراما"},
        {"name": "The Gentlemen", "name_ar": "السادة", "year": 2024, "genre": "كوميدي/جريمة"},
        {"name": "Ripley", "name_ar": "ريبلي", "year": 2024, "genre": "إثارة/جريمة"},
        {"name": "Hacks", "name_ar": "هاكس", "year": 2021, "genre": "كوميدي/دراما"},
        {"name": "Slow Horses", "name_ar": "الخيول البطيئة", "year": 2022, "genre": "إثارة/تجسس"},
        {"name": "The Penguin", "name_ar": "البطريق", "year": 2024, "genre": "جريمة/دراما"},
        {"name": "Agatha All Along", "name_ar": "أجاثا طوال الوقت", "year": 2024, "genre": "فانتازيا/كوميدي"},
    ],
    "youtube": [
        {"name": "MrBeast", "name_ar": "مستر بيست - تحديات", "genre": "ترفيه/تحديات"},
        {"name": "PewDiePie", "name_ar": "بيوديباي - ألعاب وكوميديا", "genre": "ألعاب/ترفيه"},
        {"name": "Markiplier", "name_ar": "ماركيبلاير - ألعاب رعب", "genre": "ألعاب"},
        {"name": "Jacksepticeye", "name_ar": "جاكسبتيكاي - ألعاب وكوميديا", "genre": "ألعاب"},
        {"name": "Kurzgesagt", "name_ar": "كورزجيساجت - علوم مبسطة", "genre": "تعليمي"},
        {"name": "Veritasium", "name_ar": "فيريتاسيوم - علوم وتجارب", "genre": "تعليمي"},
        {"name": "Vsauce", "name_ar": "في سوس - أسئلة علمية غريبة", "genre": "تعليمي"},
        {"name": "Dude Perfect", "name_ar": "ديود بيرفكت - رياضة وتحديات", "genre": "رياضة/ترفيه"},
        {"name": "Linus Tech Tips", "name_ar": "لينوس تك تيبس - تقنية", "genre": "تقنية"},
        {"name": "MKBHD", "name_ar": "MKBHD - مراجعات تقنية", "genre": "تقنية"},
        {"name": "Casey Neistat", "name_ar": "كيسي نايستات - فلوجات", "genre": "فلوجات"},
        {"name": "Corridor Crew", "name_ar": "كوريدور كرو - مؤثرات بصرية", "genre": "أفلام/تقنية"},
        {"name": "JiDion", "name_ar": "جي ديون - كوميديا ومقالب", "genre": "كوميديا"},
        {"name": "IShowSpeed", "name_ar": "آي شو سبيد - ترفيه مباشر", "genre": "ترفيه"},
        {"name": "Kai Cenat", "name_ar": "كاي سينات - بث مباشر", "genre": "ترفيه"},
        {"name": "Sidemen", "name_ar": "سايدمن - تحديات جماعية", "genre": "ترفيه"},
        {"name": "Unbox Therapy", "name_ar": "أنبوكس ثيرابي - فتح صناديق", "genre": "تقنية"},
        {"name": "Numberphile", "name_ar": "نمبرفايل - رياضيات", "genre": "تعليمي"},
        {"name": "3Blue1Brown", "name_ar": "ثري بلو ون براون - رياضيات مرئية", "genre": "تعليمي"},
        {"name": "Oversimplified", "name_ar": "أوفرسمبلفايد - تاريخ مبسط", "genre": "تعليمي/تاريخ"},
        {"name": "History Matters", "name_ar": "هيستوري ماترز - تاريخ قصير", "genre": "تعليمي/تاريخ"},
        {"name": "CGP Grey", "name_ar": "سي جي بي جراي - شروحات", "genre": "تعليمي"},
        {"name": "SmarterEveryDay", "name_ar": "سمارتر إيفري داي - علوم", "genre": "تعليمي"},
        {"name": "Mark Rober", "name_ar": "مارك روبر - هندسة وتجارب", "genre": "تعليمي/ترفيه"},
        {"name": "The Slow Mo Guys", "name_ar": "ذا سلو مو جايز - حركة بطيئة", "genre": "ترفيه/علوم"},
        {"name": "Vox", "name_ar": "فوكس - شروحات وتحليلات", "genre": "تعليمي/أخبار"},
        {"name": "Johnny Harris", "name_ar": "جوني هاريس - جيوبوليتيك", "genre": "تعليمي"},
        {"name": "Wendover Productions", "name_ar": "وندوفر - شروحات متنوعة", "genre": "تعليمي"},
        {"name": "Half as Interesting", "name_ar": "هاف آز إنترستنج - حقائق قصيرة", "genre": "تعليمي"},
        {"name": "Real Engineering", "name_ar": "ريل إنجنيرنج - هندسة", "genre": "تعليمي"},
        {"name": "Tom Scott", "name_ar": "توم سكوت - أماكن ومعلومات", "genre": "تعليمي"},
        {"name": "Fireship", "name_ar": "فايرشيب - برمجة سريعة", "genre": "برمجة"},
        {"name": "NetworkChuck", "name_ar": "نتورك تشاك - شبكات وأمن", "genre": "تقنية"},
        {"name": "The Coding Train", "name_ar": "ذا كودنج ترين - برمجة إبداعية", "genre": "برمجة"},
        {"name": "Traversy Media", "name_ar": "ترافيرسي ميديا - تطوير ويب", "genre": "برمجة"},
        {"name": "freeCodeCamp", "name_ar": "فري كود كامب - دورات مجانية", "genre": "برمجة"},
        {"name": "GamesRadar", "name_ar": "جيمز رادار - أخبار ألعاب", "genre": "ألعاب"},
        {"name": "IGN", "name_ar": "آي جي إن - مراجعات ألعاب", "genre": "ألعاب"},
        {"name": "Gameranx", "name_ar": "جيمرانكس - أخبار ألعاب", "genre": "ألعاب"},
        {"name": "theRadBrad", "name_ar": "ذا راد براد - قصص ألعاب", "genre": "ألعاب"},
        {"name": "xQc", "name_ar": "إكس كيو سي - بث مباشر", "genre": "ترفيه"},
        {"name": "Ludwig", "name_ar": "لودفيج - ترفيه متنوع", "genre": "ترفيه"},
        {"name": "Jschlatt", "name_ar": "جيشلات - كوميديا", "genre": "كوميديا"},
        {"name": "Dream", "name_ar": "دريم - ماينكرافت", "genre": "ألعاب"},
        {"name": "GeorgeNotFound", "name_ar": "جورج نوت فاوند - ماينكرافت", "genre": "ألعاب"},
        {"name": "Technoblade", "name_ar": "تكنوبليد - ماينكرافت", "genre": "ألعاب"},
        {"name": "TommyInnit", "name_ar": "تومي إنيت - ماينكرافت", "genre": "ألعاب"},
        {"name": "Philza", "name_ar": "فيلزا - ماينكرافت هاردكور", "genre": "ألعاب"},
        {"name": "2kliksphilip", "name_ar": "تو كليكس فيليب - كاونتر سترايك", "genre": "ألعاب"},
        {"name": "penguinz0", "name_ar": "بينجوينز زيرو - مراجعات وكوميديا", "genre": "ترفيه"},
        {"name": "Dunkey", "name_ar": "دانكي - مراجعات ألعاب ساخرة", "genre": "ألعاب/كوميديا"},
        {"name": "Game Theory", "name_ar": "جيم ثيوري - نظريات ألعاب", "genre": "ألعاب/تعليمي"},
        {"name": "Film Theory", "name_ar": "فيلم ثيوري - نظريات أفلام", "genre": "أفلام/تعليمي"},
        {"name": "CinemaSins", "name_ar": "سينما سينز - أخطاء الأفلام", "genre": "أفلام"},
        {"name": "CinemaWins", "name_ar": "سينما وينز - محاسن الأفلام", "genre": "أفلام"},
        {"name": "Chris Stuckmann", "name_ar": "كريس ستكمان - مراجعات أفلام", "genre": "أفلام"},
        {"name": "Jeremy Jahns", "name_ar": "جيرمي جانز - مراجعات أفلام", "genre": "أفلام"},
        {"name": "Red Letter Media", "name_ar": "ريد ليتر ميديا - نقد أفلام", "genre": "أفلام"},
        {"name": "Corridor Digital", "name_ar": "كوريدور ديجيتال - أفلام قصيرة", "genre": "أفلام"},
        {"name": "Gigguk", "name_ar": "جيجوك - أنمي", "genre": "أنمي"},
        {"name": "Trash Taste", "name_ar": "تراش تيست - بودكاست", "genre": "بودكاست/أنمي"},
        {"name": "CDawgVA", "name_ar": "سي داوج - أنمي وتحديات", "genre": "ترفيه/أنمي"},
        {"name": "The Anime Man", "name_ar": "ذا أنمي مان - أنمي", "genre": "أنمي"},
        {"name": "Nux Taku", "name_ar": "نوكس تاكو - أنمي وميمز", "genre": "أنمي"},
        {"name": "NileRed", "name_ar": "نايل ريد - كيمياء", "genre": "تعليمي/علوم"},
        {"name": "ElectroBOOM", "name_ar": "إلكتروبوم - كهرباء وكوميديا", "genre": "تعليمي"},
        {"name": "Stuff Made Here", "name_ar": "ستف ميد هير - اختراعات", "genre": "هندسة"},
        {"name": "Michael Reeves", "name_ar": "مايكل ريفز - روبوتات مجنونة", "genre": "تقنية/كوميديا"},
        {"name": "William Osman", "name_ar": "ويليام عثمان - اختراعات فاشلة", "genre": "ترفيه/هندسة"},
        {"name": "Adam Savage's Tested", "name_ar": "آدم سافيج - صناعة وتجارب", "genre": "صناعة"},
        {"name": "Colin Furze", "name_ar": "كولين فيرز - اختراعات خطرة", "genre": "هندسة"},
        {"name": "Simone Giertz", "name_ar": "سيموني جيرتز - روبوتات فاشلة", "genre": "هندسة/كوميديا"},
        {"name": "I Did A Thing", "name_ar": "آي ديد أ ثينج - اختراعات غريبة", "genre": "ترفيه"},
        {"name": "JJ Olatunji", "name_ar": "كيه إس آي - ترفيه", "genre": "ترفيه"},
        {"name": "MrWhoseTheBoss", "name_ar": "مستر هوز ذا بوس - تقنية", "genre": "تقنية"},
        {"name": "Austin Evans", "name_ar": "أوستن إيفانز - تقنية", "genre": "تقنية"},
        {"name": "Dave2D", "name_ar": "ديف تو دي - مراجعات لابتوب", "genre": "تقنية"},
        {"name": "iJustine", "name_ar": "آي جستين - تقنية آبل", "genre": "تقنية"},
        {"name": "TechLinked", "name_ar": "تك لينكد - أخبار تقنية", "genre": "تقنية"},
        {"name": "JerryRigEverything", "name_ar": "جيري ريج - تفكيك أجهزة", "genre": "تقنية"},
        {"name": "Zack Nelson", "name_ar": "زاك نيلسون - اختبارات تحمل", "genre": "تقنية"},
        {"name": "Joshua Weissman", "name_ar": "جوشوا وايزمان - طبخ", "genre": "طبخ"},
        {"name": "Binging with Babish", "name_ar": "طبخ مع بابيش", "genre": "طبخ"},
        {"name": "Gordon Ramsay", "name_ar": "جوردن رامزي - طبخ", "genre": "طبخ"},
        {"name": "Nick DiGiovanni", "name_ar": "نيك ديجوفاني - طبخ", "genre": "طبخ"},
        {"name": "First We Feast", "name_ar": "فيرست وي فيست - هوت وينجز", "genre": "ترفيه/طعام"},
        {"name": "Sorted Food", "name_ar": "سورتد فود - طبخ جماعي", "genre": "طبخ"},
        {"name": "Tasty", "name_ar": "تيستي - وصفات سريعة", "genre": "طبخ"},
        {"name": "Yes Theory", "name_ar": "يس ثيوري - مغامرات", "genre": "مغامرات"},
        {"name": "Sailing La Vagabonde", "name_ar": "سايلنج لا فاجابوند - إبحار", "genre": "سفر"},
        {"name": "Drew Binsky", "name_ar": "درو بينسكي - سفر", "genre": "سفر"},
        {"name": "Kara and Nate", "name_ar": "كارا وناتي - سفر", "genre": "سفر"},
        {"name": "Peter McKinnon", "name_ar": "بيتر ماكينون - تصوير", "genre": "تصوير"},
        {"name": "Mango Street", "name_ar": "مانجو ستريت - تصوير", "genre": "تصوير"},
        {"name": "Brandon Woelfel", "name_ar": "براندون ويلفل - تصوير", "genre": "تصوير"},
        {"name": "Daniel Schiffer", "name_ar": "دانيال شيفر - تصوير إعلانات", "genre": "تصوير"},
        {"name": "Parker Walbeck", "name_ar": "باركر والبيك - فيديو", "genre": "تصوير"},
        {"name": "Matt D'Avella", "name_ar": "مات دافيلا - مينيماليزم", "genre": "أسلوب حياة"},
        {"name": "Nathaniel Drew", "name_ar": "ناثانيال درو - أسلوب حياة", "genre": "أسلوب حياة"},
        {"name": "Thomas Frank", "name_ar": "توماس فرانك - إنتاجية", "genre": "تعليمي"},
        {"name": "Ali Abdaal", "name_ar": "علي عبدال - إنتاجية", "genre": "تعليمي"},
    ]
}

# Seed database on startup
async def seed_database():
    """Seed the database with entertainment data if empty"""
    for category, items in ENTERTAINMENT_DATA.items():
        collection = db[category]
        count = await collection.count_documents({})
        if count == 0:
            docs = []
            for item in items:
                doc = {
                    "id": str(uuid.uuid4()),
                    "name": item["name"],
                    "name_ar": item["name_ar"],
                    "category": category,
                    "year": item.get("year"),
                    "genre": item.get("genre"),
                }
                docs.append(doc)
            if docs:
                await collection.insert_many(docs)
                logging.info(f"Seeded {len(docs)} items in {category}")

@app.on_event("startup")
async def startup_event():
    await seed_database()

# Routes
@api_router.get("/")
async def root():
    return {"message": "مرحباً بك في موقع الاقتراحات العشوائية!"}

@api_router.get("/categories")
async def get_categories():
    """Get all available categories with counts"""
    categories = []
    for cat_name in ENTERTAINMENT_DATA.keys():
        count = await db[cat_name].count_documents({})
        categories.append({
            "id": cat_name,
            "name": cat_name,
            "name_ar": {
                "games": "ألعاب",
                "movies": "أفلام",
                "series": "مسلسلات",
                "youtube": "يوتيوب"
            }.get(cat_name, cat_name),
            "count": count
        })
    return categories

@api_router.get("/genres/{category}")
async def get_genres(category: str):
    """Get all unique genres for a category"""
    if category not in ENTERTAINMENT_DATA:
        raise HTTPException(status_code=404, detail="الفئة غير موجودة")
    
    collection = db[category]
    genres = await collection.distinct("genre")
    genres = [g for g in genres if g]  # Remove None values
    return {"genres": sorted(genres)}

@api_router.get("/suggest/{category}", response_model=SuggestionResponse)
async def get_random_suggestion(category: str, exclude_ids: str = "", genre: str = ""):
    """Get a random suggestion from a category, optionally excluding certain IDs and filtering by genre"""
    if category not in ENTERTAINMENT_DATA:
        raise HTTPException(status_code=404, detail="الفئة غير موجودة")
    
    collection = db[category]
    
    # Build query
    query = {}
    
    # Parse excluded IDs
    excluded = []
    if exclude_ids:
        excluded = exclude_ids.split(",")
    if excluded:
        query["id"] = {"$nin": excluded}
    
    # Filter by genre if provided
    if genre:
        query["genre"] = genre
    
    total = await collection.count_documents(query if genre else {})
    
    # Get count of available items
    available_count = await collection.count_documents(query)
    
    # If all items have been shown, reset exclusion (keep genre filter)
    if available_count == 0:
        if excluded:
            query.pop("id", None)
            available_count = await collection.count_documents(query)
        if available_count == 0:
            raise HTTPException(status_code=404, detail="لا توجد اقتراحات متاحة لهذا النوع")
    
    # Get random item using aggregation
    pipeline = [
        {"$match": query},
        {"$sample": {"size": 1}},
        {"$project": {"_id": 0}}
    ]
    
    cursor = collection.aggregate(pipeline)
    items = await cursor.to_list(1)
    
    if not items:
        raise HTTPException(status_code=404, detail="لا توجد اقتراحات متاحة")
    
    item = items[0]
    suggestion = Suggestion(
        id=item["id"],
        name=item["name"],
        name_ar=item["name_ar"],
        category=item["category"],
        year=item.get("year"),
        genre=item.get("genre"),
        external_url=get_external_url(item["name"], category)
    )
    
    return SuggestionResponse(suggestion=suggestion, total_in_category=total)

@api_router.get("/all/{category}")
async def get_all_in_category(category: str, skip: int = 0, limit: int = 20):
    """Get all items in a category with pagination"""
    if category not in ENTERTAINMENT_DATA:
        raise HTTPException(status_code=404, detail="الفئة غير موجودة")
    
    collection = db[category]
    total = await collection.count_documents({})
    items = await collection.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Add external URLs
    for item in items:
        item["external_url"] = get_external_url(item["name"], category)
    
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

# Favorites endpoints
@api_router.post("/favorites")
async def add_favorite(favorite: FavoriteCreate):
    """Add an item to favorites"""
    # Check if already in favorites
    existing = await db.favorites.find_one({"item_id": favorite.item_id}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="موجود في المفضلة مسبقاً")
    
    # Get item details from category collection
    collection = db[favorite.category]
    item = await collection.find_one({"id": favorite.item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="العنصر غير موجود")
    
    # Create favorite document
    fav_doc = {
        "id": str(uuid.uuid4()),
        "item_id": favorite.item_id,
        "category": favorite.category,
        "name": item["name"],
        "name_ar": item["name_ar"],
        "year": item.get("year"),
        "genre": item.get("genre"),
        "external_url": get_external_url(item["name"], favorite.category),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.favorites.insert_one(fav_doc)
    fav_doc.pop("_id", None)
    return fav_doc

@api_router.delete("/favorites/{item_id}")
async def remove_favorite(item_id: str):
    """Remove an item from favorites"""
    result = await db.favorites.delete_one({"item_id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="العنصر غير موجود في المفضلة")
    return {"message": "تم الحذف من المفضلة"}

@api_router.get("/favorites")
async def get_favorites():
    """Get all favorites"""
    favorites = await db.favorites.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"favorites": favorites}

@api_router.get("/favorites/check/{item_id}")
async def check_favorite(item_id: str):
    """Check if an item is in favorites"""
    existing = await db.favorites.find_one({"item_id": item_id}, {"_id": 0})
    return {"is_favorite": existing is not None}

# Legacy routes
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
