# Plan projektu — odległość do pojazdów w trudnych warunkach pogodowych

Zespół — Łukasz Kubik i Paweł Mroczek. Szczegółowe założenia są w [opisie projektu](Opis%20projektu.md).

## Harmonogram

| Termin | Planowane prace |
| --- | --- |
| Do 4 listopada 2026 | Przegląd literatury. Uruchomienie metod YOLO + geometria oraz LiDAR na KITTI. Prezentacja założeń. |
| Do 9 grudnia 2026 | Uruchomienie gotowych sieci głębi na KITTI. Porównanie wyników w Seeing Through Fog według pogody i odległości. Podział SHIFT na sceny do uczenia i walidacji. |
| Do 5 stycznia 2027 | Dostrojenie wariantu B na dobrej pogodzie oraz C na mgle i deszczu. Test wariantów A, B i C na Seeing Through Fog i KITTI. |
| 13 stycznia 2027 | Prezentacja końcowa. Tabele wyników według pogody i odległości, film z odległościami nad pojazdami oraz README repozytorium. |

Na slajdzie 10 prezentacji, termin 9 grudnia opisano jako „Prezentacja 2”. [Ustalenia z 3 listopada](Źródła/prompt_prezentacja_311.md) podają na ten dzień sprawozdanie do 23:59 oraz próbne dostrojenie na małej próbce SHIFT. Nazwę oddania warto potwierdzić z prowadzącą.

## Zakres eksperymentu

- Porównujemy geometrię kamery, sieci głębi i metodę z LiDAR-em. Do oceny odległości używamy oznaczonych ramek 3D.
- Wkład projektowy to dostrojenie Depth Anything V2 Metric. Wariant A to model wyjściowy. B i C zaczynają od tego samego modelu i korzystają z porównywalnych ustawień, liczby klatek i kroków uczenia.
- SHIFT służy do uczenia i walidacji. Seeing Through Fog to główny test na rzeczywistych zdjęciach. KITTI służy do uruchomienia metod i oceny działania w dobrej pogodzie na wydzielonych danych.
- Fuzja geometrii i sieci oraz sztuczna mgła na obrazach KITTI to opcjonalne rozszerzenia.
