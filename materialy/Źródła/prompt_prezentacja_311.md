Pomóż mi poprawić **prezentację nr 1** do projektu z przedmiotu Wizja komputerowa. Projekt robimy w 2 osoby. Mamy już wersję z 10 slajdami; potrzebuję planu slajd po slajdzie zgodnego z poniższymi ustaleniami (stan na 3.11.2026).

## Wymagania kursu

- **Zaliczenie:** propozycja nowego rozwiązania konkretnego problemu albo nowej funkcjonalności w określonym zadaniu, albo stworzenie nowej bazy danych i zastosowanie na niej np. transfer learningu.
- **Etapy projektu:** 1) przegląd dostępnych rozwiązań, 2) odtworzenie najlepszych rozwiązań, 3) dostosowanie modeli do swojej bazy danych, 4) propozycja nowego lub lepszego rozwiązania.
- **Zakres prezentacji 1:** temat projektu, definicja problemu, przykłady dostępnych rozwiązań, zaproponowane rozwiązanie lub funkcjonalność, założenia projektowe, plan zadań, źródła (publikacje, bazy, architektury).
- **Terminy:** prezentacja 1: grupa 1 — 4.11.2026, grupa 2 — 18.11.2026 (jesteśmy w grupie [UZUPEŁNIJ]). Sprawozdanie: 9.12.2026, 23:59. Prezentacja końcowa z wynikami liczbowymi i filmem: 13.01.2027 (grupa 1) lub 20.01.2027 (grupa 2).
- **Czas na prezentację:** [UZUPEŁNIJ; jeśli brak, przyjmij 10 minut].

## Projekt

**Temat:** Szacowanie odległości do pojazdów z pojedynczej kamery w trudnych warunkach pogodowych (ang. *Monocular Vehicle Distance Estimation under Adverse Weather Conditions*). Repozytorium: `fogrange-monocular-vehicle-distance`.

**Problem:** odległość z jednej kamery nie wynika wprost z obrazu, trzeba ją oszacować. Sieci głębi z jednej kamery wciąż nie są równo niezawodne w różnej pogodzie. LiDAR też ma słabości: w mgle o widoczności poniżej 50 m jego zasięg spada do około 25 m. Sprawdzamy, jak trzy sposoby pomiaru wypadają przy odległości do konkretnych aut i czy dostrojenie sieci głębi na złej pogodzie pomaga.

**Badane metody** (każda podaje odległość do auta wykrytego przez YOLO):

1. **YOLO + geometria (kamera):** odległość z wysokości kamery i dolnej krawędzi ramki auta albo z typowej wysokości auta i wysokości ramki w pikselach (wzór kamery otworkowej).
2. **Sieć głębi (kamera):** UniDepth V2 (przyjmuje parametry kamery) i Depth Anything V2 Metric (nie przyjmuje) zwracają odległość każdego piksela; bierzemy medianę wewnątrz ramki auta. Dostrajamy tylko Depth Anything V2 Metric. Depth Pro, jeśli zostaje na slajdach, występuje wyłącznie jako dodatkowy gotowy model do porównania, bez dostrajania.
3. **Dane z LiDAR-u:** punkty chmury rzutowane do ramki auta. Ramki 3D oznaczano z pomocą LiDAR-u, więc w dobrej pogodzie ta metoda wypada prawie idealnie z samej konstrukcji pomiaru; ciekawe jest, ile traci w mgle.

**Prawdziwa odległość (ground truth):** oznaczone ramki 3D aut; bierzemy odległość do najbliższej ściany auta wzdłuż osi kamery.

**Wkład projektowy (główny):** dostrojenie Depth Anything V2 Metric na symulowanych danych z mgłą i deszczem (SHIFT) i sprawdzenie, czy zmniejsza błąd odległości do konkretnych aut na prawdziwych danych. Poprawa jest hipotezą do sprawdzenia, nie obietnicą. Trzy warianty:

- **A:** gotowy model, bez dostrajania;
- **B (kontrola):** dostrojony na SHIFT w dobrej pogodzie;
- **C:** dostrojony na SHIFT z mgłą i deszczem.

B i C: ten sam model startowy, te same ustawienia, ta sama liczba klatek i kroków treningu, porównywalna pora dnia. Wariant B oddziela korzyść z danych ze złą pogodą od korzyści z samego dodatkowego treningu. Nie mówimy, że jedyną różnicą jest pogoda, bo B i C to różne sceny. Punktami odniesienia są geometria, gotowe sieci głębi i LiDAR.

**Możliwe rozszerzenia (nieobowiązkowe, nie są warunkiem ukończenia):** fuzja metod 1 i 2, KITTI z mgłą nałożoną przez nas. Na slajdach tylko jedno zdanie na slajdzie z wkładem projektowym, bez osobnego slajdu.

## Dostępne rozwiązania (do slajdu z przeglądem)

- Geometria jednej kamery w tempomacie adaptacyjnym: [Stein, Mano, Shashua, IEEE IV 2003](https://ieeexplore.ieee.org/abstract/document/1212895).
- Sieci szacujące odległość do obiektów: [DisNet, Haseeb i in., 2018](https://paperswithcode.com/paper/disnet-a-novel-method-for-distance-estimation); [Zhu, Fang, ICCV 2019](https://openaccess.thecvf.com/content_ICCV_2019/html/Zhu_Learning_Object-Specific_Distance_From_a_Monocular_Image_ICCV_2019_paper.html) (KITTI).
- Sieci głębi metrycznej: [UniDepth](https://arxiv.org/pdf/2403.18913), Depth Anything V2 Metric, [Depth Pro](https://arxiv.org/abs/2410.02073), [Depth Anything AC](https://arxiv.org/abs/2507.01634) (odporność na warunki).
- Głębia z jednej kamery w złych warunkach: [md4all (Gasperini i in., ICCV 2023)](https://openaccess.thecvf.com/content/ICCV2023/html/Gasperini_Robust_Monocular_Depth_Estimation_under_Challenging_Conditions_ICCV_2023_paper.html), [WeatherDepth (Wang i in., 2024)](https://arxiv.org/html/2310.05556).
- Ewaluacja sieci głębi w złej pogodzie: [ISPRS 2026](https://isprs-annals.copernicus.org/articles/XI-2-2026/473/2026/).
- LiDAR i kamera w mgle oraz zbiór Seeing Through Fog: [Bijelic i in., CVPR 2020](https://openaccess.thecvf.com/content_CVPR_2020/papers/Bijelic_Seeing_Through_Fog_Without_Seeing_Fog_Deep_Multimodal_Sensor_Fusion_CVPR_2020_paper.pdf).

Co robimy sami (wkład projektowy, bez deklarowania światowej nowości): dostrojenie metrycznej sieci głębi pod złą pogodę z wariantem kontrolnym, ocenione na odległości do konkretnych aut na prawdziwych danych, obok geometrii i LiDAR-u w tych samych warunkach.

## Dane (stan na 3.11.2026)

| Zbiór | Skąd | Co zawiera | Rola | Ograniczenia |
| --- | --- | --- | --- | --- |
| SHIFT | [shift-dev](https://github.com/SysCV/shift-dev), bez rejestracji | symulacja CARLA: obrazy, ramki 3D, dokładne mapy głębi; mgła, deszcz i dobra pogoda | dostrajanie (C: mgła i deszcz, B: dobra pogoda); wydzielona walidacja do wyboru ustawień | obraz wygląda „growo”, dlatego test na prawdziwych danych |
| Seeing Through Fog | [light.princeton.edu](https://light.princeton.edu/datasets/automated_driving_dataset/), rejestracja z akceptacją | kamera 1920×1024, LiDAR 64 wiązki, ramki 3D, tagi pogody; ok. 13,5 tys. oznaczonych klatek | główny test prawdziwej złej pogody: dobra kontra zła pogoda, warianty A, B, C | ok. 1 tys. klatek z gęstą mgłą; śnieg i deszcz połączone |
| KITTI 3D Object | [cvlibs.net](https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d), rejestracja | obrazy, LiDAR 64 wiązki, kalibracja, ramki 3D (7481 obrazów z etykietami) | uruchomienie metod; sprawdzian, czy dostrojenie nie pogorszyło dobrej pogody | tylko dzień i dobra pogoda |

Zbiór testowy nie służy do wyboru ustawień treningu ani metod (do tego walidacja SHIFT i część treningowa KITTI). Nie używamy nuScenes ani DrivingStereo i nie podajemy osobnych wyników dla nocy.

## Założenia projektowe

- Wejście: jeden obraz z przedniej kamery i jej kalibracja; wyjście: odległość w metrach do każdego wykrytego pojazdu. Ocena na pojedynczych oznaczonych klatkach; wideo tylko do filmu demo.
- Klasy: samochody osobowe, dostawcze, ciężarowe, autobusy.
- Warunki: dobra pogoda, lekka mgła, gęsta mgła, śnieg/deszcz (w Seeing Through Fog śnieg i deszcz są połączone). Na slajdach piszemy „trudne warunki”.
- Odległości: 0–20 m, 20–40 m, ponad 40 m.
- Miary: średni błąd względny (AbsRel), średni błąd ze znakiem (czy mgła zawyża, czy zaniża odległość), RMSE, odsetek aut z błędem poniżej 10%, skuteczność wykrywania aut.
- Wpływ pogody i dostrojenia liczymy w obrębie jednego zbioru (Seeing Through Fog w dobrej kontra złej pogodzie; KITTI dla A, B, C), bo skala sieci głębi zależy od kamery.
- Kod publicznie na GitHubie, bez surowych danych (licencje zbiorów).

## Plan zadań

- **Do prezentacji 1:** przegląd literatury, rejestracja w Seeing Through Fog, pobranie KITTI i SHIFT, uruchomienie YOLO + geometrii i LiDAR-u na KITTI (pierwsze wyniki, jeśli zdążymy).
- **Do 9.12 (sprawozdanie):** gotowe sieci głębi na KITTI i Seeing Through Fog (dobra kontra zła pogoda), przygotowanie danych SHIFT i pierwsze próbne dostrojenie na małym podzbiorze (czy potok treningu działa).
- **Grudzień–styczeń:** pełne dostrojenie wariantów B i C, ocena A, B, C na Seeing Through Fog i KITTI; rozszerzenia tylko, jeśli starczy czasu.
- **Do 13.01:** końcowe tabele, film z odległościami nad autami, README.

## Proponowany układ 10 slajdów

1. Temat i zespół.
2. Problem: dlaczego odległość z jednej kamery w złej pogodzie jest trudna; LiDAR też traci w mgle.
3. Dostępne rozwiązania: dwa, trzy przykłady i jedna tabela.
4. Dane i ich role: SHIFT, Seeing Through Fog, KITTI.
5. Metody: schemat M1, M2, M3 i porównanie z ramkami 3D.
6. Wkład projektowy: warianty A, B, C, hipoteza, po co kontrola; jedno zdanie o możliwych rozszerzeniach.
7. Założenia projektowe: wejście i wyjście, klasy, warunki, przedziały odległości.
8. Jak ocenimy wyniki: miary, podziały, co jest zbiorem testowym.
9. Plan zadań do 9.12 i do stycznia.
10. Źródła.

## Czego od Ciebie oczekuję

1. Plan dokładnie 10 slajdów. Dla każdego: tytuł, 3–5 punktów, propozycja grafiki lub schematu, 1–2 zdania notatek dla mówcy, kto mówi (Osoba A / Osoba B) i orientacyjny czas.
2. Pokryj wszystkie punkty zakresu prezentacji 1 i zaznacz, który slajd odpowiada któremu punktowi.
3. Slajd z przeglądem odchudź: dwa lub trzy przykłady plus jedna tabela.
4. Brak osobnego slajdu o fuzji i sztucznej mgle; jedno zdanie o możliwych rozszerzeniach na slajdzie z wkładem projektowym. Na schemacie metod pokaż, że dostrojenie zmienia metodę 2.
5. Słownictwo: „wkład projektowy”, „sprawdzamy, czy…”, „hipoteza”. Nie pisz „pierwsi”, „nowatorska metoda” ani „poprawimy wyniki”. Nie pisz, że B i C różni wyłącznie pogoda.
6. Usuń ze slajdów nuScenes, DrivingStereo i osobne wyniki dla nocy. Depth Pro zostaw tylko jako gotowy model do porównania albo usuń.
7. Nie wymyślaj wyników. Jeśli do prezentacji nie będzie jeszcze wyników, zaproponuj slajd bez nich (np. schemat metod) zamiast pustego miejsca.
8. Na końcu: lista rzeczy do przygotowania (schematy, zrzuty, tabele) oraz 3 pytania, które może zadać prowadząca, z krótkimi odpowiedziami (np. co tu jest nowego, po co wariant kontrolny, czy LiDAR nie jest po prostu prawdą).
9. Jeśli poniżej wkleiłem treść obecnych slajdów, popraw je według tego opisu zamiast pisać od nowa i wypisz, co zmieniłeś na każdym slajdzie.
10. Pisz po polsku i zwięźle.

[OPCJONALNIE: tu wklej treść obecnych 10 slajdów]
