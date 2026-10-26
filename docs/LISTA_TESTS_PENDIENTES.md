# Lista de tests pendientes en la PC del laboratorio

Actualizada: **26/10/2026**. Solo el test de prueba con **1a30** (no el core set de 285 complejos,
que queda reservado para el video).

Cada test termina con `RESULT: PASS` o `RESULT: FAIL`. Anotar el resultado en
`docs/CombiLabHUB_etapas.xlsx`, hoja **Estado SF**, columnas *Test Docker 1a30* (Q) y
*Test Windows conda 1a30* (R).

## 1. Tests listos para correr (plugins ya terminados)

| # | SF | Nivel / Lista | Windows conda (`plugins\<sf>\demo_<sf>.bat`) | Docker (`plugins\<sf>\docker_<sf>.bat`) | Nota |
|---|---|---|---|---|---|
| 1 | RFL-Score | 1 / L1 | **Pendiente** (`demo_rfl_score.bat`, solo el modelo R) | PASS | |
| 2 | HAC-Net | 2 / L1 | PASS | **Pendiente** | Usa ChargeFW2 dentro de la imagen |
| 3 | IGModel | 2 / L1 | **Pendiente** | **Pendiente** | |
| 4 | ConBAP | 2 / L1 | **Pendiente** | **Pendiente** | |
| 5 | DeepBindGCN | 2 / L1 | **Pendiente** | **Pendiente** | |
| 6 | GraphscoreDTA | 2 / L1 | **Pendiente** | **Pendiente** | No puntúa 1a30: el test compara las 279 predicciones de los autores |
| 7 | PointNet / PointTransformer | 3 / L1 | **Pendiente** (`demo_pointnet.bat`, solo los modelos) | **Pendiente** | La nube de puntos se arma solo en Linux/Docker |
| 8 | PIGNet2 | 3 / L1 | **Pendiente** | **Pendiente** | Corre en CPU |
| 9 | BAPA | 3 / L1 | **Pendiente** | **Pendiente** | |

Ya probadas en la PC (no hace falta repetir): ET-Score, GB-Score, OnionNet-2, SFCNN, PLANET,
egGNN, GIGN, EHIGN-PLA, saCNN, DEAttentionDTA (Windows conda y Docker), delta_LinF9_XGB (Docker),
DeepRLI, MMPD-DTA, DTITR (Windows conda y Docker) y T-ALPHA (Docker).

### Cómo correrlos

**Docker, todos los pendientes de una vez** (Docker Desktop abierto; cada log queda en
`PROYECTO_UNIVERSIDAD\resultados_docker\`, y el resumen en `resumen.txt`):

```bat
cd C:\Users\Admin\Desktop\PROYECTO_UNIVERSIDAD\combi_lab_hub_tmp
git pull
tools\docker_test_all.bat hacnet igmodel conbap deepbindgcn graphscoredta pointnet pignet2 bapa
```

**Windows conda, uno por uno** (doble clic en cada `.bat`, o desde una consola):

```bat
plugins\rfl_score\demo_rfl_score.bat
plugins\igmodel\demo_igmodel.bat
plugins\conbap\demo_conbap.bat
plugins\deepbindgcn\demo_deepbindgcn.bat
plugins\graphscoredta\demo_graphscoredta.bat
plugins\pointnet\demo_pointnet.bat
plugins\pignet2\demo_pignet2.bat
plugins\bapa\demo_bapa.bat
```

Si alguno falla, guardar la ventana o el log y pasármelo.

## 2. SF que todavía no tienen test (esperan una descarga)

Estos archivos no se pueden bajar ni desde la nube ni desde la PC porque los dominios están
fuera de la lista permitida. Hay dos opciones: agregar los dominios en claude.ai (Configuración →
Capacidades) o bajar los archivos a mano con el navegador y dejarlos en `SOFTWARE SF`.

| SF | Lista | Archivo que falta | Dónde está | Dominio a habilitar |
|---|---|---|---|---|
| Dynaformer | L1 | `model1.pt`, `model2.pt`, `model3.pt` (checkpoints) | OneDrive de los autores (link en `checkpoint/README.md` del repo) | 1drv.ms, onedrive.live.com, api.onedrive.com |
| TopoFormer | L1 | `finetuned_casf2016_3models.tar.gz` | weilab.math.msu.edu/Downloads/TopoFormer/ | weilab.math.msu.edu |
| DTA-GTOmega | L2 | `release1.pt` (pesos de OmegaFold, ~3 GB) | helixon.s3.amazonaws.com/release1.pt | helixon.s3.amazonaws.com |
| DBGT-PLA | L2 | `pdbbind.tgz` (grafos de interacción IChem) | bioinfo-pharma.u-strasbg.fr/labwebsite/downloads/pdbbind.tgz | bioinfo-pharma.u-strasbg.fr |
| EGNA | L1 | Perfil HHblits (`.hhm`) de la secuencia de 1a30 | Se genera en el servidor web HHblits (toolkit.tuebingen.mpg.de) | — (lo hace una persona en el navegador) |

Cuando estén los archivos, armo el plugin y queda el test 1a30 para agregar a la sección 1.

## 3. Sin test (descartadas o bloqueadas por otra razón)

| SF | Lista | Motivo |
|---|---|---|
| PLiSAGE | L2 | Solo publica el pre-entrenamiento de la proteína; para afinidad hay que reentrenar |
| TransScore | L2 | El repo no tiene código ni modelo |
| GITK | L2 | No hay modelo entrenado |
| SST | L2 | Modelo solo de ligando para receptores de SARS-CoV-2; no aplica a CASF-2016 |
| CGraphDTA | L1 | Necesita bases BLAST/UniRef90 y HH-suite/Uniclust30 (cientos de GB) |
| P3-Score | L1 | Necesita X-Score (licencia/registro) |
| HydraScreen | L1 | Inferencia local depende de paquetes privados; solo queda la API con registro |
| CPIScore, DeepTGIN | L1 y L2 | Modelo incompleto / no publicado |
