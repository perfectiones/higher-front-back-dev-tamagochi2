"""Модуль с интерфейсом и реализацией класса игры"""

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any

from .clicker import AbstractClicker
from .exceptions import (
    ActionCancelled,
    EmptyBag,
    InvalidChoice,
    NotEnoughMoney,
    TamagochiIsGone,
)
from .models import Food, Medicine
from .tamagochi import AbstractTamagochi


class AbstractGame(ABC):
    """Интерфейс для логики игры"""

    @abstractmethod
    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine]
    ) -> None:
        """
        Абстрактный метод инициализации класса игры

        :param tamagochi: экземпляр тамагочи
        :param clicker: экземпляр кликера
        :param all_food: все доступные варианты еды
        :param all_medicine: все доступные варианты лекарств
        """
        raise NotImplementedError

    @abstractmethod
    def work(self) -> int:
        """
        Абстрактный метод для логики действия "работа

        :return: количество заработанных монет
        """
        raise NotImplementedError

    @abstractmethod
    def buy_food(self) -> None:
        """Абстрактный метод для покупки еды"""
        raise NotImplementedError

    @abstractmethod
    def buy_medicine(self) -> None:
        """Абстрактный метод для покупки лекарства"""
        raise NotImplementedError

    @abstractmethod
    def feed_tamagochi(self) -> None:
        """Абстрактный метод для кормления тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def heal_tamagochi(self) -> None:
        """Абстрактный метод для лечения тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def rest_tamagochi(self) -> None:
        """Абстрактный метод для отдыха тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def play_with_tamagochi(self) -> None:
        """Абстрактный метод для игры с тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> dict[str, Any]:
        """
        Абстрактный метод для получения статуса (всех характеристик) тамагочи

        :return: словарь со всеми характеристиками тамагочи
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def food(self) -> list[Food]:
        """
        Абстрактное свойство для доступа к сумке с едой

        :return: список с имеющимися (купленными) объектами еды
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def medicine(self) -> list[Medicine]:
        """
        Абстрактное свойство для доступа к сумке с лекарствами

        :return: список с имеющимися (купленными) объектами лекарств
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def tamagochi(self) -> AbstractTamagochi:
        """
        Абстрактное свойство для доступа к тамагочи

        :return: экземпляр тамагочи, за которым ухаживает игрок
        """
        raise NotImplementedError


class SimpleGame(AbstractGame):
    """Игра, в которой монеты с работы тратятся на заботу о тамагочи"""

    REST_PRICE = 10  # стоимость отдыха в монетах

    def __init__(
        self,
        tamagochi: AbstractTamagochi,
        clicker: AbstractClicker,
        all_food: list[Food],
        all_medicine: list[Medicine]
    ) -> None:
        """
        Инициализирует игру с пустыми сумками и без монет

        :param tamagochi: экземпляр тамагочи
        :param clicker: экземпляр кликера
        :param all_food: все доступные для покупки варианты еды
        :param all_medicine: все доступные для покупки варианты лекарств
        """
        self._tamagochi = tamagochi
        self._clicker = clicker
        self._all_food = list(all_food)
        self._all_medicine = list(all_medicine)
        self._food: list[Food] = []
        self._medicine: list[Medicine] = []
        self._coins = 0

    def work(self) -> int:
        """
        Отправляет игрока на работу: клик кликера приносит монеты

        :return: количество заработанных монет
        :raises TamagochiIsGone: если тамагочи мёртв
        """
        self._ensure_alive()
        self._clicker.click()
        income = self._clicker.income_per_click
        self._coins += income
        return income

    def buy_food(self) -> None:
        """
        Покупает выбранную пользователем еду и кладёт её в сумку

        :raises TamagochiIsGone: если тамагочи мёртв
        :raises ActionCancelled: если пользователь отменил покупку
        :raises InvalidChoice: если выбран несуществующий пункт
        :raises NotEnoughMoney: если не хватает монет
        """
        self._ensure_alive()
        menu = self._build_menu('Какую еду купить?', self._all_food)
        index = self._parse_choice(input(menu), len(self._all_food))
        food = self._all_food[index]
        self._pay(food.price)
        self._food.append(food)

    def buy_medicine(self) -> None:
        """
        Покупает выбранное пользователем лекарство и кладёт в сумку
        его новую, ещё не использованную копию

        :raises TamagochiIsGone: если тамагочи мёртв
        :raises ActionCancelled: если пользователь отменил покупку
        :raises InvalidChoice: если выбран несуществующий пункт
        :raises NotEnoughMoney: если не хватает монет
        """
        self._ensure_alive()
        menu = self._build_menu('Какое лекарство купить?', self._all_medicine)
        index = self._parse_choice(input(menu), len(self._all_medicine))
        medicine = self._all_medicine[index]
        self._pay(medicine.price)
        self._medicine.append(replace(medicine, uses=0))

    def feed_tamagochi(self) -> None:
        """
        Кормит тамагочи выбранной едой из сумки, съеденная еда
        убирается из сумки

        :raises TamagochiIsGone: если тамагочи мёртв
        :raises EmptyBag: если в сумке нет еды
        :raises ActionCancelled: если пользователь отменил кормление
        :raises InvalidChoice: если выбран несуществующий пункт
        """
        self._ensure_alive()
        if not self._food:
            raise EmptyBag('Сумка с едой пуста — сначала купите еду')
        menu = self._build_menu('Чем покормить питомца?', self._food)
        index = self._parse_choice(input(menu), len(self._food))
        self._tamagochi.feed(self._food[index])
        del self._food[index]
        self._tamagochi.update()

    def heal_tamagochi(self) -> None:
        """
        Лечит тамагочи выбранным лекарством из сумки, закончившееся
        лекарство выбрасывается

        :raises TamagochiIsGone: если тамагочи мёртв
        :raises EmptyBag: если в сумке нет лекарств
        :raises ActionCancelled: если пользователь отменил лечение
        :raises InvalidChoice: если выбран несуществующий пункт
        :raises MedicineIsOver: если у лекарства не осталось применений
        """
        self._ensure_alive()
        if not self._medicine:
            raise EmptyBag(
                'Сумка с лекарствами пуста — сначала купите лекарство'
            )
        menu = self._build_menu('Каким лекарством лечить?', self._medicine)
        index = self._parse_choice(input(menu), len(self._medicine))
        medicine = self._medicine[index]
        self._tamagochi.heal(medicine)
        medicine.uses += 1
        if medicine.is_empty():
            del self._medicine[index]
        self._tamagochi.update()

    def rest_tamagochi(self) -> None:
        """
        Платно укладывает тамагочи отдыхать

        :raises TamagochiIsGone: если тамагочи мёртв
        :raises NotEnoughMoney: если не хватает монет на отдых
        """
        self._ensure_alive()
        self._pay(self.REST_PRICE)
        self._tamagochi.rest()
        self._tamagochi.update()

    def play_with_tamagochi(self) -> None:
        """
        Играет с тамагочи

        :raises TamagochiIsGone: если тамагочи мёртв
        :raises NotEnoughEnergy: если у тамагочи не хватает энергии
        """
        self._ensure_alive()
        self._tamagochi.play()
        self._tamagochi.update()

    def get_status(self) -> dict[str, int]:
        """
        Возвращает все характеристики тамагочи и количество монет

        :return: словарь с голодом, усталостью, энергией, здоровьем
            и монетами
        """
        return {**self._tamagochi.status, 'coins': self._coins}

    @property
    def food(self) -> list[Food]:
        """
        Свойство для доступа к сумке с едой

        :return: копия списка с купленной едой
        """
        return list(self._food)

    @property
    def medicine(self) -> list[Medicine]:
        """
        Свойство для доступа к сумке с лекарствами

        :return: копия списка с купленными лекарствами
        """
        return list(self._medicine)

    @property
    def tamagochi(self) -> AbstractTamagochi:
        """
        Свойство для доступа к тамагочи

        :return: экземпляр тамагочи, за которым ухаживает игрок
        """
        return self._tamagochi

    def _ensure_alive(self) -> None:
        """
        Проверяет, что тамагочи жив, перед любым действием игры

        :raises TamagochiIsGone: если тамагочи мёртв
        """
        if not self._tamagochi.is_alive():
            raise TamagochiIsGone('Питомца больше нет — игра окончена')

    def _pay(self, price: int) -> None:
        """
        Списывает монеты за покупку или отдых

        :param price: стоимость в монетах
        :raises NotEnoughMoney: если монет меньше, чем нужно
        """
        if self._coins < price:
            raise NotEnoughMoney(
                f'Не хватает монет: нужно {price}, а у вас {self._coins}'
            )
        self._coins -= price

    @staticmethod
    def _build_menu(title: str, options: list[Food] | list[Medicine]) -> str:
        """
        Собирает текст меню с пронумерованными пунктами и отменой

        :param title: заголовок меню
        :param options: варианты для выбора
        :return: текст меню, который показывается при вводе
        """
        lines = [title]
        lines.extend(
            f'{number}. {option}'
            for number, option in enumerate(options, start=1)
        )
        lines.append('0. Отмена')
        lines.append('Ваш выбор: ')
        return '\n'.join(lines)

    @staticmethod
    def _parse_choice(answer: str, options_count: int) -> int:
        """
        Превращает ответ пользователя в индекс выбранного пункта меню

        :param answer: строка, введённая пользователем
        :param options_count: количество пунктов в меню
        :return: индекс выбранного пункта в списке, начиная с нуля
        :raises ActionCancelled: если пользователь ввёл 0
        :raises InvalidChoice: если введён не номер пункта меню
        """
        choice = answer.strip()
        if choice == '0':
            raise ActionCancelled('Действие отменено')
        if not choice.isdecimal() or not 1 <= int(choice) <= options_count:
            raise InvalidChoice(
                f'Неверный выбор «{choice}»: введите номер пункта '
                f'от 1 до {options_count} или 0 для отмены'
            )
        return int(choice) - 1
