# utils/states.py
from aiogram.fsm.state import State, StatesGroup

class StarsStates(StatesGroup):
    choose_recipient = State()
    choose_quantity = State()
    choose_payment = State()

class PremiumStates(StatesGroup):
    choose_recipient = State()
    choose_duration = State()
    choose_payment = State()

class GiftsStates(StatesGroup):
    choose_recipient = State()
    choose_anonymity = State()
    choose_gift = State()
    choose_comment = State()
    choose_payment = State()