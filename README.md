# GyverLamp для Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

Компонент интеграции [Home Assistant][1] с [Огненной Wi-Fi Лампой][2] замечательного российского изобретателя [Александра Майорова][3]. Обязательно **не забывам поддержать** автора этого изобретения.

[1]: https://www.home-assistant.io/
[2]: https://alexgyver.ru/gyverlamp/
[3]: https://alexgyver.ru/about_gyver/

Компонент работает со стандартной прошивкой лампы. Текущее состояние лампы **опрашивается раз в 30 секунд**, поэтому, после старта Home Assistant, она будет пол минуты выключена.

Поддерживается:

- включение/выключение лампы
- установка яркости
- установка эффекта из списка
- установка скорости и масштаба через тон и насыщенность (круг с набором цветов в интерфейсе HA)
   - **насыщенность** это **скорость**, ближе к центру - быстрее 
   - **цвет** это **масштаб**, но в некоторых эффектах цвет это цвет :) 

![](screen.png)

## Установка

**Способ 1.** [HACS](https://hacs.xyz/)

> HACS > Интеграции > 3 точки (правый верхний угол) > Пользовательские репозитории > URL: `AlexxIT/GyverLamp`, Категория: Интеграция > Добавить > подождать > GyverLamp > Установить

**Способ 2.** Вручную скопируйте папку `gyverlamp` из [latest release](https://github.com/AlexxIT/GyverLamp/releases/latest) в директорию `/config/custom_components`.

## Настройка

[![Home Assistant компонент для Лампы Гайвера на стандартной прошивке](https://img.youtube.com/vi/riYsv5k_EdY/mqdefault.jpg)](https://www.youtube.com/watch?v=riYsv5k_EdY)

**Способ 1.** GUI

> Настройки > Интеграции > Добавить интеграцию > **GyverLamp**

Если интеграции нет в списке - очистите кэш браузера.

**Способ 2.** YAML

```yaml
light gyverlamp:
- platform: gyverlamp
  host: 192.168.1.123
  name: Лампа Гайвера
  effects:
  - Конфетти
  - Огонь
  - ...
```
