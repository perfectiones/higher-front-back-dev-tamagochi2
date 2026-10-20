"""Модуль с интерфейсом и реализацией кликера"""

import random
from abc import ABC, abstractmethod


class AbstractClicker(ABC):
    """Интерфейс для кликера"""

    @abstractmethod
    def __init__(self) -> None:
        """Абстрактный метод инициализации"""
        raise NotImplementedError

    @abstractmethod
    def click(self) -> None:
        """Абстрактный метод клика для накапливания монет"""
        raise NotImplementedError

    @property
    @abstractmethod
    def income_per_click(self) -> int:
        """Абстрактное свойство для доступа к количеству монет за клик"""
        raise NotImplementedError


class SimpleRandomClicker(AbstractClicker):
    """Кликер, который за каждый клик приносит случайный доход"""

    def __init__(self, min_income: int, max_income: int) -> None:
        """
        Инициализирует кликер с диапазоном дохода за один клик

        :param min_income: минимальный доход за клик
        :param max_income: максимальный доход за клик
        :raises ValueError: если доход отрицательный или минимум больше
            максимума
        """
        if min_income < 0 or min_income > max_income:
            raise ValueError(
                'Доход за клик должен быть неотрицательным, '
                'а минимум — не больше максимума'
            )
        self._min_income = min_income
        self._max_income = max_income
        self._income_per_click = 0

    def click(self) -> None:
        """Выполняет клик и выбирает случайный доход из диапазона"""
        self._income_per_click = random.randint(
            self._min_income, self._max_income
        )

    @property
    def income_per_click(self) -> int:
        """
        Свойство для доступа к доходу последнего клика

        :return: количество монет за последний клик (0 до первого клика)
        """
        return self._income_per_click
