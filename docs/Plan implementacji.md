# Plan implementacji

Zespół: Łukasz Kubik i Paweł Mroczek. Założenia projektu są w [opisie projektu](Opis%20projektu.md).
Ten plan mówi, co dokładnie liczymy, w jakiej kolejności i na jakich danych. Stan na 12 listopada 2026.

Mierzymy odległość do pojazdów przed autem trzema metodami i sprawdzamy, jak pogarszają ją mgła, śnieg i deszcz:

1. **M1: YOLO + geometria** (kamera).
2. **M2: sieć głębi** (kamera), w wariantach A, B i C.
3. **M3: dane z LiDAR-u** (punkty chmury w ramce auta).

Główny wkład projektowy to dostrojenie Depth Anything V2 Metric na symulowanej mgle i deszczu z SHIFT oraz
sprawdzenie, czy zmniejsza to błąd odległości do aut na prawdziwych danych (Seeing Through Fog, dalej STF).
Poprawa jest hipotezą do sprawdzenia. Wynik negatywny też jest wynikiem.

## Stan prac

| Termin | Prace | Stan |
| --- | --- | --- |
| Prezentacja 1 (slajdy z 4 listopada 2026) | Przegląd literatury, prezentacja założeń, pierwsze uruchomienie metod. | Zrobione. Metody działają na pojedynczych klatkach. Ocena na całym KITTI przechodzi do następnego etapu. |
| Do 9 grudnia 2026 | Ocena M1, M2 i M3 na KITTI z miarami błędu. Dwie sieci głębi na KITTI. Tabele STF: dobra kontra zła pogoda. Podział SHIFT na uczenie i walidację, próbne dostrojenie na małej próbce. | W toku: ocena na KITTI. |
| Do 5 stycznia 2027 | Pełne dostrojenie wariantów B i C. Test A, B i C na STF i KITTI. | Nie zaczęte. |
| 13 stycznia 2027 | Prezentacja końcowa: tabele według pogody i odległości, film z odległościami nad autami, README. | Nie zaczęte. |

Na slajdzie 10 prezentacji 1 termin 9 grudnia nazwano „Prezentacja 2”, a ustalenia z 3 listopada mówią o sprawozdaniu
do 23:59. Nazwę oddania warto potwierdzić z prowadzącą.

**Co już jest w repo:**

- `scripts/fetch_samples.py` pobiera po jednej klatce: KITTI (dobra pogoda), STF (dobra pogoda i śnieg), SHIFT (dobra
  pogoda i gęsta mgła).
- `scripts/three_methods.py` uruchamia na nich YOLO, M1 w obu odmianach, M2 (gotowy model, czyli wariant A) i M3.
- Wyniki są w `results/one_frame/` i w głównym README.

## Najbliższe kroki

1. **Ocena na KITTI.** Podział 7481 oznaczonych klatek na część treningową i walidacyjną (popularny podział
   3712/3769), dopasowanie wykryć do etykiet, miary błędu i pierwsza tabela w podziale na odległości.
2. **Dopracowanie metod na części treningowej KITTI:** wysokości klas dla M1, obszar ramki dla M2, wybór punktów
   dla M3 (szczegóły w rozdziale „Metody”).
3. **Druga sieć głębi:** UniDepth V2 jako model odniesienia.
4. **STF**, gdy przyjdzie akceptacja rejestracji: loader, tabele dobra kontra zła pogoda dla M1, M2 i M3.
5. **SHIFT:** wybór sekwencji dla B i C, wydzielenie walidacji, próbne dostrojenie na małej próbce (czy trening działa).
6. **Pełne warianty B i C** oraz ocena A, B i C na STF, KITTI i walidacji SHIFT.
7. **Końcowe tabele i wykresy, film demo, README.**

## Role zbiorów

- **SHIFT:** dostrajanie (B i C) z wydzieloną walidacją do wyboru ustawień.
- **STF:** główny test w prawdziwej złej pogodzie, w porównaniu z częścią STF nagraną w dobrej pogodzie.
- **KITTI:** uruchomienie i dopracowanie metod oraz sprawdzian, czy dostrojenie nie pogorszyło dobrej pogody.
- Zbiorów testowych (STF, część walidacyjna KITTI) nie używamy do wyboru ustawień treningu ani parametrów metod.
  Do tego służą walidacja SHIFT i część treningowa KITTI.
- Punkty odniesienia: M1, gotowe sieci głębi, M3.

## Definicje

- **Prawdziwa odległość (GT):** najmniejsza współrzędna z (oś kamery do przodu) z 8 narożników ramki 3D, czyli odległość
  do najbliższej ściany auta. Wszystkie metody mierzą powierzchnię auta, nie jego środek.
- **Dopasowanie:** wykrycia YOLO łączymy z etykietami po IoU ramek 2D ≥ 0,5 (algorytm węgierski). Etykiety bez
  dopasowania to auta pominięte: z nich liczymy skuteczność wykrywania. Fałszywe wykrycia raportujemy osobno i nie
  wchodzą do błędu odległości. Skrypt na pojedynczych klatkach bierze na razie po prostu etykietę o najlepszym IoU.
- **Podzbiory:** wszystkie obiekty oraz podzbiór „moderate” jak w KITTI (wysokość ramki ≥ 25 px, co najwyżej częściowe
  zasłonięcie, obcięcie ≤ 30%).
- **Przedziały odległości:** 0–20 m, 20–40 m, ponad 40 m.
- **Warunki:** dobra pogoda, lekka mgła, gęsta mgła, śnieg lub deszcz.

## Metody

Wszystkie trzy metody dostają te same ramki z YOLO (klasy COCO: car, truck, bus), bo porównujemy szacowanie
odległości, a nie detektory.

**M1: YOLO + geometria.** Dwie odmiany, raportujemy obie:

- płaszczyzna drogi: d = f · H / (y_dół − y_horyzont), gdzie H to wysokość kamery, a horyzont wynika z kalibracji
  (dla poziomej kamery to c_y);
- wysokość auta: d = f · h_klasy / h_ramki, gdzie h_klasy to średnia wysokość klasy z etykiet treningowych.

Stan w kodzie: obie odmiany działają. Wysokości klas są na razie wpisane na stałe (auto 1,52 m, ciężarówka 2,6 m,
autobus 3,2 m). Do zrobienia: policzyć je z części treningowej KITTI.

**M2: sieć głębi.** Model liczy mapę głębi całego obrazu, a odległość auta to mediana głębi w środkowej części ramki
(bez drogi i tła). Depth Anything V2 Metric oceniamy w każdym wariancie dostrojenia (A, B, C).

Stan w kodzie: Depth Anything V2 Metric Outdoor w wersji Small, środkowe 40% ramki. Do zrobienia: dobrać wielkość
obszaru na części treningowej KITTI, uruchomić UniDepth V2 (przyjmuje parametry kamery) i sprawdzić, która wielkość
modelu zmieści się w pamięci przy dostrajaniu.

**M3: dane z LiDAR-u.** Punkty rzutujemy do obrazu (KITTI: x = P2 · R0_rect · Tr_velo_to_cam · X) i bierzemy te
przed kamerą, które wpadają do zmniejszonej ramki. Raportujemy odsetek aut z mniej niż 5 punktami: we mgle to też jest
wynik. Ramki 3D oznaczano z pomocą LiDAR-u, więc w dobrej pogodzie M3 wypada prawie idealnie z samej konstrukcji
pomiaru. Trzeba to zaznaczać przy wynikach.

Stan w kodzie: mediana głębi punktów ze środkowych 40% ramki. Do zrobienia: porównać ją na części treningowej KITTI
z wersją, która usuwa punkty drogi i wybiera przednią powierzchnię auta, i zostawić prostszą, jeśli różnica jest mała.

## Dostrojenie (główny wkład projektowy)

- **Punkt wyjścia:** oficjalny model Depth Anything V2 Metric Outdoor (uczony na Virtual KITTI 2, zasięg do 80 m,
  nie przyjmuje parametrów kamery).
- **Kod:** folder `metric_depth` z repozytorium Depth Anything V2, strata SiLog z maską ważnych pikseli.
- **Dane:** SHIFT, widok z przodu, zbiór `discrete`.
- **Trzy warianty:**
    - A: gotowy model, bez dostrajania;
    - B (kontrola): dostrojony na SHIFT w dobrej pogodzie;
    - C: dostrojony na SHIFT z mgłą i deszczem.
- **Warunki porównania B i C:** ten sam model startowy, te same ustawienia (krok uczenia, wielkość paczki, augmentacje,
  rozdzielczość), ta sama liczba klatek i kroków, porównywalna pora dnia (propozycja: tylko dzień). Ustawienia
  dobieramy raz i używamy w obu wariantach.
- **Interpretacja:** B oddziela korzyść z danych ze złą pogodą od korzyści z samego dodatkowego treningu. B i C to różne
  sceny, więc w wynikach nie piszemy, że jedyną różnicą jest pogoda.
- **Ocena każdego wariantu:** STF w dobrej kontra złej pogodzie (główny wynik), KITTI (czy dostrojenie nie pogorszyło
  dobrej pogody), walidacja SHIFT.
- **Skala:** model nie zna parametrów kamery, a kamery SHIFT, KITTI i STF się różnią. Podajemy wyniki surowe
  i po wyrównaniu skali medianą na obraz, żeby oddzielić błąd skali od wpływu pogody. Na pojedynczych klatkach SHIFT
  gotowy model zawyża odległości około dwukrotnie.
- Zapisujemy konfigurację i krzywe uczenia (Weights & Biases). Zapisane modele trzymamy poza gitem.

## Miary i wyniki

- AbsRel, średni błąd ze znakiem (czy mgła zawyża, czy zaniża odległość), RMSE, δ < 1,25, odsetek aut z błędem
  względnym poniżej 10%, skuteczność wykrywania, liczba klatek na sekundę każdej metody.
- Wszystko w podziale: metoda (i wariant dostrojenia) × warunki × przedział odległości. Przy każdej liczbie podajemy,
  ile aut się na nią składa.
- Wpływ pogody i dostrojenia liczymy w obrębie jednego zbioru (STF w dobrej kontra złej pogodzie, KITTI dla A, B, C),
  bo skala sieci głębi zależy od kamery.
- Jeden plik CSV z wierszem na każde dopasowane auto i wynikami wszystkich metod. Wszystkie tabele i wykresy powstają
  z niego. Główny wykres to błąd na STF w dobrej i złej pogodzie dla wariantów A, B i C, z M1 i M3 jako punktami
  odniesienia.

## Dane

### KITTI 3D Object: dobra pogoda

- **Skąd:** [cvlibs.net](https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d), rejestracja, dostęp
  od ręki. Do pobrania: obrazy lewej kamery kolorowej (12 GB), chmury Velodyne (29 GB), kalibracja (16 MB), etykiety
  treningowe (5 MB). Rozpakowujemy do `data/kitti/training/`.
- **Format:** `label_2` ma 15 kolumn (typ, obcięcie, zasłonięcie, alpha, ramka 2D, wymiary h w l, położenie x y z,
  rotation_y); `location` to środek podstawy ramki 3D w układzie kamery. `calib` zawiera P2, R0_rect
  i Tr_velo_to_cam. `velodyne` to pliki .bin float32 (x, y, z, odbicie).
- **Kamera:** 1,65 m nad drogą (Geiger i in., IJRR 2013, rys. 3).
- **Uwaga:** etykiety ma tylko 7481 obrazów treningowych, więc robimy własny podział.
- **Stan:** pojedyncza klatka pochodzi z publicznego repozytorium z kilkoma klatkami KITTI. Pełny zbiór trzeba jeszcze
  pobrać.

### Seeing Through Fog: prawdziwa mgła, śnieg i deszcz (główny test)

- **Skąd:** rejestracja na [light.princeton.edu](https://light.princeton.edu/datasets/automated_driving_dataset/),
  potem link do pobrania. Każda osoba z zespołu rejestruje się osobno. Narzędzia, podziały (`splits/`) i warunki użycia
  są w [repozytorium SeeingThroughFog](https://github.com/princeton-computational-imaging/SeeingThroughFog).
- **Co ma:** kamera stereo 1920×1024, LiDAR Velodyne HDL-64 (pliki .bin z 5 kolumnami: x, y, z, odbicie, numer wiązki)
  i VLP-32C, ramki 2D i 3D w układzie lewej kamery (format jak KITTI plus dodatkowe kąty), tagi pogody i oświetlenia.
- **Kalibracja:** plik `tools/ProjectionTools/Sweden2KittiCalib/kitti_stereo_velodynehdl_calib.txt` w formacie KITTI.
  Wysokość kamery 1,24 m wynika z kalibracji zewnętrznej (`calib_tf_tree_full.json`) i zgadza się z wysokością drogi
  w chmurze punktów (1,19–1,26 m).
- **Skala:** ok. 13,5 tys. oznaczonych klatek, w tym ok. 5,5 tys. w dobrej pogodzie, 1 tys. lekkiej mgły, 1 tys. gęstej
  mgły i 4 tys. śniegu lub deszczu. Autorzy łączą śnieg i deszcz w jedną kategorię, więc u nas też. Dane z komory
  mgielnej mają tylko ramki 2D, więc je pomijamy.
- **Uwaga:** przy widoczności poniżej 50 m LiDAR widzi do ok. 25 m, więc M3 słabnie, a ramki dalekich aut mogą być mniej
  dokładne albo ich brakować. Nazwy podziałów w `splits/` sprawdzimy po pobraniu.
- **Warunki użycia:** tylko badania i nauka, bez przekazywania danych dalej. Na publikowanych obrazach trzeba zamazać
  ludzi i tablice rejestracyjne.
- **Stan:** pełny zbiór wymaga akceptacji rejestracji. Publiczne repozytorium autorów ma dwie przykładowe klatki, których używamy: jedną
  z dobrej pogody (obraz i LiDAR, bez etykiet) i jedną ze śniegu (sam obraz). Obrazki z nich w `results/one_frame/`
  nie są jeszcze zanonimizowane. To trzeba poprawić.

### SHIFT: dane do dostrajania

- **Skąd:** bez rejestracji, oficjalnie skryptem z [shift-dev](https://github.com/SysCV/shift-dev):

```bash
python download.py --view "[front]" --group "[img, det_2d, det_3d, depth]" --split "[train, val]" --framerate "[images]" --shift "discrete" ./data/shift
```

- **Stan:** 12 listopada 2026 oficjalne serwery nie odpowiadają. Korzystamy z nieoficjalnej kopii na Hugging Face
  (`KevinConnorLee/SHIFT`). Kopia ma nagrania wideo zamiast pojedynczych obrazów, etykiety 3D i plik `seq.csv`
  z pogodą i porą dnia każdej sekwencji. Mapy głębi są w niej tylko dla części `train`, a LiDAR-u nie ma wcale.
  Dopóki serwery nie wrócą, walidację wydzielamy z sekwencji `train`.
- **Co ma:** symulacja CARLA: obrazy, ramki 2D i 3D, mapy głębi (24 bity, rozdzielczość 1 mm); zmiany zachmurzenia,
  deszczu, mgły i pory dnia. Wysokość kamery jest w etykietach (ok. 1,6 m). Licencja CC BY-NC-SA 4.0.
- **Wybór danych:** B to dobra pogoda, C to mgła i deszcz, oba w porównywalnej porze dnia i tej samej liczbie klatek.
  Wybieramy po kolumnach pogody i pory dnia w `seq.csv`.
- **Uwaga:** obraz wygląda jak z gry, dlatego test jest zawsze na prawdziwych danych.

**Nie używamy:** nuScenes, DrivingStereo, osobnych wyników dla nocy.

**Ogólna uwaga:** sprawdzamy, na jakich zbiorach uczono każdy model głębi. Jeśli zbiór testowy był w jego treningu,
zaznaczamy to przy wynikach.

## Kod i zasady pracy

- **Mały, czytelny kod.** Każdy etap to osobny skrypt w `scripts/`. Wspólne funkcje wydzielimy do modułu dopiero wtedy,
  gdy zaczną się powtarzać w kilku skryptach.
- **Narzędzia:** Python 3.13, PyTorch, numpy, OpenCV, Ultralytics YOLO (YOLO26m), transformers. Ultralytics jest
  na licencji AGPL-3.0, dlatego repozytorium też.
- **Sprzęt:** uruchamianie gotowych modeli lokalnie, trening na Colabie lub Kaggle (16 GB) albo na serwerze uczelni.
- Dane, pliki pośrednie i zapisane modele nigdy nie trafiają do gita. Do repozytorium idą tylko wyniki pokazywane
  w README.
- Nie zgadujemy formatów zbiorów: sprawdzamy oficjalne narzędzia albo README zbioru.
- Przed oceną każdego zbioru rysujemy 5 losowych klatek z ramkami 3D, punktami LiDAR-u i ramkami YOLO.
- Stałe ziarna losowości, żeby wyniki dało się powtórzyć.

## Możliwe rozszerzenia

Nie są warunkiem ukończenia projektu i nie zaczynamy ich przed gotowymi wariantami A, B i C.

**Fuzja M1 i M2.** d = w · d1 + (1 − w) · d2. Wagi odwrotnie proporcjonalne do wariancji błędu każdej metody, liczone
na walidacji osobno dla przedziałów odległości i widoczności. Przy teście widoczność szacujemy z samego obrazu,
a nie z etykiety pogody.

**KITTI ze sztuczną mgłą.** Gotowe Multifog KITTI (publiczne archiwa na Dysku Google) albo własna mgła:
I = J · t + A · (1 − t), t = exp(−β · d), β ≈ 3 / V, gdzie V to widoczność w metrach. Mapę głębi d liczymy
z uzupełnionego LiDAR-u, nigdy z M2. Mgła nałożona tylko na obraz nie zmienia LiDAR-u, więc M3 porównujemy tam tylko
z mgłą z [symulatora Hahnera](https://github.com/martinhahner/lidar_fog_sim) albo wcale.
