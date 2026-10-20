"""Модуль с исключениями"""


class GameError(Exception):
    """Базовая ошибка игры, от неё наследуются все остальные"""


class TamagochiIsGone(GameError):
    """Ошибка при смерти тамагочи"""


class NotEnoughMoney(GameError):
    """Ошибка когда не хватает монет для покупки"""


class NotEnoughEnergy(GameError):
    """Ошибка когда у тамагочи не хватает энергии для действия"""


class MedicineIsOver(GameError):
    """Ошибка когда у лекарства не осталось применений"""


class EmptyBag(GameError):
    """Ошибка когда в сумке нет нужных предметов"""


class InvalidChoice(GameError):
    """Ошибка когда пользователь выбрал несуществующий пункт меню"""


class ActionCancelled(GameError):
    """Ошибка когда пользователь отменил действие"""
