"""Модуль с интерфейсом и реализациями класса тамагочи"""

import random
from abc import ABC, abstractmethod

from .exceptions import MedicineIsOver, NotEnoughEnergy, TamagochiIsGone
from .models import Food, Medicine


class AbstractTamagochi(ABC):
    """Интерфейс логики тамагочи"""

    @abstractmethod
    def feed(self, food: Food) -> None:
        """
        Абстрактный метод для кормления тамагочи

        :param food: объект еды для кормления
        """
        raise NotImplementedError

    @abstractmethod
    def play(self) -> None:
        """Абстрактный метод для игры с тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def rest(self) -> None:
        """Абстрактный метод для отдыха тамагочи"""
        raise NotImplementedError

    @abstractmethod
    def heal(self, medicine: Medicine) -> None:
        """
        Абстрактный метод для лечения тамагочи

        :param medicine: лекарство для лечения
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def status(self) -> dict[str, int]:
        """
        Абстрактное свойство для доступа ко всем состояниям тамагочи

        :return: словарь со всеми состояниями тамагочи
        """
        raise NotImplementedError

    @abstractmethod
    def is_alive(self) -> bool:
        """
        Абстрактный метод для проверки жив ли тамагочи

        :return: True если жив, иначе False
        """
        raise NotImplementedError

    @abstractmethod
    def is_sick(self) -> bool:
        """
        Абстрактный метод для проверки, не заболел ли тамагочи

        :return: True если тамагочи болеет, иначе False
        """
        raise NotImplementedError

    @abstractmethod
    def update(self) -> None:
        """
        Абстрактный метод для обновления состояний тамагочи.
        Должен использоваться после каждого взаимодействия с тамагочи
        """
        raise NotImplementedError


class SimpleTamagochi(AbstractTamagochi):
    """Тамагочи в образе котёнка Барсика"""

    MIN_STAT = 0  # нижняя граница любого показателя
    MAX_STAT = 100  # верхняя граница любого показателя
    START_HUNGER = 20  # голод при рождении
    NEGLECT_LEVEL = 80  # с этого уровня голод и усталость запущены
    HUNGER_PER_TICK = 3  # рост голода за тик
    FATIGUE_PER_TICK = 3  # рост усталости за тик
    ENERGY_PER_TICK = 3  # расход энергии за тик
    SICKNESS_FATIGUE = 2  # дополнительная усталость за тик болезни
    NEGLECT_DAMAGE = 5  # урон за каждый запущенный показатель
    SICKNESS_DAMAGE = 5  # урон за тик болезни
    REGENERATION = 2  # восстановление здоровья ухоженного питомца
    BASE_SICKNESS_CHANCE = 0.05  # шанс заболеть за тик
    RISK_SICKNESS_CHANCE = 0.1  # прибавка к шансу за фактор риска
    PLAY_ENERGY_COST = 15  # расход энергии на игру
    PLAY_HUNGER = 10  # рост голода от игры
    PLAY_FATIGUE = 10  # рост усталости от игры
    PLAY_HEALTH_BONUS = 5  # здоровье, которое игра даёт здоровому питомцу
    REST_RECOVERY = 30  # сколько энергии даёт и усталости снимает отдых
    SICK_REST_DIVIDER = 2  # во сколько раз болезнь ослабляет отдых

    def __init__(self, name: str = 'Барсик') -> None:
        """
        Создаёт сытого, бодрого и здорового тамагочи

        :param name: имя тамагочи
        """
        self._name = name
        self._hunger = self.START_HUNGER
        self._fatigue = self.MIN_STAT
        self._energy = self.MAX_STAT
        self._hp = self.MAX_STAT
        self._sick = False

    @property
    def name(self) -> str:
        """
        Свойство для доступа к имени тамагочи

        :return: имя тамагочи
        """
        return self._name

    def feed(self, food: Food) -> None:
        """
        Кормит тамагочи: голод уменьшается на сытность еды.
        Если еда сытнее, чем тамагочи голоден, он объедается
        и теряет энергию на величину излишка

        :param food: объект еды для кормления
        :raises TamagochiIsGone: если тамагочи мёртв
        """
        self._ensure_alive()
        overeating = max(self.MIN_STAT, food.satiety - self._hunger)
        self._hunger = self._clamp(self._hunger - food.satiety)
        self._energy = self._clamp(self._energy - overeating)

    def play(self) -> None:
        """
        Играет с тамагочи: тратит энергию, повышает голод и усталость,
        а здоровому тамагочи добавляет здоровья

        :raises TamagochiIsGone: если тамагочи мёртв
        :raises NotEnoughEnergy: если энергии не хватает для игры
        """
        self._ensure_alive()
        if self._energy < self.PLAY_ENERGY_COST:
            raise NotEnoughEnergy(
                f'{self._name} слишком устал для игры: нужно '
                f'{self.PLAY_ENERGY_COST} энергии, а осталось {self._energy}'
            )
        self._energy -= self.PLAY_ENERGY_COST
        self._hunger = self._clamp(self._hunger + self.PLAY_HUNGER)
        self._fatigue = self._clamp(self._fatigue + self.PLAY_FATIGUE)
        if not self._sick:
            self._hp = self._clamp(self._hp + self.PLAY_HEALTH_BONUS)

    def rest(self) -> None:
        """
        Укладывает тамагочи отдыхать: энергия растёт, усталость падает.
        Больному тамагочи отдых помогает вдвое слабее

        :raises TamagochiIsGone: если тамагочи мёртв
        """
        self._ensure_alive()
        recovery = self.REST_RECOVERY
        if self._sick:
            recovery //= self.SICK_REST_DIVIDER
        self._energy = self._clamp(self._energy + recovery)
        self._fatigue = self._clamp(self._fatigue - recovery)

    def heal(self, medicine: Medicine) -> None:
        """
        Лечит тамагочи: восстанавливает здоровье и излечивает болезнь.
        Применения лекарства учитывает игра

        :param medicine: лекарство для лечения
        :raises TamagochiIsGone: если тамагочи мёртв
        :raises MedicineIsOver: если у лекарства не осталось применений
        """
        self._ensure_alive()
        if medicine.is_empty():
            raise MedicineIsOver(f'Лекарство «{medicine.name}» закончилось')
        self._hp = self._clamp(self._hp + medicine.heal_hp)
        self._sick = False

    @property
    def status(self) -> dict[str, int]:
        """
        Свойство для доступа ко всем состояниям тамагочи

        :return: словарь с голодом, усталостью, энергией и здоровьем
        """
        return {
            'hunger': self._hunger,
            'fatigue': self._fatigue,
            'energy': self._energy,
            'hp': self._hp,
        }

    def is_alive(self) -> bool:
        """
        Проверяет, жив ли тамагочи

        :return: True если здоровье больше нуля, иначе False
        """
        return self._hp > self.MIN_STAT

    def is_sick(self) -> bool:
        """
        Проверяет, болеет ли тамагочи

        :return: True если тамагочи болеет, иначе False
        """
        return self._sick

    def update(self) -> None:
        """
        Обновляет состояния тамагочи за один тик времени.
        Голод и усталость растут, энергия падает. Ухоженный тамагочи
        понемногу восстанавливает здоровье, а запущенный теряет его
        и чаще болеет

        :raises TamagochiIsGone: если тамагочи мёртв
        """
        self._ensure_alive()
        self._pass_time()
        risk_factors = self._count_risk_factors()
        self._try_to_get_sick(risk_factors)
        self._change_health(risk_factors)

    def _pass_time(self) -> None:
        """Повышает голод и усталость и тратит энергию за один тик"""
        fatigue_gain = self.FATIGUE_PER_TICK
        if self._sick:
            fatigue_gain += self.SICKNESS_FATIGUE
        self._hunger = self._clamp(self._hunger + self.HUNGER_PER_TICK)
        self._fatigue = self._clamp(self._fatigue + fatigue_gain)
        self._energy = self._clamp(self._energy - self.ENERGY_PER_TICK)

    def _count_risk_factors(self) -> int:
        """
        Считает запущенные показатели: сильный голод, сильную усталость
        и полное отсутствие энергии

        :return: количество запущенных показателей
        """
        return sum((
            self._hunger >= self.NEGLECT_LEVEL,
            self._fatigue >= self.NEGLECT_LEVEL,
            self._energy == self.MIN_STAT,
        ))

    def _try_to_get_sick(self, risk_factors: int) -> None:
        """
        Случайно решает, заболеет ли тамагочи.
        Шанс растёт с каждым запущенным показателем

        :param risk_factors: количество запущенных показателей
        """
        chance = (
            self.BASE_SICKNESS_CHANCE
            + self.RISK_SICKNESS_CHANCE * risk_factors
        )
        if random.random() < chance:
            self._sick = True

    def _change_health(self, risk_factors: int) -> None:
        """
        Отнимает здоровье за запущенные показатели и болезнь,
        а ухоженному тамагочи понемногу восстанавливает его

        :param risk_factors: количество запущенных показателей
        """
        damage = self.NEGLECT_DAMAGE * risk_factors
        if self._sick:
            damage += self.SICKNESS_DAMAGE
        if damage:
            self._hp = self._clamp(self._hp - damage)
        else:
            self._hp = self._clamp(self._hp + self.REGENERATION)

    def _ensure_alive(self) -> None:
        """
        Проверяет, что тамагочи жив, перед любым действием с ним

        :raises TamagochiIsGone: если тамагочи мёртв
        """
        if not self.is_alive():
            raise TamagochiIsGone(f'{self._name} больше не с нами')

    @classmethod
    def _clamp(cls, value: int) -> int:
        """
        Ограничивает значение показателя допустимым диапазоном

        :param value: новое значение показателя
        :return: значение в пределах от MIN_STAT до MAX_STAT
        """
        return max(cls.MIN_STAT, min(cls.MAX_STAT, value))
