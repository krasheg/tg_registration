from django.conf import settings
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tg_registration.settings")
if not settings.configured:
    django.setup()


from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import CommandStart
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Command
from django.contrib.auth.models import User
from django.db import transaction
from asgiref.sync import sync_to_async

class RegisterState(StatesGroup):
    waiting_for_username = State()
    waiting_for_email = State()
    waiting_for_password = State()
    waiting_for_profile = State()
    waiting_for_confirmation = State()


bot = Bot(token=settings.TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


@dp.message_handler(CommandStart())
async def start(message: types.Message):
    await message.reply("Hello! type /register for registration on site.")


@dp.message_handler(Command('register'))
async def register(message: types.Message):
    await bot.send_message(chat_id=message.chat.id, text="Enter username:")
    await RegisterState.waiting_for_username.set()


@dp.message_handler(state=RegisterState.waiting_for_username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text
    await state.update_data(username=username)

    await bot.send_message(chat_id=message.chat.id, text="Enter email:")
    await RegisterState.waiting_for_email.set()


@dp.message_handler(state=RegisterState.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)

    await bot.send_message(chat_id=message.chat.id, text="Enter password:")
    await RegisterState.waiting_for_password.set()





@dp.message_handler(state=RegisterState.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    await state.update_data(password=password)

    data = await state.get_data()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # saving data
    await sync_to_async(create_user)(username, email, password)

    user = message.from_user

    # name from tg
    first_name = user.first_name
    last_name = user.last_name
    name = f"{first_name} {last_name}" if last_name else first_name
    print(name)

    # User`s data
    username = user.username
    print(username)

    user_id = user.id
    is_bot = user.is_bot
    language_code = user.language_code

    # receive profile
    profile_photos = await bot.get_user_profile_photos(user_id=user_id, limit=1)

    # receive photo
    photo_id = profile_photos.photos[0][-1].file_id
    print(photo_id)


    await bot.send_message(chat_id=message.chat.id, text="Congratulations! You`ve successfully registered!")

    # starting state
    await state.finish()


# Creating user`s function
@transaction.atomic
def create_user(username, email, password):
    user = User(username=username, email=email)
    user.set_password(password)
    user.save()
    return user


if __name__ == '__main__':
    # Run bot
    executor.start_polling(dp, skip_updates=True)
