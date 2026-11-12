# Opis projektu: odległość do pojazdów z pojedynczej kamery w złej pogodzie

## Temat i cel

**Szacowanie odległości do pojazdów z pojedynczej kamery w trudnych warunkach pogodowych** (ang. *Monocular Vehicle Distance Estimation under Adverse Weather Conditions*).

Mierzymy odległość do aut przed nami trzema metodami — dwiema z kamery i jedną z LiDAR-u — i sprawdzamy, jak pogarszają ją mgła, śnieg i deszcz. Głównym wkładem projektowym jest dostrojenie sieci głębi Depth Anything V2 Metric na symulowanych danych z mgłą i deszczem (SHIFT). Sprawdzamy hipotezę, że takie dostrojenie zmniejsza błąd odległości do aut na prawdziwych danych. Prawdziwą odległość bierzemy z oznaczonych ramek 3D aut. Repozytorium: `fogrange-monocular-vehicle-distance`.

## Problem

Odległość z jednej kamery nie wynika wprost z obrazu, więc trzeba ją oszacować: z geometrii kamery albo siecią neuronową. Sieci głębi z jednej kamery wciąż nie są równo niezawodne w różnej pogodzie ([ISPRS 2026](https://isprs-annals.copernicus.org/articles/XI-2-2026/473/2026/)).

LiDAR też traci w złej pogodzie: przy widoczności poniżej 50 m jego zasięg spada do ok. 25 m ([Bijelic i in., CVPR 2020](https://openaccess.thecvf.com/content_CVPR_2020/papers/Bijelic_Seeing_Through_Fog_Without_Seeing_Fog_Deep_Multimodal_Sensor_Fusion_CVPR_2020_paper.pdf)). Sprawdzamy, jak trzy sposoby pomiaru wypadają przy odległości do konkretnych aut, w zależności od pogody i odległości.

## Co robimy

Porównujemy trzy metody; każda podaje odległość do auta wykrytego przez YOLO.

1. **Metoda 1: YOLO + geometria (kamera).** Odległość ze wzoru kamery otworkowej: z wysokości kamery i dolnej krawędzi ramki albo z typowej wysokości auta.
2. **Metoda 2: sieć głębi (kamera).** UniDepth V2 i Depth Anything V2 Metric szacują odległość każdego piksela; bierzemy medianę wewnątrz ramki auta. Dostrajamy tylko Depth Anything V2 Metric. Ewentualny dodatkowy gotowy model (np. Depth Pro) służy wyłącznie do porównania, bez dostrajania.
3. **Metoda 3: dane z LiDAR-u.** Punkty chmury rzutowane do ramki auta. Ramki 3D oznaczano z pomocą LiDAR-u, więc w dobrej pogodzie ta metoda wypada prawie idealnie z samej konstrukcji pomiaru; ciekawe jest, ile traci w mgle.

Wzory metody 1 (lewy: z wysokości kamery, prawy: z wysokości auta):

```latex
Z = \frac{f \cdot H_{kamery}}{y_{dol} - y_{horyzont}} \qquad Z = \frac{f \cdot h_{auta}}{h_{ramki}}
```

f to ogniskowa w pikselach, H wysokość kamery nad drogą, y położenie dolnej krawędzi ramki i horyzontu w obrazie, h wysokość auta w metrach i ramki w pikselach.

**Wkład projektowy: dostrojenie sieci głębi.** Porównujemy trzy warianty Depth Anything V2 Metric:

- **A:** gotowy model, bez dostrajania;
- **B (kontrola):** dostrojony na SHIFT w dobrej pogodzie;
- **C:** dostrojony na SHIFT z mgłą i deszczem.

B i C startują z tego samego modelu, z tymi samymi ustawieniami, tą samą liczbą klatek i kroków treningu oraz w porównywalnej porze dnia. Wariant B oddziela korzyść z danych ze złą pogodą od korzyści z samego dodatkowego treningu. Zbiory B i C to różne sceny, więc nie twierdzimy, że różni je wyłącznie pogoda. Punktami odniesienia są geometria (metoda 1), gotowe sieci głębi i LiDAR (metoda 3).

**Możliwe rozszerzenia (nieobowiązkowe, nie są warunkiem ukończenia projektu):** fuzja metod 1 i 2 oraz KITTI z mgłą nałożoną przez nas. Pracujemy na pojedynczych oznaczonych klatkach; wideo służy tylko do filmu demo.

## Dane

**SHIFT:** dostrajanie (warianty B i C) z wydzieloną częścią walidacyjną. **Seeing Through Fog:** główny test w prawdziwej złej pogodzie, w porównaniu z jego częścią nagraną w dobrej pogodzie. **KITTI:** uruchomienie metod i sprawdzian, czy dostrojenie nie pogorszyło wyników w dobrej pogodzie.

| Zbiór | Warunki | Prawda o odległości | Rola w projekcie | Dostęp |
| --- | --- | --- | --- | --- |
| [KITTI 3D Object](https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d) | dzień, dobra pogoda | ramki 3D z LiDAR-u | uruchomienie metod; sprawdzian, czy dostrojenie nie pogorszyło dobrej pogody | rejestracja, od ręki |
| [Seeing Through Fog](https://light.princeton.edu/datasets/automated_driving_dataset/) | prawdziwa lekka i gęsta mgła, śnieg/deszcz; też dobra pogoda | ramki 3D z LiDAR-u | główny test: dobra kontra zła pogoda, warianty A, B, C | rejestracja z akceptacją |
| [SHIFT](https://www.vis.xyz/shift) | symulator CARLA: mgła i deszcz; też dobra pogoda | ramki 3D i dokładne mapy głębi z symulatora | dostrajanie (C: mgła i deszcz, B: dobra pogoda); walidacja na wydzielonej części | bez rejestracji |
| KITTI ze sztuczną mgłą (możliwe rozszerzenie) | mgła liczona fizycznie, kilka poziomów widoczności | te same ramki 3D co w KITTI | porównanie mgły sztucznej z prawdziwą | [Multifog KITTI](https://mdpi-res.com/d_attachment/sensors/sensors-21-06711/article_deploy/sensors-21-06711-v2.pdf) na prośbę albo mgła nałożona przez nas |

Ustawienia treningu i metod (liczbę kroków, wybór checkpointu, obszar ramki dla sieci głębi) wybieramy na walidacji SHIFT i na części treningowej KITTI. Zbiorów testowych (Seeing Through Fog, część testowa KITTI) do tego nie używamy.

Od razu: rejestracja w Seeing Through Fog, bo wymaga akceptacji. SHIFT pobiera się bez rejestracji. Gdyby powstało rozszerzenie ze sztuczną mgłą: prośba do autorów Multifog KITTI albo własna mgła (wzór Koschmiedera na obrazach, [symulator Hahnera](https://github.com/martinhahner/lidar_fog_sim) na chmurach LiDAR-u).

## Wymóg zaliczenia i etapy kursu

Zaliczenie opieramy na propozycji lepszego rozwiązania: sieci głębi dostrojonej pod złą pogodę (transfer learning z danych symulowanych na prawdziwe). To wkład projektowy, nie deklarujemy światowej nowości. To, czy dostrojenie poprawia wyniki, jest hipotezą, którą sprawdzamy; wynik negatywny też raportujemy. Nie tworzymy nowej bazy.

1. **Przegląd:** metody geometryczne, sieci głębi z jednej kamery, praca w złej pogodzie (md4all, WeatherDepth, Depth Anything AC), zbiory ze sztuczną złą pogodą (Multifog KITTI, KITTI-C).
2. **Odtworzenie:** trzy metody na KITTI, porównanie z ramkami 3D.
3. **Dostosowanie do naszych danych:** Seeing Through Fog, wyniki w podziale na warunki i odległość.
4. **Lepsze rozwiązanie:** dostrojenie Depth Anything V2 Metric na SHIFT z mgłą i deszczem (C) z kontrolą na dobrej pogodzie (B); możliwe rozszerzenia: fuzja metod 1 i 2, KITTI ze sztuczną mgłą.

## Jak ocenimy wyniki

Miary: średni błąd względny (AbsRel), średni błąd ze znakiem (czy mgła zawyża, czy zaniża odległość), RMSE, odsetek aut z błędem poniżej 10% oraz skuteczność wykrywania aut.

Wyniki dzielimy na warunki (dobra pogoda, lekka mgła, gęsta mgła, śnieg/deszcz) i odległości (0–20 m, 20–40 m, ponad 40 m). Wpływ pogody i dostrojenia liczymy w obrębie jednego zbioru (Seeing Through Fog w dobrej kontra złej pogodzie dla wariantów A, B, C; KITTI dla A, B, C), bo skala sieci głębi zależy od kamery. Na prezentację końcową przygotujemy film z odległością nad każdym autem.

## Źródła

- [KITTI 3D Object](https://www.cvlibs.net/datasets/kitti/eval_object.php?obj_benchmark=3d)
- [Seeing Through Fog: pobieranie](https://light.princeton.edu/datasets/automated_driving_dataset/), [repozytorium](https://github.com/princeton-computational-imaging/SeeingThroughFog) i [artykuł (Bijelic i in., CVPR 2020)](https://openaccess.thecvf.com/content_CVPR_2020/papers/Bijelic_Seeing_Through_Fog_Without_Seeing_Fog_Deep_Multimodal_Sensor_Fusion_CVPR_2020_paper.pdf)
- [SHIFT (CVPR 2022)](https://arxiv.org/abs/2206.08367) i [SHIFT DevKit](https://github.com/SysCV/shift-dev)
- [Evaluation of Metric Monocular Depth Estimation Models Under Adverse Weather (ISPRS 2026)](https://isprs-annals.copernicus.org/articles/XI-2-2026/473/2026/)
- [md4all (Gasperini i in., ICCV 2023)](https://openaccess.thecvf.com/content/ICCV2023/html/Gasperini_Robust_Monocular_Depth_Estimation_under_Challenging_Conditions_ICCV_2023_paper.html) i [WeatherDepth](https://arxiv.org/html/2310.05556)
- [Depth Anything AC](https://arxiv.org/abs/2507.01634), [UniDepth](https://arxiv.org/pdf/2403.18913), [Depth Anything V2 Metric](https://huggingface.co/spaces/depth-anything/Depth-Anything-V2/blob/0811d77a41e746dba19012d2907007075953be2f/metric_depth/README.md)
- [Multifog KITTI (Mai i in., Sensors 2021)](https://mdpi-res.com/d_attachment/sensors/sensors-21-06711/article_deploy/sensors-21-06711-v2.pdf) i [RoboDepth / KITTI-C (NeurIPS 2023)](https://ar5iv.labs.arxiv.org/html/2310.15171)
- [Symulator mgły dla LiDAR-u (Hahner i in.)](https://github.com/martinhahner/lidar_fog_sim)
