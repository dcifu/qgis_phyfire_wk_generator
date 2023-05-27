# -*- coding: utf-8 -*-
import json
import os
import sys
import shutil 
import logging
from osgeo.osr import SpatialReference, CoordinateTransformation
import subprocess
from qgis.core import QgsApplication

#from subprocess import Popen, PIPE


QGISprefixPathBin =  os.path.join(QgsApplication.prefixPath(),'bin/')


def _logMsg(log, msg, showOutput):
    log += msg+"\n"
    if showOutput: print(msg)
    return log

def runGDALNeptuno(pathfile, showOutput=False):
    
    errorQ=False
    ortoQ=True
    tempQ=True
    fireBreakQ=True
    fuelTypeQ=True
    ascQ=False
    ## nodata
    nodata=-9999
    
    logOut = ""
    
    # Devolvemos un objeto con el log y si hay error
    o = dict();
    o['msg'] = logOut
    o['error']   = False
    
    with open(pathfile) as config_file:
        config_file_contents = config_file.read()

    data = json.loads(config_file_contents)
    
    path_workspace = os.path.dirname(pathfile)
    path_LogNeptunoGDAL = os.path.join(path_workspace, 'Logs', 'neptunoGDAL.log')
    
    #Inputs
    ## DEM
    if data.get('gisInfo')["DEM"]:
        DEM=data.get('gisInfo')["DEM"]
        if not DEM:
            logOut = _logMsg(logOut,'  - ERROR: DEM not provided.',showOutput)
            errorQ=True
    else:
        logOut = _logMsg(logOut,'  - ERROR: Label DEM is not avaliable at configFile.',showOutput)
        errorQ=True
    
    ## fireBreak
    if data.get('gisInfo')["fireBreaksDB"]:
        fireBreaksDB=data.get('gisInfo')["fireBreaksDB"]
        if not fireBreaksDB:
            logOut = _logMsg(logOut,"  - WARNING: fireBreaks db not provided. This info is REQUIRED by phyFire",showOutput)
            fireBreakQ=False
    else:
        logOut = _logMsg(logOut,"  - WARNING: Label fireBreaksDB is not avaliable at configFile. This info is REQUIRED by phyFire",showOutput)
        fireBreakQ=False

    ## fuelTypeDB
    if data.get('gisInfo')["fuelTypeDB"]:
        fuelTypeDB=data.get('gisInfo')["fuelTypeDB"]
        if not fuelTypeDB:
            logOut = _logMsg(logOut," - ERROR: fuelType db not provided.",showOutput)
            errorQ=True
    else:
        logOut = _logMsg(logOut,"  - WARNING: fuelTypeDB not provided. This info is REQUIRED phyFire and hdWind",showOutput)
        fuelTypeQ=False

    ## temperatureDB
    if data.get('gisInfo')["temperatureDB"]:
        temperatureDB=data.get('gisInfo')["temperatureDB"]
        if not temperatureDB:
            logOut = _logMsg(logOut," - WARNING: temperaute raster not provided. Using constant raster.",showOutput)
            tempQ=False
    else:
        logOut = _logMsg(logOut,"  - WARNING: temperaute raster not provided. Using constant raster.",showOutput)
        tempQ=False


    ## ortophoto
    if data.get('gisInfo')["ortophotoWMS"]:
        ortophotoWMS=data.get('gisInfo')["ortophotoWMS"]
        if not ortophotoWMS:
            logOut = _logMsg(logOut," - WARNING: ortophoto WMS not provided. Video output disabled.",showOutput)
            ortoQ=False
    else:
        logOut = _logMsg(logOut,"  - WARNING: Label ortophotoWMS is not avaliable at configFile. Video output disabled.",showOutput)
        ortoQ=False


    ## srs
    if data.get('gisInfo')["srs"]:
        srs=data.get('gisInfo')["srs"]
        if not srs:
            logOut = _logMsg(logOut," - ERROR: srs not provided.",showOutput)
            errorQ=False
    else:
        logOut = _logMsg(logOut,"  - ERROR: Label srs is not avaliable at configFile.",showOutput)
        errorQ=False

    ## cellsize
    if data.get('gisInfo')["cellSizeGIS"]:
        cellSize=data.get('gisInfo')["cellSizeGIS"]
        if not cellSize:
            logOut = _logMsg(logOut," - WARNING: cellSizeGIS not provided. Using devalut value (5).",showOutput)
    else:
        logOut = _logMsg(logOut,"  - WARNING: Label cellSizeGIS is not avaliable at configFile. Using devalut value (5).",showOutput)

    ## boundingBox
    if data.get('gisInfo')["boundingBox"]:
        xmin=data.get('gisInfo').get('boundingBox')[0]
        ymin=data.get('gisInfo').get('boundingBox')[1]
        xmax=data.get('gisInfo').get('boundingBox')[2]
        ymax=data.get('gisInfo').get('boundingBox')[3]
        
        if (xmin, ymin, xmax, ymax ) is None:
            logOut = _logMsg(logOut,"ERROR: bounding box is not defined.",showOutput)
            errorQ=True
        if data.get('gisInfo')["srs_bbox"]:
            srsBB=data.get('gisInfo')["srs_bbox"]
            if srsBB:
                logOut = _logMsg(logOut," Projecting bbox coordinates " + srsBB + "---->" + srs,showOutput)
                
                projSource = int(srsBB[5:])
                source = SpatialReference()
                source.ImportFromEPSG(projSource)
                
                projTarget = int(srs[5:])
                target = SpatialReference()
                target.ImportFromEPSG(projTarget)
                
                transform_epsg = CoordinateTransformation(source, target)
                
                cmin =transform_epsg.TransformPoint(xmin, ymin)
                cmax =transform_epsg.TransformPoint(xmax, ymax)
                
                #cmdtransfmin = f'echo "{xmin} {ymin}" | gdaltransform -s_srs {srsBB} -t_srs {srs}'
                #strcoordmin = subprocess.call([cmdtransfmin], shell=False)
                #cmin = strcoordmin.split()
                
                #cmdtransfmax = f'echo "{xmax} {ymax}" | gdaltransform -s_srs {srsBB} -t_srs {srs}'
                #strcoordmax = subprocess.check_output(cmdtransfmax, shell=True)
                #cmax = strcoordmax.split()
                
                xmin = float(cmin[0])
                ymin = float(cmin[1])
                xmax = float(cmax[0])
                ymax = float(cmax[1])
                logOut = _logMsg(logOut," Bbox ( "+ srs + "): [ " + str(xmin) + " " + str(ymin) + " " + str(xmax) + " " + str(ymax) +"]",showOutput)
   
    else:
        logOut = _logMsg(logOut,"  - ERROR: Label BoundingBox is not avaliable at configFile.",showOutput)
        errorQ=True       
  
    ## Control errors
    if errorQ:
        logOut = _logMsg(logOut," - ERROR: There are some config errors. Aborting GDAL-GIS operations.",showOutput)
        o["msg"] = logOut
        o["error"] = errorQ
        return o
        #sys.exit(-1);
  
    #Outputs
    ## theWorkspace

    if data.get('paths')["theWorkspace"]:
        theWorkspace=data.get('paths')["theWorkspace"]
        if not theWorkspace:
            theWorkspace=os.path.basename(pathfile)
        logOut = _logMsg(logOut,"Workspace: "  + theWorkspace,showOutput)
    else:
        logOut = _logMsg(logOut,"  - WARNING: Workspace is calculated",showOutput)
        theWorkspace=os.path.basename(pathfile)

    if data.get('paths')["theDataPath"]:
        thePath=data.get('paths')["theDataPath"]
        if not thePath:
            logOut = _logMsg(logOut,"  - WARNING: theDataPath not provided. Using default value ./Data",showOutput)
            thePath="./Data/"
    else:
        logOut = _logMsg(logOut,"  - WARNING: Label theDataPath is not avaliable at configFile. Using default value ./",showOutput)
        thePath="./Data/"  


    ##orographyFilename
    if data.get('gisInfo')["orographyFilename"]:
        orographyF=data.get('gisInfo')["orographyFilename"]
        if not orographyF:
            orographyF="height.tif"
            
        file_name, file_extension = os.path.splitext(orographyF)
        if file_extension == "asc":
            orographyF= file_name + ".tif"
            orographyFasc=os.path.join(thePath,file_name + ".asc")
            ascQ=True
        orographyF=os.path.join(thePath,orographyF)
    
    ##tempFilename
    if tempQ:
        if data.get('gisInfo')["temperatureFilename"]:
            temperatureF=data.get('gisInfo')["temperatureFilename"]
        else:
            temperatureF="hdwf_temperature.tif"
        file_name, file_extension = os.path.splitext(temperatureF)
        if file_extension == "asc":
            temperatureF= file_name + ".tif"
            temperatureFasc=os.path.join(thePath, file_name + ".asc")
        temperatureF=os.path.join(thePath, temperatureF)
        
    ##areaTypeFilename
    if fuelTypeQ:
        if data.get('gisInfo')["areaTypeFilename"]:
            areaTypeF=data.get('gisInfo')["areaTypeFilename"]
        else:
            areaTypeF="area_type.tif"
        
        file_name, file_extension = os.path.splitext(areaTypeF)
        if file_extension == "asc":
            areaTypeF= file_name + ".tif"
            areaTypeFasc=os.path.join(thePath, file_name + ".asc")
        areaTypeF=os.path.join(thePath, areaTypeF)
  
    ##fueltypeFilename
    if fuelTypeQ:
        if data.get('gisInfo')["fuelFilename"]:
            fuelTypeF=data.get('gisInfo')["fuelFilename"]
        else:
            fuelTypeF="fuel.tif"
        
        file_name, file_extension = os.path.splitext(fuelTypeF)
        if file_extension == "asc":
            fuelTypeF= file_name + ".tif"
            fuelTypeFasc=os.path.join(thePath, file_name + ".asc")
        fuelTypeF=os.path.join(thePath, fuelTypeF)

    ##fcc
    if fireBreakQ:
        if data.get('gisInfo')["fccFilename"]:
            fccF=data.get('gisInfo')["fccFilename"]
        else:
            fccF="fcc.tif"
        
        file_name, file_extension = os.path.splitext(fccF)
        if file_extension == "asc":
            fccF= file_name + ".tif"
            fccFasc=os.path.join(thePath, file_name + ".asc")
        fccF=os.path.join(thePath, fccF)

    ##ortophoto
    if ortoQ:
        if data.get('phyFire').get("videoConfig")["baseMap"]:
            ortoF=data.get('phyFire').get("videoConfig")["baseMap"]
        else:
            ortoF="baseMap.png"
        ortoF=os.path.join(thePath, ortoF)

    ##ERROR: asc - tif format
    if errorQ:
        logOut = _logMsg(logOut,"  - ERROR: The format of output files are not compatible.",showOutput)
        o["msg"] = logOut
        o["error"] = errorQ
        return o
        #sys.exit(-1)


    logOut = _logMsg(logOut,"",showOutput)
    logOut = _logMsg(logOut," GDAL processing ....",showOutput)
    logOut = _logMsg(logOut,"",showOutput)

    # DEM
    orographyFAbs = os.path.join(path_workspace, orographyF[2:])
    if os.path.isfile(orographyFAbs):
        os.remove(orographyFAbs)

    logOut = _logMsg(logOut,"  Orography ----> " + orographyF,showOutput)
    
    cmdgdal = f'gdalwarp -of "GTiff" -tr {cellSize} -{cellSize} -dstnodata {nodata} \
            -te {xmin} {ymin} {xmax} {ymax} -t_srs {srs} -ot "Int16" "{DEM}" "{orographyFAbs}" >> "{path_LogNeptunoGDAL}"'

    qgiscmd = QGISprefixPathBin + cmdgdal
    os.system(qgiscmd)

    if ascQ:
        if os.path.isfile(orographyFasc):
            os.remove(orographyFasc)
        
        logOut = _logMsg(logOut,"            ----> " + orographyFasc,showOutput)
        
        cmdgdal = f'gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot "Int16" \
        "{orographyFAbs}" "{orographyFasc}" >> "{path_LogNeptunoGDAL}"'
        qgiscmd = QGISprefixPathBin + cmdgdal
        os.system(qgiscmd)
    

    #fuelType
    if fuelTypeQ:
        logOut = _logMsg(logOut,"  fuel type ----> " +fuelTypeF,showOutput)
        layername="fueltypes"
        pre, ext = os.path.splitext(fuelTypeF)
        fuel_c_db = pre+ '.sqlite'
        fuel_c_dbAbs = os.path.join(path_workspace, fuel_c_db)
        if os.path.isfile(fuel_c_dbAbs):
            os.remove(fuel_c_dbAbs)
        
        cmdogr = f'ogr2ogr --config OGR_SQLITE_CACHE 1024  -spat {xmin} {ymin} {xmax} {ymax} \
            -spat_srs {srs} -clipdst  {xmin} {ymin} {xmax} {ymax} \
            -t_srs {srs}  \
            "{fuel_c_dbAbs}" "{fuelTypeDB}" \
            -nln {layername} \
            -nlt PROMOTE_TO_MULTI -gt unlimited \
            --config OGR_ORGANIZE_POLYGONS CCW_INNER_JUST_AFTER_CW_OUTER  >> "{path_LogNeptunoGDAL}"'
        qgiscmd = QGISprefixPathBin + cmdogr
        os.system(qgiscmd)
        
        if os.path.isfile(fuelTypeF):
            os.remove(fuelTypeF)
    
        fuelTypeFAbs = os.path.join(path_workspace, fuelTypeF[2:])
        cmdrasterize = f'gdal_rasterize  -a "Fuel" -l {layername} -of "GTiff" -a_srs {srs} -a_nodata {nodata} \
            -te  {xmin} {ymin} {xmax} {ymax} -tr {cellSize} {cellSize} \
            -ot "Int16" \
            "{fuel_c_dbAbs}" "{fuelTypeFAbs}" >> "{path_LogNeptunoGDAL}"'
        qgiscmd = QGISprefixPathBin + cmdrasterize
        os.system(qgiscmd)
        
        if ascQ:
            if os.path.isfile(fuelTypeFasc):
                os.remove(fuelTypeFasc)
            logOut = _logMsg(logOut,"            ----> " + fuelTypeFasc,showOutput)
           
            cmdtranslate = f'gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot "Int16" \
            "{fuel_c_dbAbs}" "{fuelTypeFasc}" >> "{path_LogNeptunoGDAL}"'
            qgiscmd = QGISprefixPathBin + cmdtranslate
            os.system(qgiscmd)
            

    #areaTypeF
    if fuelTypeQ:
        logOut = _logMsg(logOut,"  area type ----> " + areaTypeF,showOutput)
        areaTypeFAbs = os.path.join(path_workspace, areaTypeF[2:])
        if os.path.isfile(areaTypeFAbs):
            os.remove(areaTypeFAbs)
        if os.path.isfile(fuelTypeFAbs):
            shutil.copyfile(fuelTypeFAbs, areaTypeFAbs)
        if ascQ:
            if os.path.isfile(areaTypeFasc):
                os.remove(areaTypeFasc)
            logOut = _logMsg(logOut,"            ----> " + areaTypeFasc,showOutput)
            shutil.copyfile(fuelTypeFasc, areaTypeFasc)
  
    #fcc
    if fireBreakQ:
        logOut = _logMsg(logOut,"  fcc       ----> " + fccF,showOutput)
        layername="fireBreaks"
        pre, ext = os.path.splitext(fccF)
        fcc_c_db =  pre + '.sqlite'
        fcc_c_dbAbs = os.path.join(path_workspace, fcc_c_db)
        if os.path.isfile(fcc_c_dbAbs):
            os.remove(fcc_c_dbAbs)
        
        #fcc_c_dbrep = fcc_c_db.replace(' ','\\ ')
        #fireBreaksDBrep = fireBreaksDB.replace(' ','\\ ')
        
        cmdogr = f'ogr2ogr --config OGR_SQLITE_CACHE 1024  -spat {xmin} {ymin} {xmax} {ymax} \
            -spat_srs {srs} -clipdst  {xmin} {ymin} {xmax} {ymax}  \
            -t_srs {srs} "{fcc_c_dbAbs}" "{fireBreaksDB}" -nln {layername} -nlt PROMOTE_TO_MULTI \
            -gt unlimited \
            --config OGR_ORGANIZE_POLYGONS CCW_INNER_JUST_AFTER_CW_OUTER'
        qgiscmd = QGISprefixPathBin + cmdogr
        os.system(qgiscmd)
        
        if os.path.isfile(fccF):
            os.remove(fccF)
        #fccFrep = fccF.replace(' ','\\ ')
        cmdrasterize = f'gdal_rasterize  -i -a "fid" -l {layername} -of "GTiff" -a_srs {srs} -a_nodata {nodata} \
                    -te  {xmin} {ymin} {xmax} {ymax} -tr {cellSize} {cellSize} \
                    -ot "Byte" \
                    "{fcc_c_dbAbs}" "{fccF}"  >> "{path_LogNeptunoGDAL}"'
        qgiscmd = QGISprefixPathBin + cmdrasterize
        os.system(qgiscmd)
        
        if ascQ:
            if os.path.isfile(fccFasc):
                os.remove(fccFasc)

            logOut = _logMsg(logOut,"            ----> " +fccFasc,showOutput)
           
            cmdtranslate = f'gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot "Int16" \
            "{fccF}" {fccFasc}  >> "{path_LogNeptunoGDAL}"'
            qgiscmd = QGISprefixPathBin + cmdtranslate
            os.system(qgiscmd)
  
  
    #temperatureDB
    if tempQ:
        if os.path.isfile(temperatureF):
            os.remove(temperatureF)

        logOut = _logMsg(logOut,"  temperat. ----> " + temperatureF,showOutput)

        cmdwarp = f'gdalwarp -of "GTiff" -tr {cellSize} -{cellSize} -dstnodata {nodata} \
            -te {xmin} {ymin} {xmax} {ymax} -t_srs {srs} -ot "Float32" \
            "{temperatureDB}" "{temperatureF}" >> "{path_LogNeptunoGDAL}"'
        qgiscmd = QGISprefixPathBin + cmdwarp
        os.system(qgiscmd)
        
        if ascQ:
            if os.path.isfile(temperatureFasc):
                os.remove(temperatureFasc)

            logOut = _logMsg(logOut,"            ----> " + temperatureFasc,showOutput)
            #temperatureFascrep = temperatureFasc.replace(' ','\\ ')
            cmdtranslate = f'gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot "Int16" \
                "{temperatureF}" "{temperatureFasc}" >> "{path_LogNeptunoGDAL}"'
            qgiscmd = QGISprefixPathBin + cmdtranslate
            os.system(qgiscmd)

    #sourceMap
    if ascQ:
        if data.get('gisInfo')["sourceMap"]:
            sourceMap=data.get('gisInfo')["sourceMap"]
            if not sourceMap:
                logOut = _logMsg(logOut,"  - WARNING: SourceMap not provided.",showOutput)
            else:
                logOut = _logMsg(logOut,"  - WARNING: SourceMap not provided.",showOutput)
                if data.get('gisInfo')["sourceFilename"]:
                    sourceFasc=data.get('gisInfo')["sourceFilename"]
                else:
                    sourceFasc="source.asc"
                sourceFasc=os.path.join(thePath,sourceFasc)
                logOut = _logMsg(logOut,"  source    ----> " + sourceFasc,showOutput)
                
                if os.path.isfile(sourceFasc):
                    os.remove(sourceFasc)
                
                
                tempDir="_____temporalFiles"
                os.mkdir(tempDir, 0o775)
                
                focusLocal=os.path.join(tempDir,"fL.geojson")
                focusShape=os.path.join(tempDir, "fS.shp")
                focusTif=os.path.join(tempDir,"fT.tif")
                
                radius=cellSize*3
                
                cmdogr = f'ogr2ogr {focusLocal} {sourceMap} -t_srs {srs}  >> "{path_LogNeptunoGDAL}"'
                qgiscmd = QGISprefixPathBin + cmdogr
                os.system(qgiscmd)
                cmdogr = f'ogr2ogr -f "ESRI Shapefile" {focusShape}  {focusLocal}  \
                    -dialect sqlite \
                    -sql "select ST_buffer(geometry, {radius}) as geometry, 1 as zone FROM focus" \
                    -clipdst {xmin} {ymin} {xmax} {ymax} \
                    -t_srs {srs}  >> "{path_LogNeptunoGDAL}"'
                qgiscmd = QGISprefixPathBin + cmdogr
                os.system(qgiscmd)
                
                cmdrast = f'gdal_rasterize -a "zone" -of "GTiff" -a_srs {srs} -a_nodata -9999 \
                    -te {xmin} {ymin} {xmax} {ymax}  \
                    -tr {cellSize} {cellSize} -ot Byte {focusShape} {focusTif} \
                    >> "{path_LogNeptunoGDAL}"'
                qgiscmd = QGISprefixPathBin + cmdrast
                os.system(qgiscmd) 
                cmdtrans = f'gdal_translate -stats -of AAIGrid -co force_cellsize=true -ot Int32  \
                    {focusTif} {sourceFasc}  >> "{path_LogNeptunoGDAL}"'
                qgiscmd = QGISprefixPathBin + cmdtrans
                os.system(qgiscmd)
                shutil.rmtree(tempDir) 
            
        else:
            logOut = _logMsg(logOut,"  - WARNING: Label SourceMap is not avaliable at configFile.",showOutput)
            
        
    #ortophotoWMS
    if ortoQ:
        if os.path.isfile(ortoF):
            os.remove(ortoF)
        
     
        #orographyFrep = orographyF.replace(' ', '\\ ')
        #Compute resolution with gdalinfo
        cmdinfo = f'gdalinfo "{orographyFAbs}"'
        qgiscmd = QGISprefixPathBin + cmdinfo

        outinfo = subprocess.check_output(qgiscmd, shell=True)
        
        dimP =""
        for line in str(outinfo).split('\\n'):
            if 'Size is' in line:
                dimP = line
    
        reslX = int(dimP.split()[2].replace(',', ''))
        reslY = int(dimP.split()[3])
        aspersan="&"
        urlWMS=f"{ortophotoWMS}BBOX={xmin},{ymin},{xmax},{ymax}{aspersan}SRS={srs}{aspersan}FORMAT=image/png{aspersan}WIDTH={reslX}{aspersan}HEIGHT={reslY}"

        logOut = _logMsg(logOut,"  WMS orto  ----> "  + urlWMS,showOutput)

        #ortoFrep = ortoF.replace(' ', '\\ ')
        cmdtrans = f'gdal_translate -of PNG -outsize {reslX} {reslY} -projwin  {xmin} {ymax} {xmax} {ymin}   \
                    -projwin_srs {srs} -a_srs {srs}  \
                    "{urlWMS}" "{ortoF}" >> "{path_LogNeptunoGDAL}"'
        qgiscmd = QGISprefixPathBin + cmdtrans
        os.system(qgiscmd)

    logOut = _logMsg(logOut,"-------------------------------------------------------------------------",showOutput)
    logOut = _logMsg(logOut,"",showOutput)
    
    o["msg"] = logOut
    o["error"] = errorQ
    return o

