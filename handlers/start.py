from aiogram import Router, types, F, Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import logging
from datetime import datetime

from database.models import db
from locales import get_message

router = Router()
geolocator = Nominatim(user_agent="drink_bot")
bot_instance = None  # Global bot instance for notifications

PREMIUM_STARS_PRICE = 150
PREMIUM_PAYLOAD_PREFIX = "premium_150:"

def set_bot_instance(bot: Bot):
    """Set global bot instance for notifications"""
    global bot_instance
    bot_instance = bot

async def get_lang(user_id: int, state: FSMContext = None) -> str:
    """Get user language from state first, then from database"""
    try:
        # First try to get from state
        if state:
            data = await state.get_data()
            if 'language' in data:
                return data['language']
        
        # Then try to get from database
        return db.get_user_language(user_id)
    except:
        return 'ru'  # Fallback to Russian

def get_user_language(user_id: int) -> str:
    """Get user language from database (synchronous version)"""
    try:
        return db.get_user_language(user_id)
    except:
        return 'ru'  # Fallback to Russian

def get_who_pays_text(who_pays: str, language: str = 'ru') -> str:
    """Convert who_pays code to readable text"""
    who_pays_map = {
        "each_self": get_message("who_pays_each_self", language),
        "i_treat": get_message("who_pays_i_treat", language), 
        "someone_treats": get_message("who_pays_someone_treats", language)
    }
    return who_pays_map.get(who_pays, get_message("who_pays_each_self", language))

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()
    waiting_for_city = State()
    waiting_for_drink = State()
    waiting_for_who_pays = State()
    waiting_for_photo = State()

class ProfileStates(StatesGroup):
    name = State()
    age = State()
    city = State()
    favorite_drink = State()
    who_pays = State()
    photo = State()
    gender = State()

class EventStates(StatesGroup):
    event_name = State()
    event_place = State()
    event_price = State()
    event_description = State()

class CompanyStates(StatesGroup):
    company_name = State()
    company_description = State()
    company_interests = State()
    company_meeting_place = State()
    company_max_members = State()

class DatingCityStates(StatesGroup):
    city_input = State()

class EditProfileStates(StatesGroup):
    edit_name = State()
    edit_age = State()
    edit_city = State()
    edit_favorite_drink = State()
    edit_photo = State()
    edit_who_pays = State()

class SeparateEditStates(StatesGroup):
    edit_name = State()
    edit_age = State()
    edit_gender = State()
    edit_city = State()
    edit_favorite_drink = State()
    edit_photo = State()
    edit_who_pays = State()

class SwipeStates(StatesGroup):
    swiping = State()

# Main keyboard with sections
def get_main_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=get_message("section_profile", language)),
            KeyboardButton(text=get_message("section_dating", language))
        ],
        [
            KeyboardButton(text=get_message("section_companies", language)),
            KeyboardButton(text=get_message("section_events", language))
        ],
        [
            KeyboardButton(text=get_message("btn_filters", language)),
            KeyboardButton(text=get_message("section_settings", language))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=get_message("choose_action", language)
    )

async def show_profile_screen(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id, state)
        profile = db.get_profile(user_id)
        if not profile:
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return

        who_pays_key = {
            'each_self': 'who_pays_each_self',
            'i_treat': 'who_pays_i_treat',
            'someone_treats': 'who_pays_someone_treats',
        }.get(profile.get('who_pays'), 'who_pays_each_self')

        # Get gender text
        gender_key = {
            'male': 'gender_male',
            'female': 'gender_female', 
            'other': 'gender_other',
        }.get(profile.get('gender'), 'gender_other')
        gender_text = get_message(gender_key, lang)

        city_text = (profile.get('city_display') or profile.get('city') or '').title()
        who_pays_text = get_message(who_pays_key, lang)

        text = get_message(
            'profile_created',
            lang,
            name=profile.get('name', ''),
            age=profile.get('age', ''),
            gender=gender_text,
            city=city_text,
            drink=profile.get('favorite_drink', ''),
            who_pays=who_pays_text,
        )

        if profile.get('photo_id'):
            await message.answer_photo(
                photo=profile['photo_id'],
                caption=text,
                reply_markup=get_profile_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                text,
                reply_markup=get_profile_keyboard(lang),
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Error in show_profile_screen: {e}")
        await message.answer(get_message("error", 'ru'), parse_mode='HTML')

# Section keyboards
def get_profile_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=get_message("btn_fill_profile", language)),
            KeyboardButton(text=get_message("btn_edit_profile", language))
        ],
        [
            KeyboardButton(text=get_message("btn_delete_profile", language)),
            KeyboardButton(text=get_message("btn_my_matches", language))
        ],
        [
            KeyboardButton(text=get_message("back_to_main", language))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=get_message("choose_action", language)
    )

def get_edit_profile_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=get_message("btn_edit_name", language)),
            KeyboardButton(text=get_message("btn_edit_age", language))
        ],
        [
            KeyboardButton(text=get_message("btn_edit_gender", language)),
            KeyboardButton(text=get_message("btn_edit_city", language))
        ],
        [
            KeyboardButton(text=get_message("btn_edit_drink", language)),
            KeyboardButton(text=get_message("btn_edit_who_pays", language))
        ],
        [
            KeyboardButton(text=get_message("btn_edit_photo", language)),
            KeyboardButton(text=get_message("back_to_main", language))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=get_message("choose_action", language)
    )

def get_dating_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=get_message("btn_find_dating_my_city", language)),
            KeyboardButton(text=get_message("btn_find_dating_other_city", language))
        ],
        [
            KeyboardButton(text=get_message("btn_my_matches", language))
        ],
        [
            KeyboardButton(text=get_message("back_to_main", language))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=get_message("choose_action", language)
    )

def get_companies_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=get_message("btn_create_company", language)),
            KeyboardButton(text=get_message("btn_find_companies", language))
        ],
        [
            KeyboardButton(text=get_message("btn_my_companies", language))
        ],
        [
            KeyboardButton(text=get_message("back_to_main", language))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=get_message("choose_action", language)
    )

def get_events_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=get_message("btn_create_event", language)),
            KeyboardButton(text=get_message("btn_view_events", language))
        ],
        [
            KeyboardButton(text=get_message("btn_my_events", language))
        ],
        [
            KeyboardButton(text=get_message("back_to_main", language))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=get_message("choose_action", language)
    )

def get_settings_keyboard(language: str = 'ru') -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🌐 Сменить язык / Change Language")
        ],
        [
            KeyboardButton(text=get_message("back_to_main", language))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=get_message("choose_action", language)
    )

def get_swipe_keyboard(language: str = 'ru') -> InlineKeyboardMarkup:
    """Get inline keyboard for swipe actions (like/dislike/back)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️", callback_data="like"),
            InlineKeyboardButton(text="👎", callback_data="dislike")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_profile")
        ]
    ])
    return keyboard

@router.message(F.text == "/start")
async def cmd_start(message: types.Message, state: FSMContext):
    """Handle /start command - reset state and restart"""
    try:
        user_id = message.from_user.id
        logging.info(f"/start command from user {user_id}")
        
        # Clear state to reset any stuck processes
        await state.clear()
        
        # Update username in DB if profile exists (Telegram usernames can change)
        try:
            if message.from_user.username:
                db.update_profile(user_id, username=message.from_user.username)
        except Exception as e:
            logging.warning(f"Failed to update username for user {user_id}: {e}")

        user_profile = db.get_profile(user_id)
        logging.info(f"User profile: {user_profile}")
        
        # Check if user exists and has language set
        if not user_profile or not user_profile.get('language'):
            # Show language selection
            logging.info(f"Showing language selection for {user_id}")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
                [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_ua")],
                [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
            ])
            await message.answer(
                get_message("select_language"),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            # User exists, check if profile is filled
            language = user_profile['language']
            logging.info(f"User {user_id} exists with language: {language}")
            
            # Check if profile has name (filled)
            if not user_profile.get('name'):
                # Profile exists but not filled - show only fill profile button
                keyboard = ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text=get_message("btn_fill_profile", language))]],
                    resize_keyboard=True,
                    input_field_placeholder=get_message("choose_action", language)
                )
                await message.answer(
                    get_message("welcome", language),
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
            else:
                # Profile filled - show main menu
                await message.answer(
                    get_message("welcome", language),
                    reply_markup=get_main_keyboard(language),
                    parse_mode='HTML'
                )
            
    except Exception as e:
        logging.error(f"Error in /start handler: {e}")
        await message.answer(get_message("error", 'ru'), parse_mode='HTML')

@router.callback_query(F.data.startswith("lang_"))
async def language_selection_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle language selection and save to state and DB"""
    user_id = callback.from_user.id
    lang_code = callback.data.split("_")[1]
    
    # Save to state
    await state.update_data(language=lang_code)
    
    # Save to database
    db.update_user_language(user_id, lang_code)
    
    # Get localized messages
    language_name = {
        'ru': '🇷🇺 Русский',
        'ua': '🇺🇦 Українська',
        'en': '🇬🇧 English'
    }.get(lang_code, 'Русский')
    
    await callback.answer(f"Язык изменен на {language_name}")
    
    # Check if user already has a profile
    existing_profile = db.get_profile(user_id)
    if existing_profile and existing_profile.get('name'):
        # User has a profile - show main menu
        await callback.message.answer(
            f"✅ Язык успешно изменен на {language_name}!",
            reply_markup=get_main_keyboard(lang_code),
            parse_mode='HTML'
        )
    else:
        # New user - show welcome with fill profile button
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=get_message("btn_fill_profile", lang_code))]],
            resize_keyboard=True,
            input_field_placeholder=get_message("choose_action", lang_code)
        )
        await callback.message.answer(
            get_message("welcome", lang_code),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    
    # Clear state to avoid interference
    await state.clear()

# All state handlers should be defined BEFORE the general text handler

async def show_language_selection(message: types.Message):
    """Show language selection keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton(text="🇺🇦 Українська", callback_data="lang_ua")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
    ])
    await message.answer(
        get_message("select_language"),
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@router.message(F.text.in_(["📝 Заполнить анкету", "📝 Заповнити анкету", "📝 Fill Profile"]))
async def fill_profile_start(message: types.Message, state: FSMContext):
    """Start profile filling process"""
    # Get user language properly
    user_id = message.from_user.id
    language = get_user_language(user_id)  # Get from database
    
    # Check if profile already exists
    existing_profile = db.get_profile(user_id)
    if existing_profile and existing_profile.get('name'):  # Check if profile is actually filled
        language = existing_profile.get('language', language)  # Use profile language if available
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_message("btn_update_profile", language), callback_data="fill_again")],
            [InlineKeyboardButton(text=get_message("btn_cancel", language), callback_data="cancel_profile")]
        ])
        photo_text = f"\n📸 Фото: {'Есть' if existing_profile['photo_id'] else 'Нет'}" if existing_profile.get('photo_id') else ""
        await message.answer(
            get_message("profile_exists", language, 
                     name=existing_profile['name'], 
                     age=existing_profile['age'], 
                     city=existing_profile['city'].title(),
                     drink=existing_profile['favorite_drink'],
                     photo=photo_text),
            reply_markup=keyboard
        )
        return
    
    # Save language to state for registration
    await state.update_data(language=language)
    
    await message.answer(
        get_message("profile_name_prompt", language),
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode='HTML'
    )
    await state.set_state(RegistrationStates.waiting_for_name)

@router.message(ProfileStates.name)
async def process_profile_name(message: types.Message, state: FSMContext):
    """Process profile name input for new profile creation"""
    try:
        user_id = message.from_user.id
        logging.info(f"process_profile_name called for user {user_id}")
        
        # Get language from state first, then database
        lang = await get_lang(user_id, state)
        logging.info(f"Language for {user_id}: {lang}")
        
        # Validate input
        if not message.text or not message.text.strip():
            await message.answer(get_message("profile_name_error", lang), parse_mode='HTML')
            return
            
        if len(message.text.strip()) < 2:
            await message.answer(get_message("profile_name_error", lang), parse_mode='HTML')
            return
        
        # Save name to state
        await state.update_data(name=message.text.strip())
        logging.info(f"DEBUG: User {user_id} saved name: '{message.text.strip()}'")
        
        # Ask for age
        await message.answer(
            get_message("profile_age_prompt", lang),
            parse_mode='HTML'
        )
        
        # Set next state
        await state.set_state(ProfileStates.age)
        logging.info(f"DEBUG: User {user_id} moved to age state")
        
    except Exception as e:
        logging.error(f"Error in process_profile_name: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    """Process name input with correct sequence"""
    try:
        user_id = message.from_user.id
        logging.info(f"process_name called for user {user_id}")
        
        # Get language from state first, then database
        lang = await get_lang(user_id, state)
        logging.info(f"Language for {user_id}: {lang}")
        
        # Validate input
        if not message.text or not message.text.strip():
            await message.answer(get_message("profile_name_error", lang), parse_mode='HTML')
            return
            
        if len(message.text.strip()) < 2:
            await message.answer(get_message("profile_name_error", lang), parse_mode='HTML')
            return
        
        # Step 1: Save name to state
        name = message.text.strip()
        await state.update_data(name=name)
        logging.info(f"Name '{name}' saved to state for {user_id}")
        
        # Step 2: Change state to waiting_for_age
        await state.set_state(RegistrationStates.waiting_for_age)
        logging.info(f"🔄 DEBUG: Перехожу к шагу ВОЗРАСТ для юзера {user_id}")
        
        # Step 3: Send age question using localized message
        await message.answer(get_message("profile_age_prompt", lang), parse_mode='HTML')
        logging.info(f"Age question sent to {user_id}")
        
    except Exception as e:
        logging.error(f"Error in process_name: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("profile_name_error", lang), parse_mode='HTML')

@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    """Process age input"""
    try:
        user_id = message.from_user.id
        logging.info(f"🎂 process_age called for user {user_id}")
        
        # Get language from state first, then database
        lang = await get_lang(user_id, state)
        logging.info(f"🌍 Language for {user_id}: {lang}")
        
        # Validate input
        if not message.text or not message.text.strip():
            await message.answer(get_message("profile_age_invalid", lang), parse_mode='HTML')
            return
            
        try:
            age = int(message.text.strip())
            if age < 18 or age > 100:
                await message.answer(get_message("profile_age_error", lang), parse_mode='HTML')
                return
        except ValueError:
            await message.answer(get_message("profile_age_invalid", lang), parse_mode='HTML')
            return
        
        # Save age to state
        await state.update_data(age=age)
        logging.info(f"💾 Age '{age}' saved to state for {user_id}")
        
        # Change state to waiting_for_gender
        await state.set_state(RegistrationStates.waiting_for_gender)
        logging.info(f"🔄 DEBUG: Перехожу к шагу ПОЛ для юзера {user_id}")
        
        # Send gender question with buttons
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_message("gender_male", lang), callback_data="gender_male")],
            [InlineKeyboardButton(text=get_message("gender_female", lang), callback_data="gender_female")],
            [InlineKeyboardButton(text=get_message("gender_other", lang), callback_data="gender_other")]
        ])
        await message.answer(
            get_message("profile_gender_prompt", lang),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        logging.info(f"✅ Gender question sent to {user_id}")
        
    except Exception as e:
        logging.error(f"❌ Error in process_age: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("profile_age_invalid", lang), parse_mode='HTML')

@router.callback_query(F.data.startswith("gender_"), RegistrationStates.waiting_for_gender)
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    """Process gender selection and request city"""
    try:
        gender = callback.data.split("_")[1]
        user_id = callback.from_user.id
        
        # Get language from state first, then database
        lang = await get_lang(user_id, state)
        logging.info(f"🌍 Language for {user_id}: {lang}")
        
        # Save gender to state
        await state.update_data(gender=gender)
        logging.info(f"💾 Gender '{gender}' saved to state for {user_id}")
        
        # Change state to waiting_for_city
        await state.set_state(RegistrationStates.waiting_for_city)
        logging.info(f"🔄 DEBUG: Перехожу к шагу ГОРОД для юзера {user_id}")
        
        # Send city question
        await callback.answer()
        await callback.message.answer(get_message("profile_city_prompt", lang), parse_mode='HTML')
        logging.info(f"✅ City question sent to {user_id}")
        
    except Exception as e:
        logging.error(f"Error in process_gender: {e}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.message.answer(get_message("use_buttons_error", lang), parse_mode='HTML')

@router.message(RegistrationStates.waiting_for_city)
async def process_city(message: types.Message, state: FSMContext):
    """Process city input with geopy validation"""
    try:
        user_id = message.from_user.id
        logging.info(f"🏙️ process_city called for user {user_id}")
        
        # Get language from state first, then database
        lang = await get_lang(user_id, state)
        logging.info(f"🌍 Language for {user_id}: {lang}")
        
        # Validate input
        if not message.text or not message.text.strip():
            await message.answer(get_message("profile_city_error", lang), parse_mode='HTML')
            return
            
        city_text = message.text.strip()
        if len(city_text) < 2:
            await message.answer(get_message("profile_city_error", lang), parse_mode='HTML')
            return
        
        # Validate city with geopy (optional)
        try:
            location = geolocator.geocode(city_text, timeout=5)
            if not location:
                await message.answer(get_message("city_not_found", lang), parse_mode='HTML')
                return
        except (GeocoderTimedOut, GeocoderServiceError):
            # If geopy fails, still accept the city
            pass
        
        # Save city to state
        city = city_text.lower()
        await state.update_data(city=city)
        logging.info(f"💾 City '{city}' saved to state for {user_id}")
        
        # Change state to waiting_for_drink
        await state.set_state(RegistrationStates.waiting_for_drink)
        logging.info(f"🔄 DEBUG: Перехожу к шагу НАПИТОК для юзера {user_id}")
        
        # Send drink question
        await message.answer(get_message("profile_drink_prompt", lang), parse_mode='HTML')
        logging.info(f"✅ Drink question sent to {user_id}")
        
    except Exception as e:
        logging.error(f"❌ Error in process_city: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("profile_city_error", lang), parse_mode='HTML')

@router.message(RegistrationStates.waiting_for_drink)
async def process_favorite_drink(message: types.Message, state: FSMContext):
    """Process favorite drink input and request who pays question"""
    try:
        # Get language from state first, then database
        lang = await get_lang(message.from_user.id, state)
        
        # Validate input
        if not message.text or not message.text.strip():
            await message.answer(get_message("profile_drink_error", lang), parse_mode='HTML')
            return
            
        if len(message.text.strip()) < 2:
            await message.answer(get_message("profile_drink_error", lang), parse_mode='HTML')
            return
        
        # Save drink to state
        drink = message.text.strip()
        await state.update_data(favorite_drink=drink)
        
        # Change state to waiting_for_who_pays
        await state.set_state(RegistrationStates.waiting_for_who_pays)
        
        # Send who pays question with localized buttons
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_message("who_pays_each_self", lang), callback_data="who_pays_each_self")],
            [InlineKeyboardButton(text=get_message("who_pays_i_treat", lang), callback_data="who_pays_i_treat")],
            [InlineKeyboardButton(text=get_message("who_pays_someone_treats", lang), callback_data="who_pays_someone_treats")]
        ])
        await message.answer(
            get_message("profile_who_pays_prompt", lang),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logging.info(f"User {message.from_user.id} entered drink: {drink}")
        
    except Exception as e:
        logging.error(f"Error in process_favorite_drink: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("profile_drink_error", lang), parse_mode='HTML')

@router.callback_query(F.data.startswith("who_pays_"), RegistrationStates.waiting_for_who_pays)
async def process_who_pays(callback: types.CallbackQuery, state: FSMContext):
    """Process who pays selection and request photo"""
    try:
        # Get language from state first, then database
        lang = await get_lang(callback.from_user.id, state)
        
        # Map callback data to values
        who_pays_map = {
            "who_pays_each_self": "each_self",
            "who_pays_i_treat": "i_treat", 
            "who_pays_someone_treats": "someone_treats"
        }
        
        # Save who_pays to state
        who_pays = who_pays_map[callback.data]
        await state.update_data(who_pays=who_pays)
        
        # Change state to waiting_for_photo
        await state.set_state(RegistrationStates.waiting_for_photo)
        
        # Send photo request
        await callback.answer()
        await callback.message.answer(
            get_message("profile_photo_prompt", lang),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        
        logging.info(f"User {callback.from_user.id} selected who_pays: {who_pays}")
        
    except Exception as e:
        logging.error(f"Error in process_who_pays: {e}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.message.answer(get_message("use_buttons_error", lang), parse_mode='HTML')

@router.message(RegistrationStates.waiting_for_photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    """Process photo and save complete profile"""
    try:
        user_data = await state.get_data()
        
        # Get the largest photo
        photo = message.photo[-1]
        photo_id = photo.file_id
        
        # Get language from state first, then database
        lang = await get_lang(message.from_user.id, state)
        
        # Save profile to database with error handling
        try:
            success = db.create_profile(
                user_id=message.from_user.id,
                username=message.from_user.username,
                name=user_data['name'],
                age=user_data['age'],
                gender=user_data['gender'],
                city=user_data['city'],
                favorite_drink=user_data['favorite_drink'],
                photo_id=photo_id,
                who_pays=user_data['who_pays'],
                language=lang  # Use user's actual language
            )
        except Exception as db_error:
            logging.error(f"Database error saving profile: {db_error}")
            await message.answer(get_message("profile_error", lang), parse_mode='HTML')
            return
        
        # Clear state
        await state.clear()
        
        # Send success message
        if success:
            # Get gender text
            gender_text = {
                'male': get_message("gender_male", lang),
                'female': get_message("gender_female", lang),
                'other': get_message("gender_other", lang)
            }.get(user_data['gender'], get_message("gender_other", lang))
            
            await message.answer_photo(
                photo=photo_id,
                caption=get_message("profile_created", lang,
                                 name=user_data['name'],
                                 age=user_data['age'],
                                 gender=gender_text,
                                 city=user_data['city'].title(),
                                 drink=user_data['favorite_drink'],
                                 who_pays=get_who_pays_text(user_data['who_pays'], lang)),
                reply_markup=get_main_keyboard(lang)
            )
        else:
            await message.answer(
                get_message("profile_error", lang),
                reply_markup=get_main_keyboard(lang)
            )
        
        logging.info(f"User {message.from_user.id} completed registration with photo")
        
    except Exception as e:
        logging.error(f"Error in process_photo: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("profile_photo_error", lang), parse_mode='HTML')

@router.message(RegistrationStates.waiting_for_photo)
async def process_photo_invalid(message: types.Message, state: FSMContext):
    """Handle invalid input when photo is expected"""
    try:
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("profile_photo_error", lang), parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error in process_photo_invalid: {e}")

@router.message(RegistrationStates.waiting_for_who_pays)
async def process_who_pays_invalid(message: types.Message, state: FSMContext):
    """Handle invalid input when who pays selection is expected"""
    try:
        lang = await get_lang(message.from_user.id, state)
        await message.answer(
            get_message("use_buttons_error", lang),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_message("who_pays_each_self", lang), callback_data="who_pays_each_self")],
                [InlineKeyboardButton(text=get_message("who_pays_i_treat", lang), callback_data="who_pays_i_treat")],
                [InlineKeyboardButton(text=get_message("who_pays_someone_treats", lang), callback_data="who_pays_someone_treats")]
            ]),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in process_who_pays_invalid: {e}")

async def show_next_profile(message: types.Message, state: FSMContext):
    """Show next profile in swipe gallery with detailed logging"""
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id, state)
        
        logging.info(f"DEBUG: Starting search for user {user_id}")
        
        user_profile = db.get_profile(user_id)
        if not user_profile:
            logging.error(f"DEBUG: User {user_id} has no profile")
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        # Check for city_normalized
        user_city = user_profile.get('city')
        user_city_normalized = user_profile.get('city_normalized')
        
        logging.info(f"DEBUG: User {user_id} city_display='{user_city}', city_normalized='{user_city_normalized}'")
        
        if not user_city_normalized:
            logging.error(f"DEBUG: User {user_id} has no city_normalized, trying to normalize")
            user_city_normalized = db.normalize_city(user_city or "")
            # Update user profile with normalized city
            db.update_user_city_normalized(user_id, user_city, user_city_normalized)
            logging.info(f"DEBUG: Updated user {user_id} city_normalized to '{user_city_normalized}'")
        
        # Search for profiles using city_normalized
        logging.info(f"DEBUG: Searching profiles in city_normalized='{user_city_normalized}' for user {user_id}")
        profiles = db.find_profiles_for_swipe(user_id, city=user_city, limit=50)
        
        logging.info(f"DEBUG: Found {len(profiles)} profiles for user {user_id}")
        if profiles:
            for i, p in enumerate(profiles[:3]):  # Log first 3 profiles
                logging.info(f"DEBUG: Profile {i+1}: user_id={p.get('user_id')}, city_normalized='{p.get('city_normalized')}', name='{p.get('name')}'")
        
        if not profiles:
            logging.info(f"DEBUG: No profiles found for user {user_id} in city '{user_city_normalized}'")
            await message.answer(
                get_message("no_profiles_nearby", lang, city=user_city.title()),
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        # Check if this is the last profile - show empty message instead
        if len(profiles) == 1:
            logging.info(f"DEBUG: Only 1 profile available in nearby cities, showing empty message instead")
            await message.answer(
                get_message("no_more_profiles", lang, text="Анкеты закончились!"),
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        profile = profiles[0]
        lang = await get_lang(message.from_user.id, state)
        
        # Get gender text
        gender_key = {
            'male': 'gender_male',
            'female': 'gender_female', 
            'other': 'gender_other',
        }.get(profile.get('gender'), 'gender_other')
        gender_text = get_message(gender_key, lang)
        
        profile_text = (
            f"👤 <b>{profile['name']}, {profile['age']}</b>\n"
            f"⚧️ {gender_text}\n"
            f"🏙️ {profile['city'].title()}\n"
            f"🍺 {profile['favorite_drink']}"
        )
        
        # Add photo if available
        if profile.get('photo_id'):
            await message.answer_photo(
                photo=profile['photo_id'],
                caption=profile_text,
                reply_markup=get_swipe_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                get_message("no_photo", lang) + f"\n\n{profile_text}",
                reply_markup=get_swipe_keyboard(lang),
                parse_mode='HTML'
            )
        
        # Update current index
        await state.update_data(current_index=1)
        
    except Exception as e:
        logging.error(f"Error in show_next_profile: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')


async def create_company_start(message: types.Message, state: FSMContext):
    """Start company creation"""
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id, state)
        user_profile = db.get_profile(user_id)
        if not user_profile:
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return

        await message.answer(
            get_message("company_name_prompt", lang),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        await state.set_state(CompanyStates.company_name)
    except Exception as e:
        logging.error(f"Error in create_company_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')


@router.message(CompanyStates.company_name)
async def process_company_name(message: types.Message, state: FSMContext):
    try:
        lang = await get_lang(message.from_user.id, state)
        if not message.text or len(message.text.strip()) < 2:
            await message.answer(get_message("company_name_error", lang), parse_mode='HTML')
            return

        await state.update_data(company_name=message.text.strip())
        await state.set_state(CompanyStates.company_description)
        await message.answer(get_message("company_description_prompt", lang), parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error in process_company_name: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')


@router.message(CompanyStates.company_description)
async def process_company_description(message: types.Message, state: FSMContext):
    try:
        lang = await get_lang(message.from_user.id, state)
        if not message.text or len(message.text.strip()) < 5:
            await message.answer(get_message("company_description_error", lang), parse_mode='HTML')
            return

        await state.update_data(company_description=message.text.strip())
        await state.set_state(CompanyStates.company_interests)
        await message.answer(get_message("company_interests_prompt", lang), parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error in process_company_description: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')


@router.message(CompanyStates.company_interests)
async def process_company_interests(message: types.Message, state: FSMContext):
    try:
        lang = await get_lang(message.from_user.id, state)
        if not message.text or len(message.text.strip()) < 2:
            await message.answer(get_message("company_interests_error", lang), parse_mode='HTML')
            return

        await state.update_data(company_interests=message.text.strip())
        await state.set_state(CompanyStates.company_meeting_place)
        await message.answer(get_message("company_meeting_place_prompt", lang), parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error in process_company_interests: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')


@router.message(CompanyStates.company_meeting_place)
async def process_company_meeting_place(message: types.Message, state: FSMContext):
    try:
        lang = await get_lang(message.from_user.id, state)
        if not message.text or len(message.text.strip()) < 2:
            await message.answer(get_message("company_meeting_place_error", lang), parse_mode='HTML')
            return

        await state.update_data(company_meeting_place=message.text.strip())
        await state.set_state(CompanyStates.company_max_members)
        await message.answer(get_message("company_max_members_prompt", lang), parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error in process_company_meeting_place: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')


@router.message(CompanyStates.company_max_members)
async def process_company_max_members(message: types.Message, state: FSMContext):
    try:
        lang = await get_lang(message.from_user.id, state)
        user_id = message.from_user.id
        user_profile = db.get_profile(user_id)

        try:
            max_members = int((message.text or '').strip())
        except ValueError:
            await message.answer(get_message("company_max_members_error", lang), parse_mode='HTML')
            return

        if max_members < 2 or max_members > 100:
            await message.answer(get_message("company_max_members_error", lang), parse_mode='HTML')
            return

        data = await state.get_data()
        city_value = (user_profile.get('city_display') or user_profile.get('city') or '')
        success = db.create_company(
            creator_id=user_id,
            name=data['company_name'],
            description=data['company_description'],
            interests=data['company_interests'],
            meeting_place=data['company_meeting_place'],
            max_members=max_members,
            city=city_value,
        )

        await state.clear()

        if success:
            await message.answer(
                get_message("company_created", lang),
                reply_markup=get_companies_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                get_message("company_create_error", lang),
                reply_markup=get_companies_keyboard(lang),
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Error in process_company_max_members: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')


async def find_companies_start(message: types.Message, state: FSMContext):
    """Show companies in user's city"""
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id, state)
        user_profile = db.get_profile(user_id)
        if not user_profile:
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return

        city_value = (user_profile.get('city_display') or user_profile.get('city') or '')
        companies = db.get_companies_by_city(city_value, limit=10)
        if not companies:
            await message.answer(
                get_message("no_companies_in_city", lang, city=city_value.title()),
                reply_markup=get_companies_keyboard(lang),
                parse_mode='HTML'
            )
            return

        await message.answer(
            get_message("companies_in_city", lang, city=city_value.title()),
            parse_mode='HTML'
        )

        for company in companies:
            is_member = db.is_user_in_company(company['id'], user_id)
            button_text = get_message("leave_company", lang) if is_member else get_message("join_company", lang)
            button_callback = f"leave_company_{company['id']}" if is_member else f"join_company_{company['id']}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=button_text, callback_data=button_callback)]
            ])

            company_text = (
                f"<b>{company['name']}</b>\n"
                f"Создатель: {company.get('creator_name', '')}\n"
                f"{company.get('description', '')}\n"
                f"Интересы: {company.get('interests', '')}\n"
                f"Место встреч: {company.get('meeting_place', '')}\n"
                f"Участников: {company.get('current_members', 0)}/{company.get('max_members', 0)}"
            )

            await message.answer(company_text, reply_markup=keyboard, parse_mode='HTML')
    except Exception as e:
        logging.error(f"Error in find_companies_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def show_my_companies(message: types.Message):
    """Show user's companies with member list"""
    try:
        lang = await get_lang(message.from_user.id)
        companies = db.get_user_companies(message.from_user.id)
        
        if not companies:
            await message.answer(
                "Вы пока не участвуете ни в одной компании.\n"
                "Создайте свою или присоединитесь к существующей!",
                reply_markup=get_companies_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        await message.answer(f"Ваши компании ({len(companies)}):", parse_mode='HTML')
        
        for company in companies:
            # Get company members with usernames
            members = db.get_company_members_with_usernames(company['id'])
            
            # Create member list text
            member_list = []
            for member in members:
                if member['username']:
                    member_list.append(f"{member['name']} - @{member['username']}")
                else:
                    member_list.append(f"{member['name']} - (нет юзернейма)")
            
            members_text = "\n".join(member_list) if member_list else "Пока нет участников"
            
            company_text = (
                f"<b>{company['name']}</b>\n"
                f"Создатель: {company['creator_name']}\n"
                f"{company['description']}\n"
                f"Интересы: {company['interests']}\n"
                f"Место встреч: {company['meeting_place']}\n"
                f"Участников: {company['current_members']}/{company['max_members']}\n\n"
                f"<b>Участники:</b>\n{members_text}"
            )
            
            await message.answer(company_text, parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Error in show_my_companies: {e}")
        lang = await get_lang(message.from_user.id)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.callback_query(F.data.startswith("join_company_"))
async def join_company_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle joining a company"""
    try:
        company_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        
        success = db.join_company(company_id, user_id)
        
        if success:
            await callback.answer("Вы присоединились к компании!")
            await callback.message.answer(
                "Вы присоединились к компании!",
                reply_markup=get_companies_keyboard(get_user_language(user_id)),
                parse_mode='HTML'
            )
            logging.info(f"DEBUG: User {user_id} successfully joined company {company_id}")
        else:
            await callback.answer("Вы уже участвуете в этой компании")
            
    except Exception as e:
        logging.error(f"Error in join_company_callback: {e}")
        await callback.answer("Ошибка при присоединении к компании")

@router.callback_query(F.data.startswith("leave_company_"))
async def leave_company_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle leaving a company"""
    try:
        company_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        
        success = db.leave_company(company_id, user_id)
        
        if success:
            await callback.answer("Вы покинули компанию")
            await callback.message.answer(
                "Вы покинули компанию",
                reply_markup=get_companies_keyboard(get_user_language(user_id)),
                parse_mode='HTML'
            )
            logging.info(f"DEBUG: User {user_id} successfully left company {company_id}")
        else:
            await callback.answer("Вы не участвуете в этой компании")
            
    except Exception as e:
        logging.error(f"Error in leave_company_callback: {e}")
        await callback.answer("Ошибка при выходе из компании")

async def find_company_start(message: types.Message, state: FSMContext):
    """Start swipe gallery for finding company with detailed logging"""
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id, state)
        
        logging.info(f"DEBUG: find_company_start called for user {user_id}")
        
        user_profile = db.get_profile(user_id)
        if not user_profile:
            logging.error(f"DEBUG: User {user_id} has no profile in find_company_start")
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        logging.info(f"DEBUG: User {user_id} profile found: city='{user_profile.get('city')}', city_normalized='{user_profile.get('city_normalized')}'")
        
        if not user_profile.get('photo_id'):
            logging.warning(f"DEBUG: User {user_id} has no photo")
            await message.answer(
                get_message("need_photo_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        await state.set_state(SwipeStates.swiping)
        logging.info(f"DEBUG: State set to swiping for user {user_id}")
        await show_next_profile(message, state)
        
    except Exception as e:
        logging.error(f"DEBUG: Real error in find_company_start for user {message.from_user.id}: {e}")
        import traceback
        logging.error(f"DEBUG: Traceback: {traceback.format_exc()}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(
            f"Search start error: {str(e)}",
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )

async def send_profile_with_photo(message, profile, user_id, state):
    """Send profile with photo and swipe keyboard"""
    try:
        lang = await get_lang(user_id, state)
        
        # Update user activity
        from notification_system import get_notification_system
        notification_system = get_notification_system(message.bot)
        await notification_system.update_user_activity(user_id)
        
        # Format profile text
        profile_text = f"👤 {profile['name']}, {profile['age']}\n🏙️ {profile['city'].title()}\n🍺 {profile['favorite_drink']}"
        
        # Send with photo if available
        if profile.get('photo_id'):
            await message.answer_photo(
                photo=profile['photo_id'],
                caption=profile_text,
                reply_markup=get_swipe_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                get_message("no_photo", lang) + f"\n\n{profile_text}",
                reply_markup=get_swipe_keyboard(lang),
                parse_mode='HTML'
            )
        
        logging.info(f"DEBUG: Profile sent to user {user_id}")
        
    except Exception as e:
        logging.error(f"Error in send_profile_with_photo: {e}")
        lang = await get_lang(user_id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.callback_query(F.data == "back_profile")
async def handle_back_profile(callback: types.CallbackQuery, state: FSMContext):
    """Handle back button in swipe - go to previous profile or main menu"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        
        # Get current state data
        data = await state.get_data()
        profiles = data.get('profiles', [])
        current_index = data.get('current_index', 0)
        
        logging.info(f"DEBUG: Back button pressed. Current index: {current_index}, Total profiles: {len(profiles)}")
        
        # Check if we can go back
        if current_index > 0 and len(profiles) > 1:
            # Move to previous profile
            new_index = current_index - 1
            await state.update_data(current_index=new_index)
            
            # Get previous profile
            prev_profile = profiles[new_index]
            logging.info(f"DEBUG: Moving back to profile {new_index}: {prev_profile.get('name')}")
            
            # Send previous profile
            await send_profile_with_photo(callback.message, prev_profile, user_id, state)
            
        else:
            # At first profile or no profiles - return to main menu
            logging.info(f"DEBUG: At first profile or no profiles, returning to main menu")
            
            lang = get_user_language(user_id)
            await callback.message.answer(
                "Возвращаемся в главное меню...",
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            
            # Clear state
            await state.clear()
        
    except Exception as e:
        logging.error(f"Error in handle_back_profile: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer("Ошибка при возврате")

@router.callback_query(F.data.in_(["like", "dislike"]), SwipeStates.swiping)
async def handle_swipe_action(callback: types.CallbackQuery, state: FSMContext):
    """Handle like/dislike actions with notification system"""
    try:
        await callback.answer()
        
        data = await state.get_data()
        profiles = data.get('profiles', [])
        current_index = data.get('current_index', 0)
        
        logging.info(f"DEBUG: Swipe action - profiles: {len(profiles)}, current_index: {current_index}")
        
        if not profiles or current_index >= len(profiles):
            lang = await get_lang(callback.from_user.id, state)
            await callback.message.answer(
                get_message("no_more_profiles", lang, text="Анкеты закончились!"),
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            await state.clear()
            return
        
        # Check if this is the last profile - show empty message instead of showing it
        if current_index == len(profiles) - 1:
            logging.info(f"DEBUG: Last profile reached, showing empty message instead")
            lang = await get_lang(callback.from_user.id, state)
            await callback.message.answer(
                get_message("no_more_profiles", lang, text="Анкеты закончились!"),
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            await state.clear()
            return
        
        current_profile = profiles[current_index]
        logging.info(f"DEBUG: Current profile: user_id={current_profile.get('user_id')}")
        
        # Mark profile as viewed for today
        db.mark_profile_as_viewed(callback.from_user.id, current_profile['user_id'])
        logging.info(f"DEBUG: Marked profile {current_profile['user_id']} as viewed for user {callback.from_user.id}")
        
        # Handle like action
        if callback.data == "like":
            from_user_id = callback.from_user.id
            to_user_id = current_profile['user_id']
            
            logging.info(f"DEBUG: User {from_user_id} liked user {to_user_id}")
            
            # Add like to database
            like_added = db.add_like(from_user_id, to_user_id)
            
            if like_added:
                # Check for mutual like
                is_mutual = db.check_mutual_like(from_user_id, to_user_id)
                
                if is_mutual:
                    # MATCH! Save to database and send notifications
                    match_created = db.create_match(from_user_id, to_user_id)
                    logging.info(f"DEBUG: Match created: {match_created} between {from_user_id} and {to_user_id}")
                    
                    # Send notifications to both users
                    await send_match_notifications(from_user_id, to_user_id)
                else:
                    # One-sided like - send notification to the other user
                    await send_like_notification(from_user_id, to_user_id, current_profile)
        
        # Move to next profile
        next_index = current_index + 1
        await state.update_data(current_index=next_index)
        
        # Show next profile or finish
        if next_index < len(profiles):
            next_profile = profiles[next_index]
            fresh_profile = db.get_profile(next_profile.get('user_id'))
            if fresh_profile and fresh_profile.get('photo_id'):
                next_profile['photo_id'] = fresh_profile.get('photo_id')
            lang = await get_lang(callback.from_user.id, state)
            
            # Get gender text
            gender_key = {
                'male': 'gender_male',
                'female': 'gender_female', 
                'other': 'gender_other',
            }.get(next_profile.get('gender'), 'gender_other')
            gender_text = get_message(gender_key, lang)
            
            profile_text = (
                f"👤 <b>{next_profile['name']}, {next_profile['age']}</b>\n"
                f"⚧️ {gender_text}\n"
                f"🏙️ {next_profile['city'].title()}\n"
                f"🍺 {next_profile['favorite_drink']}"
            )
            
            # Add photo if available
            if next_profile.get('photo_id'):
                await callback.message.answer_photo(
                    photo=next_profile['photo_id'],
                    caption=profile_text,
                    reply_markup=get_swipe_keyboard(lang),
                    parse_mode='HTML'
                )
            else:
                await callback.message.answer(
                    get_message("no_photo", lang) + f"\n\n{profile_text}",
                    reply_markup=get_swipe_keyboard(lang),
                    parse_mode='HTML'
                )
        else:
            # No more profiles
            lang = await get_lang(callback.from_user.id, state)
            await callback.message.answer(
                get_message("no_more_profiles", lang, text="Анкеты закончились!"),
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            await state.clear()
        
    except Exception as e:
        logging.error(f"DEBUG: Real error in handle_swipe_action for user {callback.from_user.id}: {e}")
        import traceback
        logging.error(f"DEBUG: Traceback: {traceback.format_exc()}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.message.answer(
            f"Swipe error: {str(e)}",
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )

async def send_like_notification(from_user_id: int, to_user_id: int, from_profile: dict):
    """Send notification to user who was liked"""
    try:
        if not bot_instance:
            logging.error("Bot instance not available for notifications")
            return
            
        to_user_lang = db.get_user_language(to_user_id)
        
        # Create "View profile" button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=get_message("view_profile", to_user_lang),
                callback_data=f"view_like_profile_{from_user_id}"
            )]
        ])
        
        # Send notification
        await bot_instance.send_message(
            to_user_id,
            get_message("someone_liked_you", to_user_lang),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        logging.info(f"Like notification sent: {from_user_id} -> {to_user_id}")
        
    except Exception as e:
        logging.error(f"Error sending like notification: {e}")

def get_who_pays_text(who_pays: str, language: str) -> str:
    """Get formatted text for who pays preference"""
    who_pays_texts = {
        'ru': {
            'i_treat': '🍺 Я угощаю',
            'someone_treats': '🤝 Кто-то угощает',
            'each_self': '💰 Каждый платит за себя'
        },
        'ua': {
            'i_treat': '🍺 Я заплачу',
            'someone_treats': '🤝 Хтось заплатить',
            'each_self': '💰 Кожен платить за себе'
        },
        'en': {
            'i_treat': '🍺 I treat',
            'someone_treats': '🤝 Someone treats',
            'each_self': '💰 Each pays for themselves'
        }
    }
    return who_pays_texts.get(language, who_pays_texts['ru']).get(who_pays, '🤝 Кто платит')

async def send_match_notifications(user1_id: int, user2_id: int):
    """Send match notifications to both users with block handling"""
    try:
        if not bot_instance:
            logging.error("ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Bot instance not available")
            return
            
        # Get profiles and languages
        profile1 = db.get_profile(user1_id)
        profile2 = db.get_profile(user2_id)
        
        if not profile1 or not profile2:
            logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Missing profile data - user1={bool(profile1)}, user2={bool(profile2)}")
            return
        
        lang1 = profile1.get('language', 'ru')
        lang2 = profile2.get('language', 'ru')
        
        # Get icebreaker
        icebreaker = db.get_icebreaker()
        
        # Create user links
        user1_link = create_user_link(profile1)
        user2_link = create_user_link(profile2)
        
        # Send to user1
        match_message1 = (
            f"{get_message('mutual_like', lang1)}\n\n"
            f"👤 {profile2['name']}, {profile2['age']}\n"
            f"⚧️ {profile2.get('gender', '👤').title()}\n"
            f"🏙️ {profile2['city'].title()}\n"
            f"🍺 {profile2['favorite_drink']}\n"
            f"💰 {get_who_pays_text(profile2.get('who_pays', 'each_self'), lang1)}\n\n"
            f"{get_message('write_to_user', lang1, username=profile2.get('username', user2_link))}\n\n"
            f"{get_message('conversation_starter', lang1)} {icebreaker}"
        )
        
        # Send to user2
        match_message2 = (
            f"{get_message('mutual_like', lang2)}\n\n"
            f"👤 {profile1['name']}, {profile1['age']}\n"
            f"⚧️ {profile1.get('gender', '👤').title()}\n"
            f"🏙️ {profile1['city'].title()}\n"
            f"🍺 {profile1['favorite_drink']}\n"
            f"💰 {get_who_pays_text(profile1.get('who_pays', 'each_self'), lang2)}\n\n"
            f"{get_message('write_to_user', lang2, username=profile1.get('username', user1_link))}\n\n"
            f"{get_message('conversation_starter', lang2)} {icebreaker}"
        )
        
        # Send notifications with block handling
        notifications_sent = []
        
        try:
            await bot_instance.send_message(
                user1_id,
                match_message1,
                reply_markup=get_main_keyboard(lang1),
                parse_mode='HTML'
            )
            notifications_sent.append(f"user1:{user1_id}")
            logging.info(f"DEBUG: Match notification sent to user1:{user1_id}")
        except Exception as e:
            logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Не удалось отправить user1:{user1_id} - {e}")
            if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Пользователь user1:{user1_id} заблокировал бота")
            else:
                logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Другая ошибка для user1:{user1_id} - {e}")
        
        try:
            await bot_instance.send_message(
                user2_id,
                match_message2,
                reply_markup=get_main_keyboard(lang2),
                parse_mode='HTML'
            )
            notifications_sent.append(f"user2:{user2_id}")
            logging.info(f"DEBUG: Match notification sent to user2:{user2_id}")
        except Exception as e:
            logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Не удалось отправить user2:{user2_id} - {e}")
            if "blocked" in str(e).lower() or "chat not found" in str(e).lower():
                logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Пользователь user2:{user2_id} заблокировал бота")
            else:
                logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Другая ошибка для user2:{user2_id} - {e}")
        
        # Log final result
        if notifications_sent:
            logging.info(f"DEBUG: Match notifications sent successfully: {user1_id} <-> {user2_id} | Sent: {', '.join(notifications_sent)}")
        else:
            logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Не удалось отправить ни одно уведомление для мэтча {user1_id} <-> {user2_id}")
        
    except Exception as e:
        logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Критическая ошибка для мэтча {user1_id} <-> {user2_id}: {e}")
        import traceback
        logging.error(f"ОШИБКА В ШАГЕ SEND_MATCH_NOTIFICATIONS: Traceback: {traceback.format_exc()}")

def create_user_link(profile: dict) -> str:
    """Create secure user link (username or HTML tg://user?id= link)"""
    username = profile.get('username')
    if username:
        return f"@{username}"
    else:
        return f'<a href="tg://user?id={profile["user_id"]}">Перейти в профиль</a>'

@router.callback_query(F.data.startswith("view_like_profile_"))
async def view_like_profile_callback(callback: types.CallbackQuery):
    """Handle viewing profile of user who liked you"""
    try:
        from_user_id = int(callback.data.split("_")[3])
        from_profile = db.get_profile(from_user_id)
        
        if not from_profile:
            await callback.answer("Profile not found")
            return
        
        user_lang = db.get_user_language(callback.from_user.id)
        
        # Create profile caption
        caption = (
            f"👤 {from_profile['name']}, {from_profile['age']}\n"
            f"🏙️ {from_profile['city'].title()}\n"
            f"🍺 {from_profile['favorite_drink']}"
        )
        
        # Create like button
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❤️", callback_data=f"like_back_{from_user_id}")]
        ])
        
        if from_profile.get('photo_id'):
            await callback.message.answer_photo(
                photo=from_profile['photo_id'],
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(
                get_message("no_photo", user_lang) + f"\n\n{caption}",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Error in view_like_profile_callback: {e}")
        await callback.answer("Error loading profile")

@router.callback_query(F.data.startswith("like_back_"))
async def like_back_callback(callback: types.CallbackQuery):
    """Handle liking back from notification"""
    try:
        from_user_id = int(callback.data.split("_")[2])
        to_user_id = callback.from_user.id
        
        # Add like
        db.add_like(to_user_id, from_user_id)
        
        # Check for mutual like (should be true now)
        if db.check_mutual_like(to_user_id, from_user_id):
            # MATCH! Save to database and send notifications
            match_created = db.create_match(to_user_id, from_user_id)
            logging.info(f"DEBUG: Match created in like_back_callback: {match_created} between {to_user_id} and {from_user_id}")
            
            await send_match_notifications(to_user_id, from_user_id)
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"Error in like_back_callback: {e}")
        await callback.answer("Error")

async def show_premium(message: types.Message):
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id)

        profile = db.get_profile(user_id)
        if profile and int(profile.get('is_premium') or 0) == 1:
            await message.answer(
                get_message("premium_already_active", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_message("btn_buy_premium", lang), callback_data="buy_premium")]
        ])

        await message.answer(
            f"{get_message('premium_title', lang)}\n\n{get_message('premium_features', lang)}",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in show_premium: {e}")
        lang = await get_lang(message.from_user.id)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def show_filters(message: types.Message):
    """Show filters screen with premium options"""
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id)

        profile = db.get_profile(user_id)
        if profile and int(profile.get('is_premium') or 0) == 1:
            # User has premium - show actual filters
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_message("filter_gender", lang), callback_data="filter_gender")],
                [InlineKeyboardButton(text=get_message("filter_who_pays", lang), callback_data="filter_who_pays")],
                [InlineKeyboardButton(text=get_message("btn_back", lang), callback_data="filters_back")]
            ])
            await message.answer(
                get_message("premium_filters", lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            # User doesn't have premium - show offer
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_message("btn_buy_filters", lang), callback_data="buy_filters")],
                [InlineKeyboardButton(text=get_message("btn_back", lang), callback_data="filters_back")]
            ])
            await message.answer(
                get_message("filters_premium_required", lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Error in show_filters: {e}")
        lang = await get_lang(message.from_user.id)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def process_event_name(message: types.Message, state: FSMContext):
    """Process event name input"""
    try:
        lang = await get_lang(message.from_user.id, state)
        
        if not message.text or not message.text.strip():
            await message.answer(get_message("event_name_error", lang), parse_mode='HTML')
            return
            
        if len(message.text.strip()) < 2:
            await message.answer(get_message("event_name_error", lang), parse_mode='HTML')
            return
        
        await state.update_data(event_name=message.text.strip())
        await state.set_state(EventStates.event_place)
        
    except Exception as e:
        logging.error(f"Error in process_event_name: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.callback_query(F.data == "filter_gender")
async def filter_gender_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle gender filter selection"""
    try:
        user_id = callback.from_user.id
        lang = await get_lang(user_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨 Мужчины", callback_data="set_filter_gender_male")],
            [InlineKeyboardButton(text="👩 Женщины", callback_data="set_filter_gender_female")],
            [InlineKeyboardButton(text="🧑 Все", callback_data="set_filter_gender_all")],
            [InlineKeyboardButton(text=get_message("btn_back", lang), callback_data="filters_main")]
        ])
        
        await callback.answer()
        await callback.message.answer(
            "🔍 Выберите гендер для поиска:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in filter_gender_callback: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "filter_who_pays")
async def filter_who_pays_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle who pays filter selection"""
    try:
        user_id = callback.from_user.id
        lang = await get_lang(user_id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍺 Я угощаю", callback_data="set_filter_who_pays_i_treat")],
            [InlineKeyboardButton(text="🤝 Кто-то угощает", callback_data="set_filter_who_pays_you_treat")],
            [InlineKeyboardButton(text="💰 Каждый платит за себя", callback_data="set_filter_who_pays_split")],
            [InlineKeyboardButton(text="🎲 Любой вариант", callback_data="set_filter_who_pays_any")],
            [InlineKeyboardButton(text=get_message("btn_back", lang), callback_data="filters_main")]
        ])
        
        await callback.answer()
        await callback.message.answer(
            "💰 Кто платит за напитки:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in filter_who_pays_callback: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data.startswith("set_filter_gender_"))
async def set_filter_gender_callback(callback: types.CallbackQuery, state: FSMContext):
    """Set gender filter"""
    try:
        user_id = callback.from_user.id
        filter_value = callback.data.split("_")[-1]  # male, female, all
        
        # Save filter to database
        filter_saved = db.save_user_filters(user_id, gender_filter=filter_value)
        logging.info(f"DEBUG: Gender filter saved: {filter_saved} for user {user_id}")
        
        filter_names = {
            "male": "👨 Мужчины",
            "female": "👩 Женщины", 
            "all": "🧑 Все"
        }
        
        await callback.answer(f"✅ Фильтр установлен: {filter_names.get(filter_value)}")
        await callback.message.answer(
            f"✅ Фильтр по гендеру установлен: {filter_names.get(filter_value)}\n\n"
            f"Теперь знакомства будут показывать только {filter_names.get(filter_value).lower()}",
            reply_markup=get_dating_keyboard(await get_lang(user_id)),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in set_filter_gender_callback: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data.startswith("set_filter_who_pays_"))
async def set_filter_who_pays_callback(callback: types.CallbackQuery, state: FSMContext):
    """Set who pays filter"""
    try:
        user_id = callback.from_user.id
        filter_value = callback.data.split("_")[-1]  # i_treat, you_treat, split, any
        
        # Save filter to database
        filter_saved = db.save_user_filters(user_id, who_pays_filter=filter_value)
        logging.info(f"DEBUG: Who pays filter saved: {filter_saved} for user {user_id}")
        
        filter_names = {
            "i_treat": "🍺 Я угощаю",
            "you_treat": "🤝 Кто-то угощает",
            "split": "💰 Каждый платит за себя",
            "any": "🎲 Любой вариант"
        }
        
        filter_name = filter_names.get(filter_value, "🎲 Любой вариант")
        
        await callback.answer(f"✅ Фильтр установлен: {filter_name}")
        await callback.message.answer(
            f"✅ Фильтр по оплате установлен: {filter_name}\n\n"
            f"Теперь знакомства будут показывать только тех, кто {filter_name.lower()}",
            reply_markup=get_dating_keyboard(await get_lang(user_id)),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in set_filter_who_pays_callback: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "filters_back")
async def filters_back_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle back button from filters to main menu"""
    try:
        lang = await get_lang(callback.from_user.id)
        await callback.answer()
        await callback.message.answer(
            "🔙 Возврат в главное меню",
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in filters_back_callback: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data == "filters_main")
async def filters_main_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle back button to main filters menu"""
    try:
        user_id = callback.from_user.id
        lang = await get_lang(user_id)

        profile = db.get_profile(user_id)
        if profile and int(profile.get('is_premium') or 0) == 1:
            # User has premium - show actual filters
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_message("filter_gender", lang), callback_data="filter_gender")],
                [InlineKeyboardButton(text=get_message("filter_who_pays", lang), callback_data="filter_who_pays")],
                [InlineKeyboardButton(text=get_message("btn_back", lang), callback_data="filters_back")]
            ])
            await callback.answer()
            await callback.message.answer(
                get_message("premium_filters", lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
            # User doesn't have premium - show offer
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_message("btn_buy_filters", lang), callback_data="buy_filters")],
                [InlineKeyboardButton(text=get_message("btn_back", lang), callback_data="filters_back")]
            ])
            await callback.answer()
            await callback.message.answer(
                get_message("filters_premium_required", lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Error in filters_main_callback: {e}")
        await callback.answer("❌ Ошибка")

@router.message(EventStates.event_name)
async def process_event_name_handler(message: types.Message, state: FSMContext):
    await process_event_name(message, state)

@router.message(EventStates.event_place)
async def process_event_place(message: types.Message, state: FSMContext):
    """Process event place input"""
    try:
        lang = await get_lang(message.from_user.id, state)
        
        if not message.text or not message.text.strip():
            await message.answer(get_message("event_place_error", lang), parse_mode='HTML')
            return
        
        await state.update_data(event_place=message.text.strip())
        await state.set_state(EventStates.event_price)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_message("price_free", lang), callback_data="price_free")],
            [InlineKeyboardButton(text=get_message("price_paid", lang), callback_data="price_paid")]
        ])
        await message.answer(get_message("event_price_prompt", lang), reply_markup=keyboard, parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Error in process_event_place: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("event_place_error", lang), parse_mode='HTML')

@router.callback_query(F.data.startswith("price_"), EventStates.event_price)
async def process_event_price(callback: types.CallbackQuery, state: FSMContext):
    """Process event price selection"""
    try:
        lang = await get_lang(callback.from_user.id, state)
        price_type = callback.data.split("_")[1]
        
        await state.update_data(event_price=price_type)
        await state.set_state(EventStates.event_description)
        await callback.answer()
        await callback.message.answer(get_message("event_description_prompt", lang), parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Error in process_event_price: {e}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.message.answer(get_message("use_buttons_error", lang), parse_mode='HTML')

@router.message(EventStates.event_description)
async def process_event_description(message: types.Message, state: FSMContext):
    """Process event description and create event"""
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id, state)
        
        if not message.text or not message.text.strip():
            await message.answer(get_message("event_description_error", lang), parse_mode='HTML')
            return
        
        user_data = await state.get_data()
        user_profile = db.get_profile(user_id)

        city_value = (user_profile.get('city_display') or user_profile.get('city') or '')
        
        success = db.create_event(
            creator_id=user_id,
            name=user_data['event_name'],
            place=user_data['event_place'],
            price_type=user_data['event_price'],
            description=message.text.strip(),
            city=city_value
        )
        
        await state.clear()
        
        if success:
            await message.answer(
                get_message("event_created", lang,
                         name=user_data['event_name'],
                         place=user_data['event_place'],
                         price=get_message(f"price_{user_data['event_price']}", lang),
                         creator=user_profile['name'],
                         description=message.text.strip()[:100] + "...",
                         city=(user_profile.get('city_display') or user_profile.get('city') or '').title()),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(
                get_message("event_error", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
        
    except Exception as e:
        logging.error(f"Error in process_event_description: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("event_error", lang), parse_mode='HTML')

async def create_event_start(message: types.Message, state: FSMContext):
    """Start event creation process"""
    try:
        lang = await get_lang(message.from_user.id, state)
        user_profile = db.get_profile(message.from_user.id)
        
        if not user_profile:
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        await message.answer(
            get_message("create_event_start", lang),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        await state.set_state(EventStates.event_name)
        
    except Exception as e:
        logging.error(f"Error in create_event_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def show_events_feed(message: types.Message):
    """Show events in user's city using city_normalized"""
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id)
        user_profile = db.get_profile(user_id)
        
        if not user_profile:
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        user_city_display = (user_profile.get('city_display') or user_profile.get('city') or '')
        user_city_key = user_profile.get('city_normalized') or user_city_display
        
        # Get events from user city and nearby cities (use normalized key if present)
        events = db.get_events_by_city_nearby(user_city_key, limit=10)
        
        if not events:
            await message.answer(
                get_message("no_events_in_city", lang, city=user_city_display.title()),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        await message.answer(
            f"📅 Тусовки в {user_city_display.title()} и рядом:",
            parse_mode='HTML'
        )
        
        for event in events:
            price_text = get_message("price_free" if event['price_type'] == 'free' else "price_paid", lang)
            is_participating = db.is_user_participating(event['id'], user_id)
            button_text = get_message("leave_event", lang) if is_participating else get_message("join_event", lang)
            button_callback = f"leave_event_{event['id']}" if is_participating else f"join_event_{event['id']}"
            
            # Calculate time remaining
            time_remaining = db.get_time_remaining(event['expires_at'])
            is_expired = time_remaining == "00:00"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=button_text, callback_data=button_callback)]
            ])
            
            # Create event text with time remaining and city info
            status_text = get_message("event_expired", lang) if is_expired else get_message("time_remaining", lang, time=time_remaining)
            city_info = f"🏙️ {event['city'].title()}" if event['city'] != user_city_display else ""
            
            event_text = (
                f"📅 <b>{event['name']}</b>\n"
                f"📍 {event['place']}\n"
                f"💰 {price_text}\n"
                f"📝 {event['description']}\n"
                f"👤 Создатель: {event['creator_name']}\n"
                f"👥 Участников: {event.get('current_members', 0)}\n"
                f"{city_info}\n"
                f"{status_text}"
            )
            
            await message.answer(
                event_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
    except Exception as e:
        logging.error(f"Error in show_events_feed: {e}")
        import traceback
        logging.error(f"DEBUG: Traceback: {traceback.format_exc()}")
        lang = await get_lang(message.from_user.id)
        await message.answer(get_message("error", lang), parse_mode='HTML')

        
        await message.answer(
            get_message("matches_message", lang),
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error in show_matches: {e}")
        lang = await get_lang(message.from_user.id)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.callback_query(F.data.startswith("matches_prev_"))
async def matches_prev_callback(callback: types.CallbackQuery):
    """Handle previous matches page"""
    try:
        offset = int(callback.data.split("_")[2])
        await callback.answer()
        await show_matches(callback.message, offset - 5)
    except Exception as e:
        logging.error(f"Error in matches_prev_callback: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data.startswith("matches_next_"))
async def matches_next_callback(callback: types.CallbackQuery):
    """Handle next matches page"""
    try:
        offset = int(callback.data.split("_")[2])
        await callback.answer()
        await show_matches(callback.message, offset + 5)
    except Exception as e:
        logging.error(f"Error in matches_next_callback: {e}")
        await callback.answer("❌ Ошибка")

async def show_matches(message: types.Message, offset: int = 0):
    """Show user's matches with pagination and usernames"""
    try:
        lang = await get_lang(message.from_user.id)
        matches = db.get_user_matches(message.from_user.id)
        
        # Apply pagination manually
        total_matches = len(matches)
        paginated_matches = matches[offset:offset + 5]
        
        if not matches and offset == 0:
            await message.answer(
                get_message("no_matches", lang),
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        if not paginated_matches and offset > 0:
            await message.answer(
                "Больше нет метчей",
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        await message.answer(f"💕 Ваши метчи (показано {offset + 1}-{offset + len(paginated_matches)} из {total_matches}):", parse_mode='HTML')
        
        for match in paginated_matches:
            # Get who pays text
            who_pays_text = get_who_pays_text(match.get('who_pays', 'each_self'), lang)
            
            caption = (
                f"👤 {match['name']}, {match['age']} лет\n"
                f"⚧️ {match.get('gender', '👤').title()}\n"
                f"🏙️ {match['city'].title()}\n"
                f"🍺 {match['favorite_drink']}\n"
                f"💰 {who_pays_text}\n"
                f"🔗 @{match.get('username', 'нет юзернейма')}"
            )
            
            if match.get('photo_id'):
                await message.answer_photo(
                    photo=match['photo_id'],
                    caption=caption
                )
            else:
                await message.answer(
                    get_message("no_photo", lang) + f"\n\n{caption}",
                    parse_mode='HTML'
                )
            
            await message.answer(get_message("photo_separator", lang))
        
        # Add pagination buttons
        keyboard_buttons = []
        
        # Previous button
        if offset > 0:
            keyboard_buttons.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"matches_prev_{offset - 5}")
            )
        
        # Next button
        if offset + 5 < total_matches:  # There are more matches
            keyboard_buttons.append(
                InlineKeyboardButton(text="➡️ Далее", callback_data=f"matches_next_{offset + 5}")
            )
        
        if keyboard_buttons:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[keyboard_buttons])
            await message.answer("Навигация:", reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"Error in show_matches: {e}")
        lang = await get_lang(message.from_user.id)
        await message.answer(get_message("error", lang), parse_mode='HTML')

# GENERAL TEXT HANDLER - MUST BE LAST TO CATCH ONLY UNHANDLED TEXT MESSAGES
@router.message(StateFilter(None), F.text)
async def handle_main_menu(message: types.Message, state: FSMContext):
    """Handle main menu button clicks using section navigation"""
    try:
        logging.info(f"handle_main_menu called with text: '{message.text}' from user {message.from_user.id}")

        user_profile = db.get_profile(message.from_user.id)
        if user_profile and user_profile.get('language'):
            language = user_profile['language']
        else:
            language = 'ru'

        # Sections - safe get_message calls
        try:
            section_profile_text = get_message("section_profile", language)
            section_dating_text = get_message("section_dating", language)
            section_companies_text = get_message("section_companies", language)
            section_events_text = get_message("section_events", language)
            section_settings_text = get_message("section_settings", language)
            back_to_main_text = get_message("back_to_main", language)
        except Exception as e:
            logging.error(f"Error getting section messages: {e}")
            # Fallback to hardcoded Russian
            section_profile_text = "👤 Мой профиль"
            section_dating_text = "💕 Знакомства"
            section_companies_text = "🎉 Компании"
            section_events_text = "📅 Тусовки"
            section_settings_text = "⚙️ Настройки"
            back_to_main_text = "⬅️ Назад"

        # Buttons
        fill_profile_text = get_message("btn_fill_profile", language)
        edit_profile_text = get_message("btn_edit_profile", language)
        delete_profile_text = get_message("btn_delete_profile", language)
        my_matches_text = get_message("btn_my_matches", language)

        find_dating_my_city_text = get_message("btn_find_dating_my_city", language)
        find_dating_other_city_text = get_message("btn_find_dating_other_city", language)

        create_event_text = get_message("btn_create_event", language)
        view_events_text = get_message("btn_view_events", language)
        my_events_text = get_message("btn_my_events", language)

        create_company_text = get_message("btn_create_company", language)
        find_companies_text = get_message("btn_find_companies", language)
        my_companies_text = get_message("btn_my_companies", language)

        filters_text = get_message("btn_filters", language)
        change_lang_text = "🌐 Сменить язык / Change Language"

        # Edit profile buttons
        btn_edit_name_text = get_message("btn_edit_name", language)
        btn_edit_age_text = get_message("btn_edit_age", language)
        btn_edit_gender_text = get_message("btn_edit_gender", language)
        btn_edit_city_text = get_message("btn_edit_city", language)
        btn_edit_drink_text = get_message("btn_edit_drink", language)
        btn_edit_photo_text = get_message("btn_edit_photo", language)
        btn_edit_who_pays_text = get_message("btn_edit_who_pays", language)

        current_state = await state.get_state()
        allowed_menu_texts = {
            section_profile_text,
            section_dating_text,
            section_companies_text,
            section_events_text,
            section_settings_text,
            back_to_main_text,
            fill_profile_text,
            edit_profile_text,
            delete_profile_text,
            my_matches_text,
            find_dating_my_city_text,
            find_dating_other_city_text,
            create_event_text,
            view_events_text,
            my_events_text,
            create_company_text,
            find_companies_text,
            my_companies_text,
            filters_text,
            change_lang_text,
            btn_edit_name_text,
            btn_edit_age_text,
            btn_edit_gender_text,
            btn_edit_city_text,
            btn_edit_drink_text,
            btn_edit_photo_text,
            btn_edit_who_pays_text,
        }

        # If user is in some FSM step (e.g. entering city/name/etc), do not spam "welcome".
        # Only react to menu buttons; otherwise let the state-specific handlers process the text.
        if current_state is not None and message.text not in allowed_menu_texts:
            return
        if current_state is not None and message.text in allowed_menu_texts:
            await state.clear()

        # Navigation
        if message.text == section_profile_text:
            await show_profile_screen(message, state)
            return
        if message.text == section_dating_text:
            await message.answer(get_message("welcome", language), reply_markup=get_dating_keyboard(language), parse_mode='HTML')
            return
        if message.text == section_companies_text:
            await message.answer(get_message("section_companies", language), reply_markup=get_companies_keyboard(language), parse_mode='HTML')
            return
        if message.text == section_events_text:
            await message.answer(get_message("section_events", language), reply_markup=get_events_keyboard(language), parse_mode='HTML')
            return
        if message.text == section_settings_text:
            await message.answer(get_message("section_settings", language), reply_markup=get_settings_keyboard(language), parse_mode='HTML')
            return
        if message.text == back_to_main_text:
            await message.answer(get_message("welcome", language), reply_markup=get_main_keyboard(language), parse_mode='HTML')
            return

        # Actions
        if message.text == fill_profile_text:
            await fill_profile_start(message, state)
            return
        if message.text == edit_profile_text:
            await edit_profile_start(message, state)
            return
        if message.text == delete_profile_text:
            await delete_profile_start(message, state)
            return
        if message.text == my_matches_text:
            await show_matches(message)
            return

        if message.text == find_dating_my_city_text:
            await find_dating_my_city_start(message, state)
            return
        if message.text == find_dating_other_city_text:
            await find_dating_other_city_start(message, state)
            return

        if message.text == create_event_text:
            await create_event_start(message, state)
            return
        if message.text == view_events_text:
            await show_events_feed(message)
            return
        if message.text == my_events_text:
            await show_my_events(message)
            return

        if message.text == create_company_text:
            await create_company_start(message, state)
            return
        if message.text == find_companies_text:
            await find_companies_start(message, state)
            return
        if message.text == my_companies_text:
            await show_my_companies(message)
            return

        if message.text == filters_text:
            await show_filters(message)
            return
        if message.text == change_lang_text:
            await show_language_selection(message)
            return

        # Edit profile actions
        if message.text == btn_edit_name_text:
            await edit_name_start(message, state)
            return
        if message.text == btn_edit_age_text:
            await edit_age_start(message, state)
            return
        if message.text == btn_edit_gender_text:
            await edit_gender_start(message, state)
            return
        if message.text == btn_edit_city_text:
            await edit_city_start(message, state)
            return
        if message.text == btn_edit_drink_text:
            await edit_drink_start(message, state)
            return
        if message.text == btn_edit_photo_text:
            await edit_photo_start(message, state)
            return
        if message.text == btn_edit_who_pays_text:
            await edit_who_pays_start(message, state)
            return

        logging.warning(f"Unknown button text: '{message.text}'")
        await message.answer(get_message("welcome", language), reply_markup=get_main_keyboard(language), parse_mode='HTML')

    except Exception as e:
        logging.error(f"Error in handle_main_menu: {e}")
        await message.answer(get_message("error", 'ru'), parse_mode='HTML')

@router.callback_query(F.data == "buy_premium")
async def buy_premium_callback(callback: types.CallbackQuery):
    """Send Telegram Stars invoice for Premium (150 XTR)"""
    try:
        user_id = callback.from_user.id
        lang = get_user_language(user_id)

        profile = db.get_profile(user_id)
        if not profile:
            await callback.answer()
            await callback.message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        if profile and int(profile.get('is_premium') or 0) == 1:
            await callback.answer(get_message("premium_already_active", lang))
            return

        payload = f"{PREMIUM_PAYLOAD_PREFIX}{user_id}"

        await callback.answer()
        await callback.bot.send_invoice(
            chat_id=user_id,
            title="💎 Drink Bot Premium",
            description="Premium access",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label="Premium", amount=PREMIUM_STARS_PRICE)],
        )
    except Exception as e:
        logging.error(f"Error in buy_premium_callback: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer(get_message("premium_payment_error", lang), show_alert=True)

@router.callback_query(F.data == "buy_filters")
async def buy_filters_callback(callback: types.CallbackQuery):
    """Send Telegram Stars invoice for Filters (200 XTR)"""
    try:
        user_id = callback.from_user.id
        lang = get_user_language(user_id)

        profile = db.get_profile(user_id)
        if not profile:
            await callback.answer()
            await callback.message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        if profile and int(profile.get('is_premium') or 0) == 1:
            await callback.answer(get_message("premium_already_active", lang))
            return

        payload = f"filters_200:{user_id}"

        await callback.answer()
        await callback.bot.send_invoice(
            chat_id=user_id,
            title="🔍 Drink Bot Filters",
            description="Premium filters access",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label="Filters", amount=200)],
        )
    except Exception as e:
        logging.error(f"Error in buy_filters_callback: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer(get_message("premium_payment_error", lang), show_alert=True)

@router.callback_query(F.data == "filters_back")
async def filters_back_callback(callback: types.CallbackQuery):
    """Handle back button from filters"""
    try:
        await callback.answer()
        lang = get_user_language(callback.from_user.id)
        await callback.message.answer(
            get_message("welcome", lang),
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in filters_back_callback: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer(get_message("error", lang))

@router.callback_query(F.data.startswith("filter_"))
async def filter_options_callback(callback: types.CallbackQuery):
    """Handle filter options (only for premium users)"""
    try:
        await callback.answer()
        lang = get_user_language(callback.from_user.id)
        await callback.message.answer(
            get_message("premium_only", lang),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in filter_options_callback: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer(get_message("error", lang))


@router.pre_checkout_query()
async def premium_pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    """Validate Stars payment before checkout"""
    try:
        user_id = pre_checkout_query.from_user.id
        lang = get_user_language(user_id)

        ok = True
        error_message = None

        # Check if this is premium payment or filters payment
        is_premium = pre_checkout_query.invoice_payload.startswith(PREMIUM_PAYLOAD_PREFIX)
        is_filters = pre_checkout_query.invoice_payload.startswith("filters_200:")
        
        if not is_premium and not is_filters:
            ok = False
            error_message = get_message("premium_payment_error", lang)
        else:
            try:
                if is_premium:
                    payload_user_id = int(pre_checkout_query.invoice_payload.split(":", 1)[1])
                else:  # is_filters
                    payload_user_id = int(pre_checkout_query.invoice_payload.split(":", 1)[1])
            except Exception:
                payload_user_id = None

            if payload_user_id != user_id:
                ok = False
                error_message = get_message("premium_payment_error", lang)

        if ok:
            profile = db.get_profile(user_id)
            if profile and int(profile.get('is_premium') or 0) == 1:
                ok = False
                error_message = get_message("premium_already_active", lang)

        await pre_checkout_query.answer(ok=ok, error_message=error_message)
    except Exception as e:
        logging.error(f"Error in premium_pre_checkout: {e}")
        try:
            await pre_checkout_query.answer(ok=False, error_message="Payment error")
        except Exception:
            pass


@router.message(F.successful_payment)
async def premium_successful_payment(message: types.Message):
    """Activate premium after successful Stars payment"""
    try:
        user_id = message.from_user.id
        lang = get_user_language(user_id)

        profile = db.get_profile(user_id)
        if not profile:
            await message.answer(get_message("premium_payment_error", lang), parse_mode='HTML')
            return

        sp = message.successful_payment
        if not sp:
            return

        # Check if this is premium payment (500 XTR) or filters payment (200 XTR)
        is_premium = sp.invoice_payload.startswith(PREMIUM_PAYLOAD_PREFIX)
        is_filters = sp.invoice_payload.startswith("filters_200:")
        
        if is_premium:
            # Premium payment validation
            if sp.currency != "XTR" or sp.total_amount != PREMIUM_STARS_PRICE:
                logging.warning(f"Unexpected premium payment: user={user_id}, currency={sp.currency}, amount={sp.total_amount}")
                await message.answer(get_message("premium_payment_error", lang), parse_mode='HTML')
                return

            if not sp.invoice_payload.startswith(PREMIUM_PAYLOAD_PREFIX):
                logging.warning(f"Unexpected premium payload: user={user_id}, payload={sp.invoice_payload}")
                await message.answer(get_message("premium_payment_error", lang), parse_mode='HTML')
                return

            # Activate premium
            db.update_profile(user_id, is_premium=1)
            await message.answer(
                get_message("premium_activated", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            logging.info(f"User {user_id} activated premium")
            
        elif is_filters:
            # Filters payment validation
            if sp.currency != "XTR" or sp.total_amount != 200:
                logging.warning(f"Unexpected filters payment: user={user_id}, currency={sp.currency}, amount={sp.total_amount}")
                await message.answer(get_message("premium_payment_error", lang), parse_mode='HTML')
                return

            if not sp.invoice_payload.startswith("filters_200:"):
                logging.warning(f"Unexpected filters payload: user={user_id}, payload={sp.invoice_payload}")
                await message.answer(get_message("premium_payment_error", lang), parse_mode='HTML')
                return

            # Activate premium for filters
            db.update_profile(user_id, is_premium=1)
            await message.answer(
                get_message("premium_activated", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            logging.info(f"User {user_id} activated premium via filters purchase")
        else:
            # Unknown payment type
            logging.warning(f"Unknown payment type: user={user_id}, payload={sp.invoice_payload}")
            await message.answer(get_message("premium_payment_error", lang), parse_mode='HTML')
            return

    except Exception as e:
        logging.error(f"Error in premium_successful_payment: {e}")
        lang = get_user_language(message.from_user.id)
        await message.answer(get_message("premium_payment_error", lang), parse_mode='HTML')

@router.callback_query(F.data.startswith("join_event_"))
async def join_event_callback(callback: types.CallbackQuery):
    """Handle joining an event"""
    try:
        language = get_user_language(callback.from_user.id)
        event_id = int(callback.data.split("_")[2])
        
        logging.info(f"DEBUG: User {callback.from_user.id} trying to join event {event_id}")
        
        # Check if already participating
        if db.is_user_participating(event_id, callback.from_user.id):
            await callback.answer("❌ Вы уже участвуете в этом событии")
            return
        
        success = db.join_event(event_id, callback.from_user.id)
        
        if success:
            # Get event details
            event = db.get_event_by_id(event_id)
            if not event:
                await callback.answer(get_message("error", language))
                return
            participants = db.get_event_participants(event_id)
            
            creator_id = event.get('creator_id')
            creator_name = event.get('creator_name') or "Неизвестно"
            creator_username_raw = event.get('creator_username')
            if creator_username_raw:
                creator_contact = f"@{creator_username_raw.lstrip('@')}"
            elif creator_id:
                creator_contact = f'<a href="tg://user?id={creator_id}">Написать создателю</a>'
            else:
                creator_contact = "нет юзернейма"
            
            await callback.answer("✅ Вы присоединились к событию!")
            
            # Create success message with creator info
            success_message = get_message("event_joined_success", language, 
                count=len(participants) + 1,
                creator_name=creator_name,
                username=creator_contact)
            
            await callback.message.answer(
                success_message,
                reply_markup=get_events_keyboard(language),
                parse_mode='HTML'
            )
            
            logging.info(f"DEBUG: User {callback.from_user.id} successfully joined event {event_id}")
        else:
            await callback.answer("❌ Не удалось присоединиться к событию")
            
    except Exception as e:
        logging.error(f"Error in join_event_callback: {e}")
        await callback.answer("❌ Ошибка при присоединении к событию")

# ... (rest of the code remains the same)
@router.callback_query(F.data.startswith("leave_event_"))
async def leave_event_callback(callback: types.CallbackQuery):
    """Handle leaving an event"""
    try:
        language = get_user_language(callback.from_user.id)
        event_id = int(callback.data.split("_")[2])
        
        logging.info(f"DEBUG: User {callback.from_user.id} trying to leave event {event_id}")
        
        success = db.leave_event(event_id, callback.from_user.id)
        
        if success:
            await callback.answer("🚪 Вы покинули событие")
            await callback.message.answer(
                "🚪 Вы покинули событие",
                reply_markup=get_main_keyboard(language),
                parse_mode='HTML'
            )
            
            logging.info(f"DEBUG: User {callback.from_user.id} successfully left event {event_id}")
        else:
            await callback.answer("❌ Вы не участвуете в этом событии")
            
    except Exception as e:
        logging.error(f"Error in leave_event_callback: {e}")
        await callback.answer("❌ Ошибка при выходе из события")



async def edit_profile_start(message: types.Message, state: FSMContext):
    """Start separate profile editing process"""
    try:
        user_profile = db.get_profile(message.from_user.id)
        if not user_profile:
            lang = await get_lang(message.from_user.id, state)
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        lang = await get_lang(message.from_user.id, state)
        await message.answer(
            "📝 Выберите, что хотите изменить в анкете:",
            reply_markup=get_edit_profile_keyboard(lang),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error in edit_profile_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def delete_profile_start(message: types.Message, state: FSMContext):
    """Start profile deletion process with confirmation"""
    try:
        lang = await get_lang(message.from_user.id, state)
        
        # Show confirmation dialog
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_message("btn_yes", lang), callback_data="confirm_delete_profile"),
                InlineKeyboardButton(text=get_message("btn_no", lang), callback_data="cancel_delete_profile")
            ]
        ])
        
        await message.answer(
            get_message("confirm_delete_profile", lang),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error in delete_profile_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.callback_query(F.data == "confirm_delete_profile")
async def confirm_delete_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    """Confirm profile deletion"""
    try:
        user_id = callback.from_user.id
        lang = get_user_language(user_id)
        
        # Delete profile and all related data
        success = db.delete_profile(user_id)
        
        if success:
            await callback.answer()
            await callback.message.answer(
                get_message("profile_deleted", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            logging.info(f"DEBUG: User {user_id} profile deleted successfully")
        else:
            await callback.answer(get_message("error", lang))
        
        # Clear state
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in confirm_delete_profile_callback: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer(get_message("error", lang))

@router.callback_query(F.data == "cancel_delete_profile")
async def cancel_delete_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    """Cancel profile deletion"""
    try:
        lang = get_user_language(callback.from_user.id)
        await callback.answer()
        await callback.message.answer(
            get_message("action_cancelled", lang),
            reply_markup=get_profile_keyboard(lang),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error in cancel_delete_profile_callback: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer(get_message("error", lang))

# Separate edit field handlers
async def edit_name_start(message: types.Message, state: FSMContext):
    """Start name editing"""
    try:
        lang = await get_lang(message.from_user.id, state)
        field_name = get_message("field_name", lang)
        await message.answer(
            get_message("edit_field_prompt", lang, field=field_name),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        await state.set_state(SeparateEditStates.edit_name)
        
    except Exception as e:
        logging.error(f"Error in edit_name_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def edit_age_start(message: types.Message, state: FSMContext):
    """Start age editing"""
    try:
        lang = await get_lang(message.from_user.id, state)
        field_name = get_message("field_age", lang)
        await message.answer(
            get_message("edit_field_prompt", lang, field=field_name),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        await state.set_state(SeparateEditStates.edit_age)
        
    except Exception as e:
        logging.error(f"Error in edit_age_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def edit_gender_start(message: types.Message, state: FSMContext):
    """Start gender editing"""
    try:
        lang = await get_lang(message.from_user.id, state)
        
        # Send gender selection buttons
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_message("gender_male", lang), callback_data="edit_gender_male")],
            [InlineKeyboardButton(text=get_message("gender_female", lang), callback_data="edit_gender_female")],
            [InlineKeyboardButton(text=get_message("gender_other", lang), callback_data="edit_gender_other")],
            [InlineKeyboardButton(text=get_message("btn_cancel", lang), callback_data="edit_gender_cancel")]
        ])
        
        await message.answer(
            get_message("profile_gender_prompt", lang),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error in edit_gender_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def edit_city_start(message: types.Message, state: FSMContext):
    """Start city editing"""
    try:
        lang = await get_lang(message.from_user.id, state)
        field_name = get_message("field_city", lang)
        await message.answer(
            get_message("edit_field_prompt", lang, field=field_name),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        await state.set_state(SeparateEditStates.edit_city)
        
    except Exception as e:
        logging.error(f"Error in edit_city_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def edit_drink_start(message: types.Message, state: FSMContext):
    """Start drink editing"""
    try:
        lang = await get_lang(message.from_user.id, state)
        field_name = get_message("field_drink", lang)
        await message.answer(
            get_message("edit_field_prompt", lang, field=field_name),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        await state.set_state(SeparateEditStates.edit_favorite_drink)
        
    except Exception as e:
        logging.error(f"Error in edit_drink_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def edit_photo_start(message: types.Message, state: FSMContext):
    """Start photo editing"""
    try:
        lang = await get_lang(message.from_user.id, state)
        await message.answer(
            "📷 Отправьте новое фото или нажмите 'Пропустить' чтобы оставить текущее",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Пропустить", callback_data="skip_edit_photo_separate")]
            ]),
            parse_mode='HTML'
        )
        await state.set_state(SeparateEditStates.edit_photo)
        
    except Exception as e:
        logging.error(f"Error in edit_photo_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

async def edit_who_pays_start(message: types.Message, state: FSMContext):
    """Start who pays editing"""
    try:
        lang = await get_lang(message.from_user.id, state)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_message("who_pays_each_self", lang), callback_data="edit_who_pays_each_self")],
            [InlineKeyboardButton(text=get_message("who_pays_i_treat", lang), callback_data="edit_who_pays_i_treat")],
            [InlineKeyboardButton(text=get_message("who_pays_someone_treats", lang), callback_data="edit_who_pays_someone_treats")],
            [InlineKeyboardButton(text=get_message("btn_cancel", lang), callback_data="cancel_profile")]
        ])
        await message.answer(
            "💰 Кто платит за напитки?",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        await state.set_state(SeparateEditStates.edit_who_pays)
        
    except Exception as e:
        logging.error(f"Error in edit_who_pays_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(SeparateEditStates.edit_name)
async def process_edit_name_separate(message: types.Message, state: FSMContext):
    """Process separate name editing"""
    try:
        if not message.text or not message.text.strip():
            lang = await get_lang(message.from_user.id, state)
            await message.answer("Имя не может быть пустым. Попробуйте еще раз:")
            return
        
        user_id = message.from_user.id
        success = db.update_profile(user_id, name=message.text.strip())
        
        if success:
            logging.info(f"DEBUG: User {user_id} updated name to '{message.text.strip()}'")
            lang = await get_lang(user_id, state)
            await message.answer(
                get_message("name_updated", lang),
                reply_markup=get_edit_profile_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(get_message("error", lang))
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in process_edit_name_separate: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(SeparateEditStates.edit_age)
async def process_edit_age_separate(message: types.Message, state: FSMContext):
    """Process separate age editing"""
    try:
        lang = await get_lang(message.from_user.id, state)
        
        try:
            age = int(message.text.strip())
            if age < 18 or age > 100:
                await message.answer("Возраст должен быть от 18 до 100. Попробуйте еще раз:")
                return
        except ValueError:
            await message.answer("Пожалуйста, введите корректный возраст (число):")
            return
        
        user_id = message.from_user.id
        success = db.update_profile(user_id, age=age)
        
        if success:
            logging.info(f"DEBUG: User {user_id} updated age to {age}")
            lang = await get_lang(user_id, state)
            await message.answer(
                get_message("age_updated", lang),
                reply_markup=get_edit_profile_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(get_message("error", lang))
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in process_edit_age_separate: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(SeparateEditStates.edit_city)
async def process_edit_city_separate(message: types.Message, state: FSMContext):
    """Process separate city editing"""
    try:
        if not message.text or not message.text.strip():
            await message.answer("Город не может быть пустым. Попробуйте еще раз:")
            return
        
        user_id = message.from_user.id
        success = db.update_profile(user_id, city=message.text.strip())
        
        if success:
            logging.info(f"DEBUG: User {user_id} updated city to '{message.text.strip()}'")
            lang = await get_lang(user_id, state)
            await message.answer(
                get_message("city_updated", lang),
                reply_markup=get_edit_profile_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(get_message("error", lang))
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in process_edit_city_separate: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(SeparateEditStates.edit_favorite_drink)
async def process_edit_drink_separate(message: types.Message, state: FSMContext):
    """Process separate drink editing"""
    try:
        if not message.text or not message.text.strip():
            await message.answer("Напиток не может быть пустым. Попробуйте еще раз:")
            return
        
        user_id = message.from_user.id
        success = db.update_profile(user_id, favorite_drink=message.text.strip())
        
        if success:
            logging.info(f"DEBUG: User {user_id} updated favorite drink to '{message.text.strip()}'")
            lang = await get_lang(user_id, state)
            await message.answer(
                get_message("drink_updated", lang),
                reply_markup=get_edit_profile_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(get_message("error", lang))
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in process_edit_drink_separate: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(SeparateEditStates.edit_photo, F.photo)
async def process_edit_photo_separate(message: types.Message, state: FSMContext):
    """Process separate photo editing"""
    try:
        user_id = message.from_user.id
        success = db.update_profile(user_id, photo_id=message.photo[-1].file_id)
        
        if success:
            logging.info(f"DEBUG: User {user_id} updated photo")
            lang = await get_lang(user_id, state)
            await message.answer(
                get_message("photo_updated", lang),
                reply_markup=get_edit_profile_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await message.answer(get_message("error", lang))
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in process_edit_photo_separate: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(ProfileStates.age)
async def process_profile_age(message: types.Message, state: FSMContext):
    """Process profile age input"""
    try:
        user_id = message.from_user.id
        
        # Validate age
        try:
            age = int(message.text.strip())
            if age < 16 or age > 100:
                lang = await get_lang(user_id, state)
                await message.answer(get_message("profile_age_error", lang), parse_mode='HTML')
                return
        except ValueError:
            lang = await get_lang(user_id, state)
            await message.answer(get_message("profile_age_error", lang), parse_mode='HTML')
            return
        
        # Save age to state
        await state.update_data(age=age)
        logging.info(f"DEBUG: User {user_id} saved age: {age}")
        
        # Ask for city
        lang = await get_lang(user_id, state)
        await message.answer(
            get_message("profile_city_prompt", lang),
            parse_mode='HTML'
        )
        
        # Set next state
        await state.set_state(ProfileStates.city)
        logging.info(f"DEBUG: User {user_id} moved to city state")
        
    except Exception as e:
        logging.error(f"Error in process_profile_age: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(ProfileStates.city)
async def process_profile_city(message: types.Message, state: FSMContext):
    """Process profile city input"""
    try:
        user_id = message.from_user.id
        
        if not message.text or not message.text.strip():
            lang = await get_lang(user_id, state)
            await message.answer(get_message("profile_city_error", lang), parse_mode='HTML')
            return
        
        # Save city to state
        await state.update_data(city=message.text.strip())
        logging.info(f"DEBUG: User {user_id} saved city: '{message.text.strip()}'")
        
        # Ask for favorite drink
        lang = await get_lang(user_id, state)
        await message.answer(
            get_message("profile_drink_prompt", lang),
            parse_mode='HTML'
        )
        
        # Set next state
        await state.set_state(ProfileStates.favorite_drink)
        logging.info(f"DEBUG: User {user_id} moved to favorite_drink state")
        
    except Exception as e:
        logging.error(f"Error in process_profile_city: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(ProfileStates.favorite_drink)
async def process_profile_favorite_drink(message: types.Message, state: FSMContext):
    """Process profile favorite drink input"""
    try:
        user_id = message.from_user.id
        
        if not message.text or not message.text.strip():
            lang = await get_lang(user_id, state)
            await message.answer(get_message("profile_drink_error", lang), parse_mode='HTML')
            return
        
        # Save favorite drink to state
        await state.update_data(favorite_drink=message.text.strip())
        logging.info(f"DEBUG: User {user_id} saved favorite drink: '{message.text.strip()}'")
        
        # Ask for gender instead of who_pays
        lang = await get_lang(user_id, state)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👨 Мужчина", callback_data="profile_gender_male")],
            [InlineKeyboardButton(text="👩 Женщина", callback_data="profile_gender_female")],
            [InlineKeyboardButton(text="🧪 Другой", callback_data="profile_gender_other")]
        ])
        await message.answer(
            "Укажите ваш пол:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Set next state to gender
        await state.set_state(ProfileStates.gender)
        logging.info(f"DEBUG: User {user_id} moved to gender state")
        
    except Exception as e:
        logging.error(f"Error in process_profile_favorite_drink: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.callback_query(F.data.startswith("profile_gender_"))
async def process_profile_gender(callback: types.CallbackQuery, state: FSMContext):
    """Process profile gender selection"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        
        # Extract gender value
        gender = callback.data.split("_")[2]
        
        # Save to state
        await state.update_data(gender=gender)
        logging.info(f"DEBUG: User {user_id} saved gender: {gender}")
        
        # Get current state to determine next step
        current_state = await state.get_state()
        
        if current_state == ProfileStates.photo:
            # User was in photo state, now we can save the profile
            data = await state.get_data()
            
            # Save to database with all required parameters
            success = db.create_profile(
                user_id=user_id,
                name=data['name'],
                age=data['age'],
                gender=data['gender'],
                city=data['city'],
                favorite_drink=data['favorite_drink'],
                who_pays=data['who_pays'],
                photo_id=data['photo_id']
            )
            
            if success:
                lang = await get_lang(user_id, state)
                await callback.message.answer(
                    get_message("profile_saved", lang),
                    reply_markup=get_main_keyboard(lang),
                    parse_mode='HTML'
                )
                
                logging.info(f"DEBUG: User {user_id} successfully created profile after gender")
                
                # Clear state
                await state.clear()
            else:
                lang = await get_lang(user_id, state)
                await callback.message.answer(get_message("error", lang), parse_mode='HTML')
        else:
            # Normal flow - ask for who pays
            lang = await get_lang(user_id, state)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_message("who_pays_i_treat", lang), callback_data="profile_who_pays_i_treat")],
                [InlineKeyboardButton(text=get_message("who_pays_someone_treats", lang), callback_data="profile_who_pays_someone_treats")],
                [InlineKeyboardButton(text=get_message("who_pays_each_self", lang), callback_data="profile_who_pays_each_self")]
            ])
            await callback.message.answer(
                get_message("profile_who_pays_prompt", lang),
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            # Set next state
            await state.set_state(ProfileStates.who_pays)
            logging.info(f"DEBUG: User {user_id} moved to who_pays state")
        
    except Exception as e:
        logging.error(f"Error in process_profile_gender: {e}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.answer(get_message("error", lang))

@router.callback_query(F.data.startswith("profile_who_pays_"))
async def process_profile_who_pays(callback: types.CallbackQuery, state: FSMContext):
    """Process profile who pays selection"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        
        # Extract who_pays value - FIXED PARSING
        who_pays = "_".join(callback.data.split("_")[3:])
        
        # Save to state
        await state.update_data(who_pays=who_pays)
        logging.info(f"DEBUG: User {user_id} saved who_pays: {who_pays}")
        
        # Ask for photo
        lang = await get_lang(user_id, state)
        await callback.message.answer(
            get_message("profile_photo_prompt", lang),
            parse_mode='HTML'
        )
        
        # Set next state
        await state.set_state(ProfileStates.photo)
        logging.info(f"DEBUG: User {user_id} moved to photo state")
        
    except Exception as e:
        logging.error(f"Error in process_profile_who_pays: {e}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.answer(get_message("error", lang))

@router.message(ProfileStates.photo, F.photo)
async def process_profile_photo(message: types.Message, state: FSMContext):
    """Process profile photo input and save complete profile"""
    try:
        user_id = message.from_user.id
        
        # Save photo to state
        photo_id = message.photo[-1].file_id
        await state.update_data(photo_id=photo_id)
        logging.info(f"DEBUG: User {user_id} saved photo: {photo_id}")
        
        # Get all profile data
        data = await state.get_data()
        
        # Check if gender exists (fix for users who started before gender was added)
        if 'gender' not in data:
            logging.warning(f"DEBUG: User {user_id} missing gender, asking for it now")
            
            # Ask for gender
            lang = await get_lang(user_id, state)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👨 Мужчина", callback_data="profile_gender_male")],
                [InlineKeyboardButton(text="👩 Женщина", callback_data="profile_gender_female")],
                [InlineKeyboardButton(text="🧪 Другой", callback_data="profile_gender_other")]
            ])
            await message.answer(
                "Укажите ваш пол (этот шаг был добавлен недавно):",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            
            # Stay in photo state (we have photo, just need gender)
            logging.info(f"DEBUG: User {user_id} needs to provide gender")
            return
        
        # Save to database with all required parameters
        success = db.create_profile(
            user_id=user_id,
            name=data['name'],
            age=data['age'],
            gender=data['gender'],  # Now we have gender!
            city=data['city'],
            favorite_drink=data['favorite_drink'],
            who_pays=data['who_pays'],
            photo_id=photo_id
        )
        
        if success:
            lang = await get_lang(user_id, state)
            await message.answer(
                get_message("profile_saved", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            
            logging.info(f"DEBUG: User {user_id} successfully created profile")
            
            # Clear state
            await state.clear()
        else:
            lang = await get_lang(user_id, state)
            await message.answer(get_message("error", lang), parse_mode='HTML')
        
    except Exception as e:
        logging.error(f"Error in process_profile_photo: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(ProfileStates.photo)
async def process_profile_photo_text(message: types.Message, state: FSMContext):
    """Handle text input when photo expected"""
    try:
        lang = await get_lang(message.from_user.id, state)
        await message.answer(
            get_message("profile_photo_error", lang),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in process_profile_photo_text: {e}")

@router.callback_query(F.data == "fill_again")
async def fill_again_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle fill again button - restart profile creation"""
    try:
        await callback.answer()
        user_id = callback.from_user.id
        lang = get_user_language(user_id)
        
        # Clear any existing state
        await state.clear()
        
        # Start fresh profile creation
        await callback.message.answer(
            "Давайте заполним анкету заново!\n\nВведите ваше имя:",
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        
        # Set state to name input
        await state.set_state(ProfileStates.name)
        
        logging.info(f"User {user_id} started filling profile again")
        
    except Exception as e:
        logging.error(f"Error in fill_again_callback: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer(get_message("error", lang))

@router.callback_query(F.data == "cancel_profile")
async def cancel_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle cancel profile update button"""
    try:
        await callback.answer()
        lang = get_user_language(callback.from_user.id)
        await callback.message.answer(
            get_message("welcome", lang),
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in cancel_profile_callback: {e}")
        lang = get_user_language(callback.from_user.id)
        await callback.answer(get_message("error", lang))

@router.callback_query(F.data == "skip_edit_photo_separate", SeparateEditStates.edit_photo)
async def skip_edit_photo_separate(callback: types.CallbackQuery, state: FSMContext):
    """Skip photo editing"""
    try:
        await callback.answer()
        lang = await get_lang(callback.from_user.id, state)
        await callback.message.answer(
            get_message("photo_skipped", lang),
            reply_markup=get_edit_profile_keyboard(lang),
            parse_mode='HTML'
        )
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in skip_edit_photo_separate: {e}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.answer(get_message("error", lang))

@router.callback_query(F.data == "edit_gender_cancel", SeparateEditStates.edit_gender)
async def edit_gender_cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    """Handle gender edit cancellation"""
    try:
        await callback.answer()
        lang = await get_lang(callback.from_user.id, state)
        await state.clear()
        await callback.message.answer(
            get_message("cancelled", lang),
            reply_markup=get_edit_profile_keyboard(lang),
            parse_mode='HTML'
        )
    except Exception as e:
        logging.error(f"Error in edit_gender_cancel_callback: {e}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.answer(get_message("error", lang))

@router.callback_query(F.data.startswith("edit_gender_"), SeparateEditStates.edit_gender)
async def process_edit_gender_separate(callback: types.CallbackQuery, state: FSMContext):
    """Process separate gender editing"""
    try:
        gender = callback.data.split("_")[2]
        user_id = callback.from_user.id
        success = db.update_profile(user_id, gender=gender)
        
        if success:
            logging.info(f"DEBUG: User {user_id} updated gender to '{gender}'")
            lang = await get_lang(user_id, state)
            await callback.answer()
            await callback.message.answer(
                get_message("profile_updated", lang),
                reply_markup=get_edit_profile_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            await callback.answer(get_message("error", lang))
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in process_edit_gender_separate: {e}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.answer(get_message("error", lang))

@router.callback_query(F.data.startswith("edit_who_pays_"), SeparateEditStates.edit_who_pays)
async def process_edit_who_pays_separate(callback: types.CallbackQuery, state: FSMContext):
    """Process separate who pays editing"""
    try:
        # Parse callback_data correctly: edit_who_pays_each_self -> ["edit", "who", "pays", "each_self"]
        parts = callback.data.split("_")
        who_pays = "_".join(parts[3:])  # Join all parts after index 2 to handle "each_self"
        user_id = callback.from_user.id
        logging.info(f"DEBUG: User {user_id} editing who_pays to '{who_pays}' (from callback_data: {callback.data})")
        
        success = db.update_profile(user_id, who_pays=who_pays)
        
        if success:
            logging.info(f"DEBUG: User {user_id} updated who_pays to '{who_pays}'")
            lang = await get_lang(user_id, state)
            await callback.answer()
            await callback.message.answer(
                get_message("who_pays_updated", lang),
                reply_markup=get_edit_profile_keyboard(lang),
                parse_mode='HTML'
            )
        else:
            logging.error(f"DEBUG: Failed to update who_pays for user {user_id}")
            lang = await get_lang(user_id, state)
            await callback.answer(get_message("error", lang))
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Error in process_edit_who_pays_separate: {e}")
        import traceback
        logging.error(f"DEBUG: Traceback: {traceback.format_exc()}")
        lang = await get_lang(callback.from_user.id, state)
        await callback.answer(get_message("error", lang))

# Dating functions with city separation
async def find_dating_my_city_start(message: types.Message, state: FSMContext):
    """Start dating search in user's city"""
    try:
        user_id = message.from_user.id
        logging.info(f"DEBUG: find_dating_my_city_start called for user {user_id}")
        
        user_profile = db.get_profile(user_id)
        if not user_profile:
            lang = await get_lang(user_id, state)
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        logging.info(f"DEBUG: User profile found: city_display='{user_profile.get('city_display')}', city_normalized='{user_profile.get('city_normalized')}'")
        
        # Get profiles from user's city and nearby cities with filters
        user_filters = db.get_user_filters(user_id)
        user_city = user_profile.get('city_normalized')
        profiles = db.get_profiles_for_swiping_with_filters(user_id, city_normalized=user_city,
                                                           gender_filter=user_filters.get('gender'),
                                                           who_pays_filter=user_filters.get('who_pays'))
        
        # Also check profiles without filters to determine the reason
        profiles_without_filters = db.get_profiles_for_swiping_with_filters(user_id, city_normalized=user_city,
                                                                          gender_filter='all',
                                                                          who_pays_filter='any')
        
        logging.info(f"DEBUG: Found {len(profiles)} profiles with filters, {len(profiles_without_filters)} without filters for user {user_id}")
        if profiles:
            for i, p in enumerate(profiles[:3]):
                logging.info(f"DEBUG: Profile {i+1}: user_id={p.get('user_id')}, name={p.get('name')}, city_normalized={p.get('city_normalized')}")
        
        if not profiles:
            lang = await get_lang(user_id, state)
            city_display = (user_profile.get('city_display') or user_profile.get('city') or '').title()
            
            # Check if no profiles due to filters
            if profiles_without_filters:
                # There are profiles, but none match the filters
                filter_info = []
                if user_filters.get('gender') and user_filters.get('gender') != 'all':
                    gender_names = {'male': '👨 Мужчины', 'female': '👩 Женщины'}
                    filter_info.append(f"гендер: {gender_names.get(user_filters.get('gender'), user_filters.get('gender'))}")
                
                if user_filters.get('who_pays') and user_filters.get('who_pays') != 'any':
                    pays_names = {
                        'i_treat': '🍺 Я угощаю',
                        'you_treat': '🤝 Кто-то угощает', 
                        'split': '💰 Каждый платит за себя'
                    }
                    filter_info.append(f"оплата: {pays_names.get(user_filters.get('who_pays'), user_filters.get('who_pays'))}")
                
                filter_text = ', '.join(filter_info) if filter_info else 'ваши фильтры'
                
                await message.answer(
                    f"😔 В городе <b>{city_display}</b> есть {len(profiles_without_filters)} анкет(ы), но ни одна не соответствует вашим фильтрам:\n\n"
                    f"🔽 <b>{filter_text}</b>\n\n"
                    f"Попробуйте изменить фильтры или искать в других городах!",
                    reply_markup=get_dating_keyboard(lang),
                    parse_mode='HTML'
                )
            else:
                # Really no profiles in the city
                logging.warning(f"DEBUG: No profiles found for user {user_id} in city '{city_display}'")
                await message.answer(
                    get_message("no_profiles_nearby", lang, city=city_display),
                    reply_markup=get_dating_keyboard(lang),
                    parse_mode='HTML'
                )
            return
        
        # Check if this is the last profile - show empty message instead
        if len(profiles) == 1:
            logging.info(f"DEBUG: Only 1 profile available in my city, showing empty message instead")
            lang = await get_lang(user_id, state)
            await message.answer(
                get_message("no_more_profiles", lang, text="Анкеты закончились!"),
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        # Start swiping with first profile
        await state.set_state(SwipeStates.swiping)
        await state.update_data(profiles=profiles, current_index=0)
        
        city_display = (user_profile.get('city_display') or user_profile.get('city') or '').title()
        await message.answer(
            f"🔍 Ищем знакомства в вашем городе ({city_display})",
            parse_mode='HTML'
        )
        
        # Show first profile directly instead of calling show_next_profile
        if profiles:
            profile = profiles[0]
            fresh_profile = db.get_profile(profile.get('user_id'))
            if fresh_profile and fresh_profile.get('photo_id'):
                profile['photo_id'] = fresh_profile.get('photo_id')
            lang = await get_lang(message.from_user.id, state)
            
            # Get gender text
            gender_key = {
                'male': 'gender_male',
                'female': 'gender_female', 
                'other': 'gender_other',
            }.get(profile.get('gender'), 'gender_other')
            gender_text = get_message(gender_key, lang)
            
            profile_text = (
                f"👤 <b>{profile['name']}, {profile['age']}</b>\n"
                f"⚧️ {gender_text}\n"
                f"🏙️ {profile['city'].title()}\n"
                f"🍺 {profile['favorite_drink']}"
            )
            
            # Add photo if available
            if profile.get('photo_id'):
                await message.answer_photo(
                    photo=profile['photo_id'],
                    caption=profile_text,
                    reply_markup=get_swipe_keyboard(lang),
                    parse_mode='HTML'
                )
            else:
                await message.answer(
                    get_message("no_photo", lang) + f"\n\n{profile_text}",
                    reply_markup=get_swipe_keyboard(lang),
                    parse_mode='HTML'
                )
            
            # Update current index
            await state.update_data(current_index=1)
        
    except Exception as e:
        logging.error(f"Error in find_dating_my_city_start: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        await state.clear()  # Clear state to prevent getting stuck
        lang = await get_lang(message.from_user.id, state)
        await message.answer(
            get_message("error", lang) + "\n\n" + get_message("back_to_main", lang),
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )

async def find_dating_other_city_start(message: types.Message, state: FSMContext):
    """Start city selection for dating in other cities"""
    try:
        # Clear any existing FSM state to prevent hanging
        await state.clear()
        
        user_profile = db.get_profile(message.from_user.id)
        if not user_profile:
            lang = await get_lang(message.from_user.id, state)
            await message.answer(
                get_message("need_profile_first", lang),
                reply_markup=get_main_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        lang = await get_lang(message.from_user.id, state)
        await message.answer(
            get_message("select_dating_city", lang),
            reply_markup=types.ReplyKeyboardRemove(),
            parse_mode='HTML'
        )
        await state.set_state(DatingCityStates.city_input)
        
    except Exception as e:
        logging.error(f"Error in find_dating_other_city_start: {e}")
        lang = await get_lang(message.from_user.id, state)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.message(DatingCityStates.city_input)
async def process_dating_city_input(message: types.Message, state: FSMContext):
    """Process city input for dating search"""
    try:
        if not message.text or not message.text.strip():
            lang = await get_lang(message.from_user.id, state)
            await message.answer("Город не может быть пустым. Попробуйте еще раз:")
            return
        
        city_input = message.text.strip()
        user_id = message.from_user.id
        lang = await get_lang(user_id, state)
        
        # Normalize city and search for profiles - простая нормализация без API зависаний
        city_lower = city_input.lower().strip()
        
        # Простые соответствия для избежания зависаний
        city_mappings = {
            "киев": "Kyiv", "київ": "Kyiv", "kyiv": "Kyiv",
            "москва": "Moscow", "санкт-петербург": "Saint Petersburg", "спб": "Saint Petersburg",
            "минск": "Minsk", "харьков": "Kharkiv", "одесса": "Odesa", "днепр": "Dnipro",
            "донецк": "Donetsk", "запорожье": "Zaporizhzhia", "львов": "Lviv",
            "новосибирск": "Novosibirsk", "екатеринбург": "Yekaterinburg", "ташкент": "Tashkent",
            "казань": "Kazan", "нижний новгород": "Nizhny Novgorod", "челябинск": "Chelyabinsk",
            "алматы": "Almaty", "самара": "Samara", "уфа": "Ufa", "ростов-на-дону": "Rostov-on-Don",
            "красноярск": "Krasnoyarsk", "омск": "Omsk", "воронеж": "Voronezh", "пермь": "Perm",
            "волгоград": "Volgograd", "краснодар": "Krasnodar", "саратов": "Saratov", "тюмень": "Tyumen",
            "тольятти": "Tolyatti", "барнаул": "Barnaul", "ульяновск": "Ulyanovsk", "иркутск": "Irkutsk",
            "хабаровск": "Khabarovsk", "махачкала": "Makhachkala", "владивосток": "Vladivostok",
            "ярославль": "Yaroslavl", "оренбург": "Orenburg", "томск": "Tomsk", "кемерово": "Kemerovo",
            "рязань": "Ryazan", "набережные челны": "Naberezhnye Chelny", "астана": "Astana",
            "пенза": "Penza", "киров": "Kirov", "липецк": "Lipetsk", "чебоксары": "Cheboksary",
            "балашиха": "Balashikha", "николаев": "Mykolaiv"
        }
        
        city_normalized = city_mappings.get(city_lower, city_input.title())
        
        # Если город не найден в базе, используем старую нормализацию (но с таймаутом)
        if city_normalized == city_input.title():
            try:
                city_normalized = db.normalize_city(city_input)
            except Exception as e:
                logging.warning(f"City normalization failed for '{city_input}': {e}")
                city_normalized = city_input.title()
        
        # Get profiles from specified city only (exact match) with filters
        user_filters = db.get_user_filters(user_id)
        
        # Apply filters in SQL query to maintain order stability
        if user_filters.get('gender') and user_filters.get('gender') != 'all':
            gender_filter = user_filters.get('gender')
        else:
            gender_filter = None
            
        if user_filters.get('who_pays') and user_filters.get('who_pays') != 'any':
            who_pays_filter = user_filters.get('who_pays')
        else:
            who_pays_filter = None
        
        # Single query with all data for filtering
        profiles = db.get_profiles_for_swiping_exact_city(user_id, city_normalized,
                                                             gender_filter=gender_filter,
                                                             who_pays_filter=who_pays_filter)
        
        # For filter checking, use same results without filters
        profiles_without_filters = db.get_profiles_for_swiping_exact_city(user_id, city_normalized,
                                                                                  gender_filter=None,
                                                                                  who_pays_filter=None)
        
        if not profiles:
            # Check if no profiles due to filters
            if profiles_without_filters:
                # There are profiles, but none match the filters
                filter_info = []
                if user_filters.get('gender') and user_filters.get('gender') != 'all':
                    gender_names = {'male': '👨 Мужчины', 'female': '👩 Женщины'}
                    filter_info.append(f"гендер: {gender_names.get(user_filters.get('gender'), user_filters.get('gender'))}")
                
                if user_filters.get('who_pays') and user_filters.get('who_pays') != 'any':
                    pays_names = {
                        'i_treat': '🍺 Я угощаю',
                        'you_treat': '🤝 Кто-то угощает', 
                        'split': '💰 Каждый платит за себя'
                    }
                    filter_info.append(f"оплата: {pays_names.get(user_filters.get('who_pays'), user_filters.get('who_pays'))}")
                
                filter_text = ', '.join(filter_info) if filter_info else 'ваши фильтры'
                
                await message.answer(
                    f"😔 В городе <b>{city_input.title()}</b> есть {len(profiles_without_filters)} анкет(ы), но ни одна не соответствует вашим фильтрам:\n\n"
                    f"🔽 <b>{filter_text}</b>\n\n"
                    f"Попробуйте изменить фильтры или искать в других городах!",
                    reply_markup=get_dating_keyboard(lang),
                    parse_mode='HTML'
                )
            else:
                # Really no profiles in the city
                await message.answer(
                    get_message("no_profiles_in_city", lang, city=city_input.title()),
                    reply_markup=get_dating_keyboard(lang),
                    parse_mode='HTML'
                )
            await state.clear()  # Clear state after showing no profiles
            return
        
        # Check if this is the last profile - show empty message instead
        if len(profiles) == 1:
            logging.info(f"DEBUG: Only 1 profile available, showing empty message instead")
            await message.answer(
                get_message("no_more_profiles", lang, text="Анкеты закончились!"),
                reply_markup=get_dating_keyboard(lang),
                parse_mode='HTML'
            )
            await state.clear()
            return
        
        # Start swiping with first profile
        logging.info(f"DEBUG: Starting swiping with {len(profiles)} profiles")
        await state.set_state(SwipeStates.swiping)
        await state.update_data(profiles=profiles, current_index=0, search_city=city_normalized)
        
        await message.answer(
            get_message("dating_in_city", lang, city=city_input.title()),
            parse_mode='HTML'
        )
        
        # Show first profile directly instead of calling show_next_profile
        profile = profiles[0]
        fresh_profile = db.get_profile(profile.get('user_id'))
        if fresh_profile and fresh_profile.get('photo_id'):
            profile['photo_id'] = fresh_profile.get('photo_id')
        logging.info(f"DEBUG: Showing profile ID {profile['user_id']}")
        
        # Get gender text
        gender_key = {
            'male': 'gender_male',
            'female': 'gender_female', 
            'other': 'gender_other',
        }.get(profile.get('gender'), 'gender_other')
        gender_text = get_message(gender_key, lang)
        
        profile_text = (
            f"👤 <b>{profile['name']}, {profile['age']}</b>\n"
            f"⚧️ {gender_text}\n"
            f"🏙️ {profile['city'].title()}\n"
            f"🍺 {profile['favorite_drink']}"
        )
        
        logging.info(f"DEBUG: Profile text created, photo_id: {profile.get('photo_id')}")
        
        # Add photo if available
        if profile.get('photo_id'):
            logging.info(f"DEBUG: Sending photo with ID: {profile['photo_id']}")
            await message.answer_photo(
                photo=profile['photo_id'],
                caption=profile_text,
                reply_markup=get_swipe_keyboard(lang),
                parse_mode='HTML'
            )
            logging.info(f"DEBUG: Photo sent successfully")
        else:
            logging.info(f"DEBUG: No photo, sending text only")
            await message.answer(
                get_message("no_photo", lang) + f"\n\n{profile_text}",
                reply_markup=get_swipe_keyboard(lang),
                parse_mode='HTML'
            )
            logging.info(f"DEBUG: Text profile sent successfully")
        
        # Update current index
        await state.update_data(current_index=1)
        logging.info(f"DEBUG: Profile display completed successfully")
        
    except Exception as e:
        logging.error(f"Error in process_dating_city_input: {e}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        await state.clear()  # Clear state to prevent getting stuck
        lang = await get_lang(message.from_user.id, state)
        await message.answer(
            get_message("error", lang) + "\n\n" + get_message("back_to_main", lang),
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )

# My events functions
async def show_my_events(message: types.Message):
    """Show user's created events with management options"""
    try:
        user_id = message.from_user.id
        lang = await get_lang(user_id)
        
        # Get all events (including expired ones for temporary display)
        all_events = db.get_user_events(user_id)
        
        # Filter to show only active events
        active_events = []
        for event in all_events:
            time_remaining = db.get_time_remaining(event['expires_at'])
            if time_remaining != "00:00":  # Only show active events
                active_events.append(event)
        
        if not active_events:
            await message.answer(
                get_message("no_my_events", lang),
                reply_markup=get_events_keyboard(lang),
                parse_mode='HTML'
            )
            return
        
        await message.answer(f"📅 Ваши тусовки ({len(active_events)}):", parse_mode='HTML')
        
        for event in active_events:
            # Calculate time remaining
            time_remaining = db.get_time_remaining(event['expires_at'])
            is_expired = time_remaining == "00:00"
            
            # Create delete button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=get_message("delete_event", lang), callback_data=f"delete_event_{event['id']}")]
            ])
            
            # Create event text with time remaining
            status_text = get_message("event_expired", lang) if is_expired else get_message("time_remaining", lang, time=time_remaining)
            
            event_text = (
                f"📅 <b>{event['name']}</b>\n"
                f"📍 {event['place']}\n"
                f"💰 {'Бесплатно' if event['price_type'] == 'free' else 'Платно'}\n"
                f"📝 {event['description']}\n"
                f"👤 Создатель: {event['creator_name']}\n"
                f"👥 Участников: {event['current_members']}\n"
                f"{status_text}"
            )
            
            await message.answer(
                event_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        
    except Exception as e:
        logging.error(f"Error in show_my_events: {e}")
        lang = await get_lang(message.from_user.id)
        await message.answer(get_message("error", lang), parse_mode='HTML')

@router.callback_query(F.data.startswith("delete_event_"))
async def delete_event_callback(callback: types.CallbackQuery):
    """Handle event deletion with confirmation"""
    try:
        event_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        lang = get_user_language(user_id)
        
        # Show confirmation dialog
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_delete_{event_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete")
            ]
        ])
        
        await callback.answer()
        await callback.message.answer(
            get_message("confirm_delete_event", lang),
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error in delete_event_callback: {e}")
        await callback.answer("❌ Ошибка")

@router.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_event_callback(callback: types.CallbackQuery):
    """Confirm event deletion"""
    try:
        event_id = int(callback.data.split("_")[2])
        user_id = callback.from_user.id
        lang = get_user_language(user_id)
        
        # Delete the event
        success = db.delete_event(event_id, user_id)
        
        if success:
            await callback.answer()
            await callback.message.answer(
                get_message("event_deleted", lang),
                reply_markup=get_events_keyboard(lang),
                parse_mode='HTML'
            )
            logging.info(f"DEBUG: Event {event_id} deleted by user {user_id}")
        else:
            await callback.answer("❌ Не удалось удалить тусовку")
        
    except Exception as e:
        logging.error(f"Error in confirm_delete_event_callback: {e}")
        await callback.answer("❌ Ошибка при удалении")

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete_callback(callback: types.CallbackQuery):
    """Cancel event deletion"""
    try:
        lang = get_user_language(callback.from_user.id)
        await callback.answer()
        await callback.message.answer(
            "Удаление отменено",
            reply_markup=get_events_keyboard(lang),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logging.error(f"Error in cancel_delete_callback: {e}")
        await callback.answer("❌ Ошибка")
