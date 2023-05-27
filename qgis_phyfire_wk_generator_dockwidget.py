# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PhyFireWKGeneratorDockWidget
                                 A QGIS plugin
 PhyFire Workspace Generator
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-05-22
        git sha              : $Format:%H$
        copyright            : (C) 2023 by David Cifuentes
        email                : david.cifuentes@usal.es
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import uuid
import shutil
from datetime import datetime
import json
from osgeo import gdal
import subprocess

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, QDate, QDateTime
from qgis.core import QgsMapLayerProxyModel, QgsProject, QgsVectorLayer, QgsSimpleMarkerSymbolLayerBase, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsVectorFileWriter, QgsApplication
from qgis.PyQt.QtWidgets import QMessageBox
from . import definitions
from .gdalneptuno import runGDALNeptuno

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qgis_phyfire_wk_generator_dockwidget_base.ui'))


class PhyFireWKGeneratorDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, pluginPath, currentPluginName, settings, parent=None):
        """Constructor."""
        super(PhyFireWKGeneratorDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.windowTitle = definitions.CONST_PROGRAM_NAME
        self.iface = iface
        self.path_plugin = pluginPath
        self.current_plugin_name = currentPluginName
        self.settings = settings
        self.setupUi(self)
        self.initialize()
        self.uuid = uuid.uuid4()
        

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()
        
    def initialize(self):
        self.about_qdialog = None

        path_file_qsettings = os.path.join(self.path_plugin, definitions.CONST_SETTINGS_FILE_NAME)
        self.settings = QSettings(path_file_qsettings,QSettings.IniFormat)
        
        self.path_datasource =os.path.join(self.path_plugin, definitions.CONST_SOURCE_PATH)  # os.path.join(self.path_plugin, 'examples', 'data', 'source')

        # Inicializar ROI combo
        existing_vector_layers = [l for l in QgsProject().instance().mapLayers().values() if isinstance(l, QgsVectorLayer)]
        self.roiLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.roiLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)
        self.roiLayerComboBox.clear()
        self.roiLayerComboBox.setAdditionalLayers(existing_vector_layers)
        
        # Combo fireSource
        self.firesourceLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.firesourceLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer) 
        self.firesourceLayerComboBox.clear()
        self.firesourceLayerComboBox.setAdditionalLayers(existing_vector_layers)
        
        # Combo fireBreaks
        self.firebreaksLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.firebreaksLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer) 
        self.firebreaksLayerComboBox.clear()
        self.firebreaksLayerComboBox.setAdditionalLayers(existing_vector_layers)
        
        # Combo windPoints
        firesourceLayer = self.firesourceLayerComboBox.currentLayer()
        # No permitimos que la capa asignada en fireSource pueda ser utilizada
        existing_wind_layers = [l for l in QgsProject().instance().mapLayers().values() if isinstance(l, QgsVectorLayer) and l!=firesourceLayer ]
        self.windLayerComboBox.setFilters(QgsMapLayerProxyModel.VectorLayer)
        self.windLayerComboBox.setFilters(QgsMapLayerProxyModel.PointLayer) 
        self.windLayerComboBox.clear()
        self.windLayerComboBox.setAdditionalLayers(existing_wind_layers)
        
        # Iniciar datos del settings:
        
        fireEventDateTimeString= definitions.CONST_PREFIRE_INITIAL_DATE_DEFAULT
        #now = QDateTime.currentDateTime()
        self.fireEventDateTimeEdit.setDateTime(QDateTime.fromString(fireEventDateTimeString,definitions.CONST_DATE_STRING_TEMPLATE))
    
        # Events:
        self.roiVirtualLayerButton.clicked.connect(self.addROIVirtualLayer)
        self.fireSourceVirtualLayerButton.clicked.connect(self.addFireSourceVirtualLayer)
        self.firebreaksVirtualLayerButton.clicked.connect(self.addFireBreaksVirtualLayer)
        self.windVirtualLayerButton.clicked.connect(self.addWindVirtualLayer)
        
        #self.outputFolderQgsFileWidget.fileChanged.connect(self.changePathOutputFolder)
        self.checkResourceButton.clicked.connect(self.checkPluginResources)
        self.generateWKButton.clicked.connect(self.createWorkspaceConfig)

    def addROIVirtualLayer(self):
        #Creacion de una capa en memoria
        ROIvirtualLyr =  QgsVectorLayer('Polygon?crs=epsg:4326', 'RoI' , "memory")
        ROIvirtualLyr.setOpacity(50)
        QgsProject.instance().addMapLayers([ROIvirtualLyr])

        #msgBox = QMessageBox(self.iface.mainWindow())
        #msgBox.setIcon(QMessageBox.Information)
        #msgBox.setWindowTitle("ROI Layer added")
        #msgBox.setText("Capa Region of Interest (ROI) generada")
        #msgBox.exec_()
        
    def addFireSourceVirtualLayer(self):
        #Creacion de una capa en memoria
        firesvirtualLyr =  QgsVectorLayer('Point?crs=epsg:4326', 'FireSource' , "memory")
        QgsProject.instance().addMapLayers([firesvirtualLyr])
        
    def addFireBreaksVirtualLayer(self):
        #Creacion de una capa en memoria
        firesvirtualLyr =  QgsVectorLayer('Linestring?crs=epsg:4326&field=width:integer', 'FireBreaks' , "memory")
        QgsProject.instance().addMapLayers([firesvirtualLyr])
    
    def addWindVirtualLayer_v0(self):
        #Creacion de una capa en memoria
        windirtualLyr =  QgsVectorLayer('Point?crs=epsg:4326&field=datetime:string&field=speed:double&field=deg:integer&field=level:double&field=temperature:integer&field=humidity:integer', 'Wind Points' , "memory")
        windirtualLyr.renderer().symbol().setColor(QtGui.QColor("blue"))
        windirtualLyr.renderer().symbol().setSize(15)
        windirtualLyr.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.Arrow)
        windirtualLyr.setCustomProperty("skipMemoryLayersCheck", 1)
        QgsProject.instance().addMapLayers([windirtualLyr])
        
    def addWindVirtualLayer(self):
        #Creacion de una capa en memoria
        windirtualLyr =  QgsVectorLayer('Point?crs=epsg:4326&field=metadata:string&field=timeseries:string&field=pointType:string', 'Wind Points' , "memory")
        windirtualLyr.renderer().symbol().setColor(QtGui.QColor("blue"))
        windirtualLyr.renderer().symbol().setSize(12)
        windirtualLyr.renderer().symbol().symbolLayer(0).setShape(QgsSimpleMarkerSymbolLayerBase.Arrow)
        windirtualLyr.setCustomProperty("skipMemoryLayersCheck", 1)
        QgsProject.instance().addMapLayers([windirtualLyr])
        
    def changePathOutputFolder(self, event):
        print("Ha cambiado la carpeta de salida")
        print(event)
    
    
    def _getJSONConfigFile(self, path_workspace):
        with open(os.path.join(path_workspace, 'config.json')) as config_file:
            config_file_contents = config_file.read()

        configObj = json.loads(config_file_contents)
        
        return configObj;
    
    def _saveJSONConfigFile(self, data, path_workspace):
        json_str = json.dumps(data, indent=4)
        fileconfig = open(os.path.join(path_workspace, 'config.json'), "wt")
        fileconfig.write(json_str)
        fileconfig.close()
    
    #Mode: 0 (-1: constant Wind, 0: hdWind, 1: hdWindRB, 2: hdWindAdjust)
    def _defineWindMode(self, path_workspace):
        windMode = -1
        windLayer = self.windLayerComboBox.currentLayer()
        if not windLayer:
            windMode = -1
        else:
            windMode= 0
            features = windLayer.getFeatures()
            for feature in features:
                timeserie = feature['timeseries']
                if timeserie is None:
                    windMode = -1
                #TODO: Check array con datos
            
        
        data = self._getJSONConfigFile(path_workspace)
        
        if data.get('hdwind')["mode"]:
            data.get('hdwind')["mode"] = windMode
            
        self._saveJSONConfigFile(data, path_workspace)
        
        return windMode
        
        
    
    
    def _createWorkspaceSKLFolder(self):
        
        path_workspace_sk = os.path.join(self.path_plugin, definitions.CONST_WK_SKELETON_PATH)
        path_workspace = self.outputFolderQgsFileWidget.filePath()
        
        if not path_workspace:
            path_workspace = os.path.join(self.path_plugin, "examples/data/workspace", str(self.uuid))
            if not os.path.isdir(path_workspace):
                os.mkdir(path_workspace, 0o755)
                
        #print("path_workspace_sk: " + path_workspace_sk)
        #print("path_workspace: " + path_workspace)
        if os.path.isdir(path_workspace):
            shutil.copytree(path_workspace_sk, path_workspace, dirs_exist_ok=True)

        return path_workspace
    
    def _getBoundingBox(self, layer):
        roiLayer = self.roiLayerComboBox.currentLayer()
        if not layer:
            return [0.0, 0.0, 0.0, 0.0]
        
        layerCrs = layer.crs()
        extentRectangle = layer.extent()
        extentWkt = extentRectangle.asWktPolygon()
        extentGeometry = QgsGeometry.fromWkt(extentWkt)
        targetCrs = QgsCoordinateReferenceSystem(4326)
        crsOperation = QgsCoordinateTransform(layerCrs, targetCrs, QgsProject.instance())
        extentGeometry.transform(crsOperation)
        #roiExtentWkt = roiExtentGeometry.asWkt()
        boundigBox = extentGeometry.boundingBox()
        #xmin = boundigBox.xMinimum()
        #xmax = boundigBox.xMaximum()
        #ymin = boundigBox.yMinimum()
        #ymax = boundigBox.yMaximum()

        return [boundigBox.xMinimum(), boundigBox.yMinimum(), boundigBox.xMaximum(), boundigBox.yMaximum()]
    
    def _hasBoundingBox(self, layer):
        bbox = self._getBoundingBox(layer)
        
        if len(bbox) ==4 and bbox[0] != 0.0 and bbox[1] != 0.0 and bbox[2] != 0.0 and bbox[3] != 0.0:
            return True
        return False
    
    def _getFeatureCount(self, layer):
        pr = layer.dataProvider()
        return pr.featureCount()
    
    def _fillConfigFile(self, path_workspace, layer):
        path_wk_fileconfig = os.path.join(path_workspace, 'config.json')
        
        path_data_source = os.path.join(self.path_plugin, definitions.CONST_SOURCE_PATH)
        
        #read input file y reemplazamos
        fileconfig = open(path_wk_fileconfig, "rt")
        #read file contents to string
        data_fileconfig = fileconfig.read()
        #replace all occurrences of the required string
        
        
        dteventfire = self.fireEventDateTimeEdit.dateTime().toString(definitions.CONST_DATE_STRING_TEMPLATE)
        
        # BBOX ROI Layer
        roiExt = self._getBoundingBox(layer)
        bbox = f"{roiExt[0]}, {roiExt[1]}, {roiExt[2]}, {roiExt[3]}"
        
        data_fileconfig = data_fileconfig.replace('<TEMPLATE_INFO_CREATEDAT>', datetime.now().isoformat())
        data_fileconfig = data_fileconfig.replace('<TEMPLATE_INFO_TITLE>', str(self.titleLineEdit.text()))
        data_fileconfig = data_fileconfig.replace('<TEMPLATE_INFO_FIRE_EVENT>', datetime.strptime(str(dteventfire), '%Y-%m-%d %H:%M').isoformat())
        data_fileconfig = data_fileconfig.replace('<TEMPLATE_INFO_SIMULATION_UUID>', str(self.uuid))
        data_fileconfig = data_fileconfig.replace('<TEMPLATE_GIS_PAHT_SOURCE>', path_data_source)
        data_fileconfig = data_fileconfig.replace('<TEMPLATE_WORKSPACE_NAME>', os.path.basename(path_workspace))
        data_fileconfig = data_fileconfig.replace('"<TEMPLATE_ARRAY_BBOX>"', bbox)
        data_fileconfig = data_fileconfig.replace('<TEMPLATE_INFO_UPDATEDAT>', str(datetime.now().isoformat()))
        #close the input file
        fileconfig.close()
       
       
        fileconfig = open(path_wk_fileconfig, "wt")
        #overrite the input file with the resulting data
        fileconfig.write(data_fileconfig)
        #close the file
        fileconfig.close()
    
    def _fillModelParamsFile(self, path_workspace):
        path_wk_modelparams = os.path.join(path_workspace, 'Data', 'modelParameters.json')
        fileparams = open(path_wk_modelparams, "rt")
        data_params = fileparams.read()
        data_params = data_params.replace('<TEMPLATE_INFO_SIMULATION_UUID>', str(self.uuid))
        fileparams.close()
       
        fileparams = open(path_wk_modelparams, "wt")
        fileparams.write(data_params)
        fileparams.close()

    def checkPluginResources(self):
        
        msg = "[x] CWD ( " + str(os.getcwd()) +")\n"
        
        if int(gdal.VersionInfo()) > 3020000:
            msg += "[x] GDAL compatible ( " + str(gdal.__version__) +")\n"
            icon = QMessageBox.Information
        else:
            msg += "[?] GDAL no encontrado\n"
            icon = QMessageBox.Warning
        
        
        msgerr = []
        sf = ["DEM", "fireBreaksDB", "fuelTypeDB", "temperatureDB"]
        foldersource = os.path.join(self.path_plugin, definitions.CONST_SOURCE_PATH)
        for f in sf:
            folders = os.path.join(foldersource, f)
            fsize = self.get_size(folders, "mb")
            #print("folder: " + str(folders) + " size: " + str(fsize) + "mb" )
            if(fsize < 1):
                msgerr.append("[?] Fuente de datos " + f + " no encontrada")
                
        if len(msgerr) == 0:
            icon = QMessageBox.Information
            msg += "[x] Fuentes de datos instaladas correctamente \n"
        else:
            icon = QMessageBox.Warning
            for m in msgerr:
                msg = msg + m + "\n"
            
        
        msgBox = QMessageBox(self.iface.mainWindow())
        msgBox.setIcon(icon)
        msgBox.setWindowTitle(self.windowTitle) 
        msgBox.setText(msg)
        msgBox.exec_()
        return    
            
            
            
        
    def get_size(self, file_path, unit='bytes'):
        #file_size = os.path.getsize(file_path)
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(file_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)

        exponents_map = {'bytes': 0, 'kb': 1, 'mb': 2, 'gb': 3}
        if unit not in exponents_map:
            raise ValueError("Must select from \
            ['bytes', 'kb', 'mb', 'gb']")
        else:
            size = total_size / 1024 ** exponents_map[unit]
            return round(size, 3)
        
    
    def createWorkspaceConfig(self):
        # Check data:
        msgerr = []
        if not self.titleLineEdit.text():
            msgerr.append("[?] Título no definido")
        
        dt = self.fireEventDateTimeEdit.dateTime()
        dtstr = dt.toString(self.fireEventDateTimeEdit.displayFormat())
        if not dtstr:
            msgerr.append("[?] Fecha no definida")
        
        #Comprobar que tenga features
        if not self.roiLayerComboBox.currentLayer():
            msgerr.append("[?] ROI no definida")
            
        if not self.firesourceLayerComboBox.currentLayer():
            msgerr.append("[?] FireSource no definida")
            
        #if not self.firebreaksLayerComboBox.currentLayer():
        #    msgerr.append("FireBreaks no definida")
            
        #if not self.windLayerComboBox.currentLayer():
        #    msgerr.append("Wind Points no definidos")
        
        if len(msgerr) > 0:
            msgBox = QMessageBox(self.iface.mainWindow())
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle(self.windowTitle)
            msg = "Complete el formulario:\n"
            for m in msgerr:
                msg = msg + m + "\n"
            msgBox.setText(msg)
            msgBox.exec_()
            return
        
        # Check features of layers:
        roiLayer = self.roiLayerComboBox.currentLayer()
        
        if not self._hasBoundingBox(roiLayer):
            msgBox = QMessageBox(self.iface.mainWindow())
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("No hay una feature de la región de interés (ROI) definida. Edite la capa y cree un poligono para definir el dominio de simulación")
            msgBox.exec_()
            return
        
        # Crear workspace:
        path_workspace = self._createWorkspaceSKLFolder()
        #print(path_workspace)
        # Configurar config.json
        self._fillConfigFile(path_workspace, roiLayer)
        # Configurar modelParams.json
        self._fillModelParamsFile(path_workspace)
        
        # Check fireSouce
        if self._getFeatureCount( self.firesourceLayerComboBox.currentLayer()) < 1:
            msgBox = QMessageBox(self.iface.mainWindow())
            msgBox.setIcon(QMessageBox.Warning)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Debe definir al menos un foco de incendio")
            msgBox.exec_()
            return
        
        # Crear fireSource.geojson
        fireSourceLayer = self.firesourceLayerComboBox.currentLayer()
        path_out_file = os.path.join(path_workspace, 'Data', 'fireSource.geojson')
        QgsVectorFileWriter.writeAsVectorFormat(fireSourceLayer, path_out_file, 'utf-8', QgsCoordinateReferenceSystem(4326), 'GeoJson')
            
        # Check Capa windLayer
        windMode = self._defineWindMode(path_workspace)
        if windMode >=0:
            # Guardar capa en GeoJSON
            windLayer = self.windLayerComboBox.currentLayer()
            path_out_file = os.path.join(path_workspace, 'Data', 'windGIS.geojson')
            QgsVectorFileWriter.writeAsVectorFormat(windLayer, path_out_file, 'utf-8', QgsCoordinateReferenceSystem(4326), 'GeoJson')
            
        
        # Si hay capa de cortafuegos se comprueba y guarda
        firebreakLayer = self.firebreaksLayerComboBox.currentLayer()
        if firebreakLayer:
            if self._getFeatureCount( firebreakLayer) < 1:
                msgBox = QMessageBox(self.iface.mainWindow())
                msgBox.setIcon(QMessageBox.Warning)
                msgBox.setWindowTitle(self.windowTitle)
                msgBox.setText("Debe definir al menos cortafuegos")
                msgBox.exec_()
                return
            
            # Guardar capa en GeoJSON
            path_out_file = os.path.join(path_workspace, 'Data', 'fireBreaks.geojson')
            QgsVectorFileWriter.writeAsVectorFormat(firebreakLayer, path_out_file, 'utf-8', QgsCoordinateReferenceSystem(4326), 'GeoJson')
        
        #print("PathWorkspace ---> " + path_workspace)
        fileconfig = os.path.join(path_workspace, 'config.json')
        
        GDALNeptunoLog = dict()
        GDALNeptunoLog["msg"] = ""
        GDALNeptunoLog["error"] = True
        try:
            GDALNeptunoLog = runGDALNeptuno(fileconfig, False)
        except:
            GDALNeptunoLog["msg"] = " - ERROR: En ejecución runGDALNeptuno"
            GDALNeptunoLog["error"] = True
        finally:
            fileGDALNeptunoLog = open(os.path.join(path_workspace, 'Logs', 'GDALNeptuno.log' ), "w")
            if len(GDALNeptunoLog) == 2:
                fileGDALNeptunoLog.write(GDALNeptunoLog["msg"])
            else:
                fileGDALNeptunoLog.write("Error al generar el Log de extracción de datos")
            fileGDALNeptunoLog.close()
        
        if GDALNeptunoLog["error"]:
            msgBox = QMessageBox(self.iface.mainWindow())
            msgBox.setIcon(QMessageBox.Critical)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("Se ha producido un error durante la generación del workspace. Revise Logs del workspace")
            msgBox.exec_()
            return
        
        if GDALNeptunoLog["error"] == False:
            msgBox = QMessageBox(self.iface.mainWindow())
            msgBox.setIcon(QMessageBox.Information)
            msgBox.setWindowTitle(self.windowTitle)
            msgBox.setText("¡Enhorabuena!\n\nEl workspace de datos de PhyFire se ha generado correctamente en:\n\n" + path_workspace)
            msgBox.exec_()
            return
 
        
        