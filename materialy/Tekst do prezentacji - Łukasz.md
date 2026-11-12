# Teksty do slajdów Łukasza: 1–3 i 7–9

Przy każdym slajdzie jest tekst do powiedzenia oraz objaśnienia do przygotowania. Sam tekst mówiony zajmuje orientacyjnie 5–6 minut, zależnie od tempa i przerw.

## Slajd 1 — temat projektu

### Do powiedzenia

Dzień dobry. Wspólnie z Pawłem przygotowujemy projekt dotyczący szacowania odległości do pojazdów z pojedynczej kamery. Szczególnie interesuje nas działanie takich metod w trudnych warunkach pogodowych oraz to, czy dostrojenie sieci neuronowej pomoże poprawić ich dokładność.

### Wyjaśnienia

Głównym wkładem jest dostrojenie gotowej sieci i sprawdzenie efektu na prawdziwych danych. Poprawa jest hipotezą do zbadania. Na tym slajdzie wystarczy przedstawić temat, bez rozwijania nazw modeli i miar.

## Slajd 2 — geneza projektu, ETS2

### Do powiedzenia

Pomysł na ten projekt wziął się z naszej wcześniejszej pracy. Na pierwszym stopniu studiów tworzyliśmy w zespole autopilota do Euro Truck Simulator 2, czyli gry, w której kieruje się ciężarówką.

Jednym z elementów było wykrywanie pojazdów i sygnalizacji świetlnej. Informacje z obrazu wykorzystywaliśmy do ustalania, kiedy i jak mocno hamować.

Była to tylko część większego projektu. Teraz chcemy skupić się właśnie na szacowaniu odległości: wyznaczać ją w metrach i sprawdzić, jak na dokładność wpływa pogoda.

### Wyjaśnienia

„Odległość w pikselach” oznacza miarę w obrazie. Bez znajomości konkretnego algorytmu nie określamy, czy chodziło o wielkość ramki, jej położenie czy odstęp między punktami. Sam wynik w pikselach nie jest jeszcze odległością do auta w metrach. Dlatego w wypowiedzi zostaje ogólne, zgodne z opisem „informacje z obrazu”.

## Slajd 3 — jedna kamera, stereowizja i LiDAR

### Do powiedzenia

Z pojedynczej kamery otrzymujemy obraz 2D. Możemy rozpoznać na nim pojazd, ale kamera nie podaje nam bezpośrednio, ile metrów nas od niego dzieli.

Informację o głębi można uzyskać na przykład dzięki stereowizji. Porównujemy wtedy położenie tych samych punktów na obrazach z dwóch skalibrowanych kamer.

Inaczej działa LiDAR impulsowy. Wysyła impulsy laserowe i mierzy czas powrotu odbitego światła. Na tej podstawie wyznacza odległości i tworzy chmurę punktów 3D.

My chcemy szacować odległość z jednego obrazu, a pomiary LiDAR-u wykorzystać do porównania. Szczególnie interesują nas mgła, deszcz i śnieg, które utrudniają analizę obrazu. Mogą też zakłócać pomiary LiDAR-u.

Sprawdzimy, jak w takich warunkach zmienia się błąd odległości i czy dostrojenie sieci pomaga go zmniejszyć.

### Wyjaśnienia

- **Obraz 2D:** zawiera wygląd i położenie obiektów w obrazie, ale nie przypisuje im bezpośrednio odległości w metrach. Geometria i wyuczone zależności pozwalają ją szacować.
- **Stereowizja:** różnica położenia odpowiadających sobie punktów w dwóch widokach pozwala obliczyć głębię przy znanej geometrii kamer. Jest tu przykładem wprowadzającym.
- **Kalibracja:** opisuje parametry kamery, np. ogniskową i zniekształcenia. W stereowizji potrzebna jest również znajomość wzajemnego położenia kamer.
- **Mapa głębi:** przypisuje pikselom wartości głębi. **Chmura punktów 3D** opisuje punkty w przestrzeni.
- **LiDAR i pogoda:** mgła osłabia i rozprasza światło, co może powodować utratę pomiarów oraz dodatkowe odbicia. Skala problemu zależy od czujnika i warunków.

Podstawa techniczna: [model kamery](https://docs.opencv.org/4.13.0/d9/d0c/group__calib3d.html), [stereowizja](https://docs.opencv.org/4.13.0/dd/d53/tutorial_py_depthmap.html), [LiDAR we mgle](https://openaccess.thecvf.com/content/ICCV2021/papers/Hahner_Fog_Simulation_on_Real_LiDAR_Point_Clouds_for_3D_Object_ICCV_2021_paper.pdf).

## Slajd 7 — nasz wkład i warianty A/B/C

### Do powiedzenia

Naszym głównym wkładem będzie dostrojenie gotowej sieci Depth Anything V2 Metric. Bierzemy model, który już potrafi szacować głębię, i uczymy go dalej na przykładach związanych z naszym zadaniem.

Na schemacie mamy jeden model wyjściowy i trzy jego warianty. A pozostawimy bez zmian. B dostroimy na obrazach z dobrą pogodą, a C na obrazach z mgłą i deszczem.

Wariant B jest kontrolą. Dzięki niemu sprawdzimy, czy trening na złej pogodzie daje więcej niż sam dodatkowy trening na dobrej pogodzie. B i C zaczną od tych samych wag modelu A. Zachowamy te same ustawienia, liczbę klatek i kroków uczenia oraz podobną porę dnia.

Do dostrajania wykorzystamy SHIFT, czyli dane z symulatora, zawierające obrazy i mapy głębi w metrach. Następnie wszystkie trzy warianty sprawdzimy na tych samych prawdziwych zdjęciach. Dopiero ten test pokaże, czy takie dostrojenie pomaga.

### Wyjaśnienia

| Pojęcie | Znaczenie |
|---|---|
| Dostrajanie | Dalsze uczenie gotowej sieci, podczas którego zmieniają się jej wagi. |
| A | Gotowy model bez dodatkowego uczenia, punkt odniesienia. |
| B | Dodatkowe uczenie na dobrej pogodzie, wariant kontrolny. |
| C | Dodatkowe uczenie na mgle i deszczu, badany wariant. |
| Metric | Wynik wyrażony w metrach. Jednostka nie gwarantuje dokładności. |

A/B/C dotyczą wyłącznie Depth Anything V2 Metric. Trzy rodzaje porównywanych metod w całym projekcie to geometria, sieci głębi i LiDAR.

B i C wykorzystują różne sceny, więc kontrola nie pozwala twierdzić, że jedyną różnicą między danymi jest pogoda. Jeżeli C nie poprawi wyników, również raportujemy ten wynik. Fuzja i własna sztuczna mgła pozostają opcjonalnymi rozszerzeniami.

Autorzy udostępniają model metryczny i kod do jego uczenia: [Depth Anything V2 Metric](https://github.com/DepthAnything/Depth-Anything-V2/blob/main/metric_depth/README.md).

## Slajd 8 — zakres projektu i ocena wyników

### Do powiedzenia

Wynikiem naszego zadania będzie odległość w metrach do konkretnego pojazdu. Oszacowania porównamy z odległościami referencyjnymi, które wyznaczymy z oznaczonych ramek 3D aut.

Wyniki podzielimy według pogody oraz odległości: do 20 metrów, od 20 do 40 i powyżej 40 metrów. Dzięki temu zobaczymy, w jakich warunkach i na jakim dystansie pojawiają się największe problemy.

Sprawdzimy wielkość błędu, czy metoda zawyża lub zaniża odległość oraz dla ilu aut pomyłka jest mniejsza niż 10 procent. Osobno policzymy, ile pojazdów udało się wykryć. To ważne, bo dobra dokładność dla kilku widocznych aut nie mówi jeszcze, ile innych pojazdów system pominął.

Warianty A, B i C porównamy na tych samych klatkach i pojazdach. Wpływ pogody ocenimy w obrębie tego samego zbioru danych.

### Wyjaśnienia

| Pojęcie | Znaczenie |
|---|---|
| Ramka 3D | Przestrzenne pudełko opisujące położenie i rozmiar pojazdu. Służy do wyznaczenia odległości referencyjnej. |
| AbsRel | Średni błąd bezwzględny podzielony przez odległość referencyjną. Pomyłka o 2 m przy 20 m daje 10% błędu względnego. |
| RMSE | Błąd w metrach, mocniej reagujący na duże pomyłki. |
| Średni błąd ze znakiem | Przy definicji „oszacowanie minus odniesienie” wynik dodatni oznacza zawyżanie, a ujemny zaniżanie. Przeciwne błędy mogą się znosić. |
| Odsetek z błędem poniżej 10% | Jaka część ocenionych aut spełnia wybrany próg. To kryterium projektu. |
| Wykrywanie pojazdów | Osobna ocena tego, ile rzeczywistych aut detektor znalazł. Warto również raportować fałszywe wykrycia. |

Definicje AbsRel i RMSE są zgodne z miarami stosowanymi w ocenie głębi: [implementacja Monodepth2](https://github.com/nianticlabs/monodepth2/blob/master/layers.py).

Pozostałe założenia do dopowiedzenia w razie pytania:

- Oceniamy pojedyncze klatki. Wideo służy do końcowego demo.
- Zakładane klasy to auta osobowe, dostawcze, ciężarówki i autobusy. Trzeba uzgodnić ich etykiety między zbiorami.
- Kod udostępnimy na GitHubie, bez surowych danych ze zbiorów.

W planie odległość odnosi się do głębi wzdłuż osi kamery. Wszystkie metody muszą korzystać z tej samej definicji odniesienia. Mediana głębi w ramce jest przybliżeniem i nie jest automatycznie dokładną odległością do najbliższej ściany auta.

Porównanie pogody w obrębie jednego zbioru ogranicza różnice kamery i sposobu zbierania danych. Nadal pozostają różnice między scenami, więc nie jest to eksperyment izolujący wyłącznie pogodę.

## Slajd 9 — dane do uczenia i testów

### Do powiedzenia

Każdy z tych zbiorów wykorzystamy do innego etapu pracy.

SHIFT posłuży do dostrajania sieci. To dane z symulatora, więc oprócz obrazów mamy również referencyjne mapy głębi, potrzebne do uczenia.

Z SHIFT wydzielimy osobne sceny do walidacji. Na nich dobierzemy ustawienia treningu i wybierzemy wersję modelu do końcowego sprawdzenia.

Główny test przeprowadzimy na Seeing Through Fog. Są tam prawdziwe sceny w dobrej i złej pogodzie. Sprawdzimy więc, czy uczenie na symulacji pomaga również na rzeczywistych zdjęciach.

KITTI wykorzystamy do uruchomienia metod i sprawdzenia, czy dostrajanie nie pogorszyło wyników w dobrej pogodzie. Część używaną do dopracowania metod oddzielimy od części przeznaczonej do końcowej oceny.

Dane testowe zostawiamy na końcowy sprawdzian, po zakończeniu doboru ustawień.

### Wyjaśnienia

- **Uczenie:** na tych przykładach model zmienia swoje wagi.
- **Walidacja:** pomaga wybrać ustawienia i moment zakończenia uczenia. Wyniki wpływają na decyzje o modelu.
- **Test:** końcowa ocena po podjęciu tych decyzji. Nie służy do dalszego wybierania ustawień.
- **Podział według scen:** niemal identyczne sąsiednie klatki nie powinny trafiać do części uczącej i walidacyjnej. Rozdzielamy całe sceny lub sekwencje.
- **Symulacja a rzeczywistość:** wygląd obrazów może się różnić. Dlatego poprawa po uczeniu na SHIFT wymaga sprawdzenia na prawdziwych zdjęciach.
- **KITTI:** własny test wydzielamy z danych z publicznymi etykietami. Autorzy wskazują taki sposób oceny dla projektów studenckich.
- **Gotowa symulacja SHIFT:** korzystanie z niej nie wymaga samodzielnego dodawania mgły do zdjęć KITTI.

Źródła: [SHIFT](https://github.com/SysCV/shift-dev), [Seeing Through Fog](https://github.com/princeton-computational-imaging/SeeingThroughFog), [zasady oceny KITTI](https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d), [podział danych na uczenie, walidację i test](https://scikit-learn.org/stable/modules/cross_validation.html).

## Krótkie odpowiedzi na możliwe pytania

**Co jest Waszym wkładem?**  
Dostrojenie gotowej sieci głębi na złej pogodzie, porównanie z wariantem kontrolnym i ocena odległości do konkretnych aut na prawdziwych danych.

**Po co wariant B?**  
Żeby sprawdzić, czy trening na złej pogodzie daje większą korzyść niż taki sam dodatkowy trening na dobrej pogodzie.

**Dlaczego uczycie na symulacji?**  
Dostarcza obrazy wraz z referencyjną głębią. Sprawdzenie na prawdziwych zdjęciach pokaże, czy efekt przenosi się poza symulator.

**Co jeśli dostrajanie nie pomoże?**  
To również wynik eksperymentu. Opiszemy, w jakich warunkach pomaga, nie pomaga lub pogarsza działanie.

**Czy LiDAR jest prawdą referencyjną?**  
Porównujemy wyniki z oznaczonymi ramkami 3D. Pomiary LiDAR-u i te oznaczenia mogą być ze sobą powiązane, więc LiDAR-u nie traktujemy jako niezależnego, bezbłędnego wzorca.

