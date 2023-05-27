# Plugin QGIS - PhyFire Generator

Autor: David Cifuentes 

El plugin “qgis_phyfire_wk_generator” permite generar los datos de entrada y ficheros de configuración y parametrización necesaria para el motor de simulación PhyFire. El plugin facilitar la laboriosa tarea de preparación de datos de entrada requeridos por el modelo de simulación, tales como capas, ficheros de configuración y datos asociados al área de interés definidos por el usuario. Este genera las capas de entrada a partir de un conjunto de fuentes de datos (DEM, Fuel,…) . Estas fuentes de datos están ubicada en la carpeta del plugin “qgis_phyfire_wk_generator/examples/data/source” y cuenta con datos de ejemplo* del Modelo Digital del Terreno, Modelo de Combustible, Cortafuegos, etc.  En caso de que  plugin no dispone de la fuentes de datos, es capaz de generar la estructura del workspace, ficheros de configuración, parametrización y capas vectoriales definidas, a excepción de los productos raster (tipo de fuel, pendiente del terreno, temperatura..) que requieran fuentes de datos.

*Importante:*

El plugin no ejecuta el modelo de simulación PhyFire, se encarga de preparar la información. Este modelo no está incluido por motivos de autoría

## Instalación en QGIS

1. Descomprimir el paquete en la carpeta de plugins de QGIS

```sh
unzip qgis_phyfire_wk_generator-main.zip
```

2.	Activar el plugin desde QGIS > Plugins > Manage and Install plugins.. PhyFire Generator

3. Abrir el plugin. Desde la barra de herramientas de QGIS hacer clic en "PhyFire Generator"


## Fuente de datos de ejemplo:


Estructura de carpetas fuente:

- sources:
    - DEM:
        - MDE_Spain.tif
    - fireBreaksDB:
	    - fireBreaks.sqlite
    - fuelTypeDB:
        - fuelTypes.sqlite
    - temperatureDB
        - temperatura_spain.tif

Datos de ejemplo:

- Ruta de instalación del plugin: examples/files:

    - CEBREROS_20220715
    - SAN_JUAN_DE_LA_NAVA_20220724

Descargar el zip de datos y sustituir en la carpeta donde se aloja el plugin. Puede consultarlo en QGIS > Settings > User profile > Open Active Profile folder. Navegar a python/plugis y buscar "qgis_phyfire_wk_generator". Sustituir examples/data/source por los ficheros del zip.

## MODELO DE SIMULACIÓN (PhyFire)

El modelo de propagación de incendios PhyFire es un modelo simplificado de propagación de incendios forestales en 2D con algunos efectos en 3D. Se basa en los principios de conservación de la energía y la masa (Asensio et al., 2002). El modelo considera la energía perdida en la dirección vertical debido a la convección natural y los dos mecanismos principales de transferencia de calor en un incendio forestal, la radiación y la convección. La radiación de las llamas por encima de la superficie considera el efecto del viento y la pendiente sobre la inclinación de las llamas. Es un modelo monofásico: solo se considera la fase sólida, la fase gaseosa se parametriza a través de la temperatura de la llama y la altura de la llama en el término de radiación (Ferragut et al., 2007, 2014, Asensio et al., 2020). El término convectivo es crítico ya que el viento es uno de los factores más influyentes en la propagación de un incendio. La pendiente de la superficie también se tiene en cuenta en el término convectivo de la ecuación de conservación de la energía. El contenido de humedad del combustible se considera utilizando una idea novedosa, un operador multivaluado de entalpía. El modelo incluye algunos fenómenos aleatorios como las manchas de fuego ( Asensio et al., 2021). El modelo puede adaptarse a diferentes clasificaciones de combustibles y escenarios. Si se dispone de información actualizada sobre la evolución de un incendio real, estos datos pueden ser asimilados por el modelo para mejorar los resultados de las simulaciones (Ferragut et al., 2015). El modelo también está preparado para actualizar los datos meteorológicos y cartográficos de entrada durante el proceso de simulación, por ejemplo, el uso de cortafuegos se puede incluir en la simulación mediante la modificación de los datos de distribución del combustible. Esto permite estudiar el efecto de las labores de prevención en posibles eventos de incendio

Los datos de entrada del modelo PhyFire incluyen todos los datos de comportamiento del fuego: topografía (pendientes y aspecto), combustible (tipo, distribución y humedad del combustible) y meteorología (viento, temperatura y humedad relativa). El modelo PhyFire puede adaptarse a diferentes niveles de resolución mediante técnicas de interpolación de datos, al igual que los otros dos modelos de simulación. El modelo PhyFire también puede adaptarse a diferentes clasificaciones de combustible como el sistema del Northern Forest Fire Laboratory (NFFL) (Anderson, 1982), el Fire Behaviour Fuel Models (FBFM) (Scott y Burgan, 2005), o el sistema mediterráneo-europeo Prometheus (Comisión Europea, 1999).El siguiente esquema proporciona una visión general de los datos de entrada necesarios, y mapa inicial sugerido con la resolución correspondiente y la tecnología que puede proporcionar la información correspondiente.

Más información en:


| Recurso    | URL |
| -------- | ------- |
| Web | [SINUMCC USAL](https://sinumcc.usal.es/)|
| Github | [GITHUB SINUMCC (privado)](https://github.com/sinumcc/Neptuno_gdal.git)|

## RESPONSABILIDAD

El plugin de QGIS se ha desarrollado dentro de la asignatura PROGRAMACIÓN OPEN SOURCE EN GEOMÁTICA y tiene un carácter formativo, está limitado en funcionalidad y podría presentar incompatibilidades en ciertos sistemas operativos y/o configuraciones. La finalidad el plugin ha sido poner el valor los conocimientos aprendidos para la generación de interfaz gráfica basada en PyQt, el uso de librerías geomáticas Open Source (como GDAL, el API de QGIS, etc) y el desarrollo de plugins en QGIS en lenguaje Python ayudado por Plugin Builder 3 y Plugin Reloader.



## Desarrollo

- ENTORNO DE DESARROLLO: macOS Monterey + VSCode + QGIS Designer + Plugin Builder

- RUTA BIN DE QGIS: ```/Applications/QGIS.app/Contents/MacOS/bin/pb_tool compile```

- ABRIR QT5 BUILDER ```/Applications/QGIS.app/Contents/MacOS/Designer.app/Contents/MacOS/Designer```

- PLUGINS QGIS - RUTA POR DEFECTO: ```/Users/<USERNAME>/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins```

- COMPILAR: 

```sh
cd /Users/<USERNAME>/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/qgis_phyfire_wk_generator && /Applications/QGIS.app/Contents/MacOS/bin/pb_tool compile
```

