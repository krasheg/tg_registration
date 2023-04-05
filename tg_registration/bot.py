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
from profiles.models import Profile
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
    new_user = await sync_to_async(create_user)(username, email, password)

    user = message.from_user

    # Отримуємо профіль користувача
    profile_photos = await bot.get_user_profile_photos(user_id=user.id, limit=1)

    # Отримуємо фотографію профілю користувача
    photo_id = profile_photos.photos[0][-1].file_id

    # Зберігаємо фотографію в media root

    file = await bot.get_file(photo_id)
    file_path = file.file_path
    downloaded_file = await bot.download_file(file_path)
    file_name = f"{user.id}.jpg"
    with open(os.path.join(settings.MEDIA_ROOT, file_name), 'wb') as new_file:
        new_file.write(downloaded_file.getvalue())

    # Зберігаємо дані користувача в базу даних
    await sync_to_async(create_profile)(user, new_user, file_name)

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


@transaction.atomic
def create_profile(user, new_user, file_name):
    result = Profile.objects.update_or_create(user=new_user,
                                              defaults={
                                                  'username': user.username,
                                                  'first_name': user.first_name,
                                                  'last_name': user.last_name,
                                                  'photo': f'{file_name}',
                                                  'user_tg_id': user.id,
                                              })
    return result


if __name__ == '__main__':
    # Run bot
    executor.start_polling(dp, skip_updates=True)
