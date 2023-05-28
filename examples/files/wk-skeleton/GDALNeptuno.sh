#!/bin/bash

VERSION=1.0.2
echo "-------------------------------------------------------------------------"
echo " GDALNeptuno v.$VERSION Preprocessing GIS files ...."
echo "-------------------------------------------------------------------------"
data=$(cat $1)
errorQ=false
ortoQ=true
tempQ=true
fireBreakQ=true
fuelTypeQ=true
ascQ=false

#Inputs
## DEM
isQ=$(jq '.gisInfo | has("DEM")' $1)
if [ "$isQ" = "true" ]; then
  DEM=$(echo $data | jq -r '.gisInfo.DEM')
  if [ -z "$DEM" ]; then
    echo "  - ERROR: DEM not provided."
    errorQ=true
  fi
else
  echo "  - ERROR: Label DEM is not avaliable at configFile."
  errorQ=true
fi
## fireBreak
isQ=$(jq '.gisInfo | has("fireBreaksDB")' $1)
if [ "$isQ" = "true" ]; then
  fireBreaksDB=$(echo $data | jq -r '.gisInfo.fireBreaksDB')
  if [ -z "$fireBreaksDB" ]; then
    echo "  - WARNING: fireBreaks db not provided. This info is REQUIRED by phyFire"
    fireBreakQ=false
  fi
else
  echo "  - WARNING: Label fireBreaksDB is not avaliable at configFile. This info is REQUIRED by phyFire"
  fireBreakQ=false
fi
## fuelTypeDB
isQ=$(jq '.gisInfo | has("fuelTypeDB")' $1)
if [ "$isQ" = "true" ]; then
  fuelTypeDB=$(echo $data | jq -r '.gisInfo.fuelTypeDB')
  if [ -z "$fuelTypeDB" ]; then
    echo "  - ERROR: fuelType db not provided."
    errorQ=true
  fi
else
  echo "  - WARNING: fuelTypeDB not provided. This info is REQUIRED phyFire and hdWind"
  fuelTypeQ=false
fi
## temperatureDB
isQ=$(jq '.gisInfo | has("temperatureDB")' $1)
if [ "$isQ" = "true" ]; then
  temperatureDB=$(echo $data | jq -r '.gisInfo.temperatureDB')
  if [ -z "$temperatureDB" ]; then
    echo "  - WARNING: temperaute raster not provided. Using constant raster."
    tempQ=false
  fi
else
  echo "  - WARNING: temperaute raster not provided. Using constant raster."
  tempQ=false
fi
## ortophoto
isQ=$(jq '.gisInfo | has("ortophotoWMS")' $1)
if [ "$isQ" = "true" ]; then
  ortophotoWMS=$(echo $data | jq -r '.gisInfo.ortophotoWMS')
  if [ -z "$ortophotoWMS" ]; then
    echo "  - WARNING: ortophoto WMS not provided. Video output disabled."
    ortoQ=false
  fi
else
  echo "  - WARNING: Label ortophotoWMS is not avaliable at configFile. Video output disabled."
  ortoQ=false
fi
## srs
isQ=$(jq '.gisInfo | has("srs")' $1)
if [ "$isQ" = "true" ]; then
  srs=$(echo $data | jq -r '.gisInfo.srs')
  if [ -z "$srs" ]; then
    echo " - ERROR: srs not provided."
    errorQ=true
  fi
else
  echo "  - ERROR: Label srs is not avaliable at configFile."
  errorQ=true
fi
## cellsize
isQ=$(jq '.gisInfo | has("cellSizeGIS")' $1)
if [ "$isQ" = "true" ]; then
  cellSize=$(echo $data | jq -r '.gisInfo.cellSizeGIS')
  if [ -z "$cellSize" ]; then
    echo "  - WARNING: cellSizeGIS not provided. Using devalut value (5)."
  fi
else
  echo "  - WARNING: Label cellSizeGIS is not avaliable at configFile. Using devalut value (5)."
fi
## boundingBox
isQ=$(jq '.gisInfo | has("boundingBox")' $1)
if [ "$isQ" = "true" ]; then
  xmin=$(echo $data | jq -r '.gisInfo.boundingBox[0]')
  ymin=$(echo $data | jq -r '.gisInfo.boundingBox[1]')
  xmax=$(echo $data | jq -r '.gisInfo.boundingBox[2]')
  ymax=$(echo $data | jq -r '.gisInfo.boundingBox[3]')
  if [ -z "$xmin" -o -z "$ymin" -o -z "$xmax" -o -z "$ymax" ]; then
      echo "ERROR: bounding box is not defined."
      errorQ=true
  fi
  isQ=$(jq '.gisInfo | has("srs_bbox")' $1)
  if [ "$isQ" = "true" ]; then
    srsBB=$(echo $data | jq -r '.gisInfo.srs_bbox')
    if [ ! "$srs" = "$srsBB" ]; then
      echo
      echo " Projecting bbox coordinates " $srsBB "---->" $srs
      echo " Bbox ($srsBB): [$xmin $ymin $xmax $ymax]"
      newCoord=$(echo "$xmin $ymin" | gdaltransform -s_srs $srsBB -t_srs $srs)
      IFS=' ' read -r xmin ymin temp <<< "$newCoord"
      newCoord=$(echo "$xmax $ymax" | gdaltransform -s_srs $srsBB -t_srs $srs)
      IFS=' ' read -r xmax ymax temp <<< "$newCoord"
      echo " Bbox ($srs): [$xmin $ymin $xmax $ymax]"
    fi
  fi
else
  echo "  - ERROR: Label BoundingBox is not avaliable at configFile."
  errorQ=true
fi
## nodata
nodata=-9999
## Control errors
if [ "$errorQ" = "true" ]; then
  echo " There are some config errors. Aborting GDAL-GIS operations."
  exit 1
fi

#Outputs
## theWorkspace
isQ=$(jq '.paths | has("theWorkspace")' $1)
if [ "$isQ" = "true" ]; then
  theWorkspace=$(echo $data | jq -r '.paths.theWorkspace')
  if [ -z "$theWorkspace" ]; then
    theWorkspace=$(basename "$PWD")
  fi
  echo " Workspace " $theWorkspace
else
  theWorkspace=$(basename "$PWD")
  echo " Workspace: " $theWorkspace
fi
## theDataPath
isQ=$(jq '.paths | has("theDataPath")' $1)
if [ "$isQ" = "true" ]; then
  thePath=$(echo $data | jq -r '.paths.theDataPath')
  if [ -z "$thePath" ]; then
    echo "  - WARNING: theDataPath not provided. Using default value ./"
  fi
  if [[ -n $thePath ]] && [[ "${thePath: -1}" != "/" ]]; then
  thePath=$(printf "%s/" "$thePath")
  fi
else
  echo "  - WARNING: Label theDataPath is not avaliable at configFile. Using default value ./"
fi
##orographyFilename
isQ=$(jq '.gisInfo | has("orographyFilename")' $1)
orographyF=$(echo $data | jq -r '.gisInfo.orographyFilename')
if [ "$isQ" = "false" -o -z "$orographyF" ]; then
    orographyF="height.tif"
fi
ext="${orographyF##*.}"
extN=$ext
if [ "$ext" = "asc" ]; then
    fname="${orographyF%.*}"
    orographyFasc="$thePath${fname}.asc"
    orographyF="${fname}.tif"
    ascQ=true;
fi
orographyF="$thePath$orographyF"

##tempFilename
if [ "$tempQ" = "true" ]; then
  isQ=$(jq '.gisInfo | has("temperatureFilename")' $1)
  temperatureF=$(echo $data | jq -r '.gisInfo.temperatureFilename')
  if [ "$isQ" = "false" -o -z "$temperatureF" ]; then
      temperatureF="hdwf_temperature.tif"
  fi
  extN="${temperatureF##*.}"
  if [ ! "$extN" = "$est" ]; then
      errorQ="true"
  fi
  if [ "$ext" = "asc" ]; then
      fname="${temperauteF%.*}"
      temperatureFasc="$thePath${fname}.asc"
      temperatureF="${fname}.tif"
  fi
  temperatureF="$thePath$temperatureF"
fi
##areaTypeFilename
if [ "$fuelTypeQ" = "true" ]; then
  isQ=$(jq '.gisInfo | has("areaTypeFilename")' $1)
  areaTypeF=$(echo $data | jq -r '.gisInfo.areaTypeFilename')
  if [ "$isQ" = "false" -o -z "$areaTypeF" ]; then
    areaTypeF="area_type.tif"
  fi
  ext="${areaTypeF##*.}"
  if [ ! "$extN" = "$ext" ]; then
    errorQ="true"
  fi
  if [ "$ext" = "asc" ]; then
    fname="${areaTypeF%.*}"
    areaTypeFasc="$thePath${fname}.asc"
    areaTypeF="${fname}.tif"
  fi
  areaTypeF="$thePath$areaTypeF"
fi
##fueltypeFilename
if [ "$fuelTypeQ" = "true" ]; then
  isQ=$(jq '.gisInfo | has("fuelFilename")' $1)
  fuelTypeF=$(echo $data | jq -r '.gisInfo.fuelFilename')
  if [ "$isQ" = "false" -o -z "$fuelTypeF" ]; then
    fuelTypeF="fuel.$extN"
  fi
  ext="${fuelTypeF##*.}"
  if [ ! "$extN" = "$ext" ]; then
    errorQ="true"
  fi
  if [ "$ext" = "asc" ]; then
    fname="${fuelTypeF%.*}"
    fuelTypeFasc="$thePath${fname}.asc"
    fuelTypeF="${fname}.tif"
  fi
  fuelTypeF="$thePath$fuelTypeF"
fi
##fcc
if [ "$fireBreakQ" = "true" ]; then
  isQ=$(jq '.gisInfo | has("fccFilename")' $1)
  fccF=$(echo $data | jq -r '.gisInfo.fccFilename')
  if [ "$isQ" = "false" -o -z "$fccF" ]; then
    fccF="fcc.tif"
  fi
  ext="${fccF##*.}"
  if [ ! "$extN" = "$ext" ]; then
    errorQ="true"
  fi
  if [ "$ext" = "asc" ]; then
    fname="${fccF%.*}"
    fccFasc="$thePath${fname}.asc"
    fccF="${fname}.tif"
  fi
  fccF="$thePath$fccF"
fi

##ortophoto
if [ "$ortoQ" = "true" ]; then
  isQ=$(jq '.phyFire.videoConfig | has("baseMap")' $1)
  ortoF=$(echo $data | jq -r '.phyFire.videoConfig.baseMap')
  if [ "$isQ" = "false" -o -z "$ortoF" ]; then
      ortoF="baseMap.png"
  fi
  ortoF="$thePath$ortoF"
fi

##ERROR: asc - tif format
if [ "$errorQ" = "true" ]; then
  echo "  - ERROR: The format of output files are not compatible."
  exit 1
fi

echo ""
echo " GDAL processing ...."
echo ""

# DEM
if [ -f "$orographyF" ]; then
  rm $orographyF
fi
echo "  Orography ----> " $orographyF
gdalwarp -of "GTiff" -tr $cellSize -$cellSize -dstnodata $nodata \
         -te $xmin $ymin $xmax $ymax -t_srs $srs -ot "Int16" \
         "$DEM" "$orographyF" > neptunoGDAL.log
if [ "$ascQ" = "true" ]; then
  if [ -f "$orographyFasc" ]; then
    rm $orographyFasc
  fi
  echo "            ----> " $orographyFasc
  gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot "Int16" \
    "$orographyF" "$orographyFasc" > neptunoGDAL.log

fi

#fuelType
if [ "$fuelTypeQ" = "true" ]; then
  echo "  fuel type ----> " $fuelTypeF
  layername="fueltypes"
  fuel_c_db="${fuelTypeF%.*}"".sqlite"
  if [ -f "$fuel_c_db" ]; then
    rm $fuel_c_db
  fi
  ogr2ogr --config OGR_SQLITE_CACHE 1024  -spat $xmin $ymin $xmax $ymax \
        -spat_srs $srs -clipdst  $xmin $ymin $xmax $ymax  \
        -t_srs $srs  \
        "$fuel_c_db" "$fuelTypeDB" \
        -nln $layername \
        -nlt PROMOTE_TO_MULTI -gt unlimited \
        --config OGR_ORGANIZE_POLYGONS CCW_INNER_JUST_AFTER_CW_OUTER
        >> neptunoGDAL.log
  if [ -f "$fuelTypeF" ]; then
    rm $fuelTypeF
  fi
  gdal_rasterize  -a "Fuel" -l $layername -of "GTiff" -a_srs $srs -a_nodata $nodata \
        -te  $xmin $ymin $xmax $ymax -tr $cellSize $cellSize \
        -ot "Int16" \
        "$fuel_c_db" "$fuelTypeF" > neptunoGDAL.log
  if [ "$ascQ" = "true" ]; then
    if [ -f "$fuelTypeFasc" ]; then
     rm $fuelTypeFasc
    fi
  echo "            ----> " $fuelTypeFasc
  gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot "Int16" \
      "$fuelTypeF" "$fuelTypeFasc" > neptunoGDAL.log
  fi
fi
#areaTypeF
if [ "$fuelTypeQ" = "true" ]; then
  echo "  area type ----> " $areaTypeF
  if [ -f "$areaTypeF" ]; then
    rm $areaTypeF
  fi
  cp $fuelTypeF $areaTypeF
  if [ "$ascQ" = "true" ]; then
    if [ -f "$areaTypeFasc" ]; then
     rm $areaTypeFasc
    fi
    echo "            ----> " $areaTypeFasc
    cp $fuelTypeFasc $areaTypeFasc
  fi
fi
#fcc
if [ "$fireBreakQ" = "true" ]; then
  echo "  fcc       ----> " $fccF
  if [ -f "$fcc_c_db" ]; then
    rm $fcc_c_db
  fi
  layername="fireBreaks"
  fcc_c_db="${fccF%.*}"".sqlite"
  if [ -f "$fcc_c_db" ]; then
    rm $fcc_c_db
  fi
  ogr2ogr --config OGR_SQLITE_CACHE 1024  -spat $xmin $ymin $xmax $ymax \
        -spat_srs $srs -clipdst  $xmin $ymin $xmax $ymax  \
        -t_srs $srs "$fcc_c_db" "$fireBreaksDB" -nln $layername -nlt PROMOTE_TO_MULTI \
        -gt unlimited \
        --config OGR_ORGANIZE_POLYGONS CCW_INNER_JUST_AFTER_CW_OUTER
  if [ -f "$fccF" ]; then
    rm $fccF
  fi
  gdal_rasterize  -i -a "fid" -l $layername -of "GTiff" -a_srs $srs -a_nodata $nodata \
                -te  $xmin $ymin $xmax $ymax -tr $cellSize $cellSize \
                -ot "Byte" \
                "$fcc_c_db" "$fccF" > neptunoGDAL.log
  if [ "$ascQ" = "true" ]; then
    if [ -f "$fccFasc" ]; then
       rm $fccFasc
    fi
    echo "            ----> " $fccFasc
    gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot "Int16" \
         "$fccF" "$fccFasc" > neptunoGDAL.log
    fi
  fi
#temperatureDB
if [ "$tempQ" = "true" ]; then
  if [ -f "$temperatureF" ]; then
    rm $temperatureF
  fi
  echo "  temperat. ----> " $temperatureF
  gdalwarp -of "GTiff" -tr $cellSize -$cellSize -dstnodata $nodata \
        -te $xmin $ymin $xmax $ymax -t_srs $srs -ot "Float32" \
         "$temperatureDB" "$temperatureF" >> neptunoGDAL.log
  if [ "$ascQ" = "true" ]; then
    if [ -f "$temperatureFasc" ]; then
      rm $temperatureFasc
    fi
    echo "            ----> " $temperatureFasc
    gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot "Int16" \
             $temperatureF $temperatureFasc > neptunoGDAL.log
  fi
fi
#sourceMap
if [ "$ascQ" = "true" ]; then
  isQ=$(jq '.gisInfo | has("sourceMap")' $1)
  if [ "$isQ" = "true" ]; then
    sourceMap=$(echo $data | jq -r '.gisInfo.sourceMap')
    if [ -z "$sourceMap" ]; then
      echo "  - WARNING: SourceMap not provided."
    else
      isQ=$(jq '.gisInfo | has("sourceFilename")' $1)
      sourceFasc=$(echo $data | jq -r '.gisInfo.sourceFilename')
      if [ "$isQ" = "false" -o -z "$sourceFasc" ]; then
          sourceFasc="source.asc"
      fi
      sourceFasc="$thePath$sourceFasc"
      echo "  source    ----> " $sourceFasc
      if [ -f "$sourceFasc" ]; then
        rm $sourceFasc
      fi
      tempDir="_____temporalFiles"
      mkdir $tempDir
      focusLocal="$tempDir""/fL.geojson"
      focusShape="$tempDir""/fS.shp"
      focusTif="$tempDir""/fT.tif"
      radius=$cellSize*3
      ogr2ogr $focusLocal $sourceMap -t_srs $srs  > neptunoGDAL.log
      ogr2ogr -f "ESRI Shapefile" $focusShape  $focusLocal  \
              -dialect sqlite \
              -sql "select ST_buffer(geometry, $radius) as geometry, '1' as zone FROM focus" \
              -clipdst $xmin $ymin $xmax $ymax \
              -t_srs $srs  > neptunoGDAL.log
     gdal_rasterize -a "zone" -of "GTiff" -a_srs $srs -a_nodata -9999 \
              -te $xmin $ymin $xmax $ymax  \
              -tr $cellSize $cellSize -ot Byte $focusShape $focusTif \
              > neptunoGDAL.log
     gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot Int32  \
              $focusTif $sourceFasc  > neptunoGDAL.log
     rm -R $tempDir
    fi
  else
    echo "  - WARNING: Label SourceMap is not avaliable at configFile."
  fi
fi

#ortophotoWMS
if [ "$ortoQ" = "true" ]; then
  if [ -f "$ortoF" ]; then
    rm $ortoF
  fi
  #Compute resolution with gdalinfo
  dimP=$(gdalinfo $orographyF | grep "Size is")
  reslX=$(echo $dimP | cut -d " " -f 3)
  reslX="${reslX%?}"
  let reslX="reslX * 2"
  reslY=$(echo $dimP | cut -d " " -f 4)
  let reslY="reslY * 2"
  echo "  ortophoto ----> " $ortoF
  aspersan="&"

  urlWMS="${ortophotoWMS}BBOX=${xmin},${ymin},${xmax},${ymax}${aspersan}SRS=${srs}${aspersan}FORMAT=image/png${aspersan}WIDTH=${reslX}${aspersan}HEIGHT=${reslY}"
  #command="gdal_translate -of PNG -outsize $reslX $reslY -projwin  $xmin $ymax $xmax $ymin -projwin_srs $srs -a_srs $srs $urlWMS $ortoF"
  #echo "command: " $command
  echo "  WMS orto  ----> " $urlWMS
  gdal_translate -of PNG -outsize $reslX $reslY -projwin  $xmin $ymax $xmax $ymin   \
                  -projwin_srs $srs -a_srs $srs  \
                  $urlWMS "$ortoF" > neptunoGDAL.log
fi
echo "-------------------------------------------------------------------------"
echo""
