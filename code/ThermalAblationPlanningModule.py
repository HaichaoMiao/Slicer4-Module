from __main__ import vtk, qt, ctk, slicer
import xml.dom.minidom
import random
import string
from Device import Device
from VTKSourceDrawer import Probe, AblationZone, InsertionSphere


# todo: shapes of the ablation zone
# todo: error handling when loading an  invalid xml-file

# ThermalAblationPlanningModule
#

standardDevicesXml = """
<devices>
    <device>
        <name>Galil CryoHit 17g MRI S needle</name>
        <diameter>2</diameter>
        <length>175</length>
        <ablationzone>
            <shape>sphere</shape>
            <shapeRadius>14</shapeRadius>
        </ablationzone>
    </device>
    <device>
        <name>Galil CryoHit 17g MRI I needle</name>
        <diameter>2</diameter>
        <length>175</length>
        <ablationzone>
            <shape>cylinder</shape>
            <shapeRadius>14</shapeRadius>
            <shapeHeight>34</shapeHeight>
        </ablationzone>
    </device>
    <device>
        <name>Galil CryoHit 2mm probe</name>
        <diameter>3</diameter>
        <length>180</length>
        <ablationzone>
            <shape>cylinder</shape>
            <shapeRadius>20</shapeRadius>
            <shapeHeight>35</shapeHeight>
        </ablationzone>
    </device>
    <device>
        <name>Galil CryoHit 3mm probe</name>
        <diameter>4</diameter>
        <length>180</length>
        <ablationzone>
            <shape>cylinder</shape>
            <shapeRadius>19</shapeRadius>
            <shapeHeight>50</shapeHeight>
        </ablationzone>
    </device>
    <device>
        <name>Microtaze AZM-520 Deep percutaneous monopolar electrode (60W, 60sec)</name>
        <diameter>2</diameter>
        <length>150</length>
        <ablationzone>
            <shape>cylinder</shape>
            <shapeRadius>18</shapeRadius>
            <shapeHeight>40</shapeHeight>
        </ablationzone>
    </device>
    <device>
        <name>Microtaze AZM-520 Deep percutaneous monopolar electrode (60W, 60sec)</name>
        <diameter>2</diameter>
        <length>150</length>
        <ablationzone>
            <shape>cylinder</shape>
            <shapeRadius>18</shapeRadius>
            <shapeHeight>40</shapeHeight>
        </ablationzone>
    </device>
    <device>
        <name>LeVeen Needle Electrode (200W RF Generator)</name>
        <diameter>2</diameter>
        <length>150</length>
        <ablationzone>
            <shape>sphere</shape>
            <shapeRadius>50</shapeRadius>
        </ablationzone>
    </device>
</devices>
"""

class ThermalAblationPlanningModule:

  def __init__(self, parent):
      
    parent.title = "Thermal Ablation Planning"
    parent.categories = ["Tumor Ablation"]
    parent.dependencies = []
    parent.contributors = ["Haichao Miao <hmiao87@gmail.com>"]
    parent.helpText = """
    Slicer module for planning a thermal ablation procedure.
    For more information, read the README 
.
    """
    parent.acknowledgementText = """
    This module was created by Haichao Miao as a part of his bachelor thesis at the Vienna University of Technology. 
    """
    self.parent = parent
    
#
# qThermalAblationPlanningModuleWidget
#

class ThermalAblationPlanningModuleWidget:

  def __init__(self, parent = None):
      
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
      
    self.layout = self.parent.layout()
    
    self.parseDevices()
    
    if not parent:
      self.setup()
      self.entryPointFiducialsNodeSelector.setMRMLScene(slicer.mrmlScene)

      self.parent.show()
  
  # setup the Widgets  
  def setup(self):
    
    #
    # Probe Placement Planning Collapsible button
    #
    
    self.probeColors = [[1, 0.2, 0], [0, 0.2, 0.9], [0.1, 1, 0.1], [0.5, 0.3, 0.9], [1, 0.9, 0]]
    self.ablationZoneColor = [1,0.5,0]
    self.ablationZones = []
    self.ablationZonesCheckBoxes = []
    
    self.sameFiducialErrorMessage = qt.QErrorMessage()
    
    probePlacementPlanningCollapsibleButton = ctk.ctkCollapsibleButton()
    probePlacementPlanningCollapsibleButton.text = "Probe Placement Planning"
    self.layout.addWidget(probePlacementPlanningCollapsibleButton)
    
    formLayout = qt.QFormLayout(probePlacementPlanningCollapsibleButton)

    # 0: Load Devices XML
    fileSelectorGroupBox = qt.QGroupBox()
    fileSelectorGroupBox.setTitle("0: Load Devices XML")
    self.fileSelectorGroupBox = fileSelectorGroupBox
    
    formLayout.addWidget(fileSelectorGroupBox)
    
    fileSelectorLayout = qt.QFormLayout(fileSelectorGroupBox)
    
    selectDevicesFileButton = qt.QPushButton()
    selectDevicesFileButton.setText("Load Devices XML")
    self.selectDevicesFileButton = selectDevicesFileButton
    
    self.selectDevicesFileButton.connect('clicked(bool)', self.onSelectDevicesFileButtonClicked)
    
    fileNameLabel = qt.QLabel("No file Selected.")
    
    self.fileNameLabel = fileNameLabel
    
    fileSelectorLayout.addRow(selectDevicesFileButton, self.fileNameLabel)
    
    # 1: Device Selection
    
    deviceSelectionGroupBox = qt.QGroupBox()
    deviceSelectionGroupBox.setTitle("1: Device Selection")
    self.deviceSelectionGroupBox = deviceSelectionGroupBox
    
    formLayout.addWidget(deviceSelectionGroupBox)
    
    deviceSelectionLayout = qt.QFormLayout(deviceSelectionGroupBox)
    
    devicesComboBox = qt.QComboBox()

    for device in self.devices:
      devicesComboBox.addItem(device.name)
      
      
    self.devicesComboBox = devicesComboBox
    
    self.insertionRadius = self.devices[self.devicesComboBox.currentIndex].length
    
    self.devicesComboBox.connect('currentIndexChanged(int)', self.deviceSelected)
    
    deviceSelectionLayout.addRow("Select Device: ", devicesComboBox)
    
    # 2: Insertion Radius
    
    insertionRadiusGroupBox = qt.QGroupBox()
    insertionRadiusGroupBox.setTitle("2: Placement of ROI")
    self.insertionRadiusGroupBox = insertionRadiusGroupBox
    
    formLayout.addWidget(insertionRadiusGroupBox)
    
    insertionRadiusLayout = qt.QGridLayout(insertionRadiusGroupBox)
    
    self.targetTumorFiducialsNodeSelector = slicer.qMRMLNodeComboBox()
    self.targetTumorFiducialsNodeSelector.objectName = "targetTumorFiducialsNodeSelector"
    self.targetTumorFiducialsNodeSelector.nodeTypes = ['vtkMRMLAnnotationFiducialNode']
    self.targetTumorFiducialsNodeSelector.baseName = "Target Tumor"
    self.targetTumorFiducialsNodeSelector.noneEnabled = False
    self.targetTumorFiducialsNodeSelector.addEnabled = False
    self.targetTumorFiducialsNodeSelector.removeEnabled = False
    
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.targetTumorFiducialsNodeSelector, 'setMRMLScene(vtkMRMLScene*)')  
    
    self.targetTumorFiducialsNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.targetTumorFiducialsNodeSelectorChanged)
    
    addInsertionRadiusButton = qt.QPushButton("Add Insertion Radius")
    addInsertionRadiusButton.toolTip = "Add Insertion Radius"
    self.addInsertionRadiusButton = addInsertionRadiusButton
    addInsertionRadiusButton.connect('clicked(bool)', self.onAddInsertionRadiusButtonClicked)

    
    deleteInsertionRadiusButton = qt.QPushButton("Delete Insertion Radius")
    deleteInsertionRadiusButton.toolTip = "Delete Insertion Radius"
    self.deleteInsertionRadiusButton = deleteInsertionRadiusButton
    self.deleteInsertionRadiusButton.connect('clicked(bool)', self.onDeleteInsertionRadiusButtonClicked)

    
    insertionRadiusLayout.addWidget(self.targetTumorFiducialsNodeSelector, 1, 1)
    insertionRadiusLayout.addWidget(self.addInsertionRadiusButton, 1, 2)
    insertionRadiusLayout.addWidget(self.deleteInsertionRadiusButton, 1, 3)
    

    # 3: Probe Placement
    
    probePlacementGroupBox = qt.QGroupBox()
    probePlacementGroupBox.setTitle("3: Probe Placement")
    self.probePlacementGroupBox = probePlacementGroupBox
    
    formLayout.addWidget(probePlacementGroupBox)
    
    probePlacementLayout = qt.QFormLayout(probePlacementGroupBox)

    self.entryPointFiducialsNodeSelector = slicer.qMRMLNodeComboBox()
    self.entryPointFiducialsNodeSelector.objectName = "entryPointFiducialsNodeSelector"
    self.entryPointFiducialsNodeSelector.nodeTypes = ['vtkMRMLAnnotationFiducialNode']
    self.entryPointFiducialsNodeSelector.baseName = "Entry Point"
    self.entryPointFiducialsNodeSelector.noneEnabled = False
    self.entryPointFiducialsNodeSelector.addEnabled = False
    self.entryPointFiducialsNodeSelector.removeEnabled = False
    
    probePlacementLayout.addRow("Entry Point:", self.entryPointFiducialsNodeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.entryPointFiducialsNodeSelector, 'setMRMLScene(vtkMRMLScene*)')     
    
    self.entryPointFiducialsNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.entryPointFiducialsNodeSelectorChanged)

    self.targetFiducialsNodeSelector = slicer.qMRMLNodeComboBox()
    self.targetFiducialsNodeSelector.objectName = "targetFiducialsNodeSelector"
    self.targetFiducialsNodeSelector.nodeTypes = ['vtkMRMLAnnotationFiducialNode']
    self.targetFiducialsNodeSelector.baseName = "Target Point"
    self.targetFiducialsNodeSelector.noneEnabled = False
    self.targetFiducialsNodeSelector.addEnabled = False
    self.targetFiducialsNodeSelector.removeEnabled = False
    
    probePlacementLayout.addRow("Target Point:", self.targetFiducialsNodeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.targetFiducialsNodeSelector, 'setMRMLScene(vtkMRMLScene*)')   

    self.targetFiducialsNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.targetFiducialsNodeSelectorChanged)
    
    placeProbeButton = qt.QPushButton("Place Probe")
    placeProbeButton.toolTip = "Place Probe"
    self.placeProbeButton = placeProbeButton
    
    placeProbeButton.connect('clicked(bool)', self.onPlaceProbeButtonClicked)
    
    self.probeNameLineEdit = qt.QLineEdit()
    
    self.probeCnt = 1
    
    self.probeNameLineEdit.text = 'Probe ' + str(self.probeCnt)
    
    probePlacementLayout.addRow(self.probeNameLineEdit, placeProbeButton)
    
    self.probePlacementLayout = probePlacementLayout
    
    # 4: Draw Ablation Zone

    drawAblationZoneGroupBox = qt.QGroupBox()
    drawAblationZoneGroupBox.setTitle("4: Draw Ablation Zone")
    self.drawAblationZoneGroupBox = drawAblationZoneGroupBox
    
    formLayout.addWidget(drawAblationZoneGroupBox)
    
    drawAblationZoneLayout = qt.QFormLayout(drawAblationZoneGroupBox)
    
    drawAblationZoneButton = qt.QPushButton("Draw Ablation Zone")
    drawAblationZoneButton.toolTip = "Draw Ablation Zone"
    self.drawAblationZoneButton = drawAblationZoneButton
    
    drawAblationZoneButton.connect('clicked(bool)', self.onDrawAblationZoneButtonClicked)
    
    drawAblationZoneLayout.addRow(drawAblationZoneButton)
    
    # Ablation Zones
    
    ablationZonesGroupBox = qt.QGroupBox()
    ablationZonesGroupBox.setTitle("Ablation Zones")
    self.ablationZonesGroupBox = ablationZonesGroupBox
    formLayout.addWidget(ablationZonesGroupBox)

    ablationZonesLayout = qt.QFormLayout(ablationZonesGroupBox)
    
    self.ablationZonesLayout = ablationZonesLayout
    
  def parseDevices(self):
    
    dom = xml.dom.minidom.parseString(standardDevicesXml)
    
    self.devices = []
    
    self.parseDom(dom)  
       
  def parseDevicesFile(self, file):
    
    dom = xml.dom.minidom.parse(file)
    
    self.devices = []
    
    self.parseDom(dom)  
    
    self.devicesComboBox.clear()
    
    for device in self.devices:
      self.devicesComboBox.addItem(device.name)
  
  def parseDom(self, dom):
    
    for num, elem in enumerate(dom.getElementsByTagName("device")):
      shapeRadius = 0
      shapeHeight = 0
      shapeVolume = 0
      for node in elem.getElementsByTagName("name"):
          name = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("diameter"):
          diameter = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("length"):
          length = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("shape"):
          shape = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("shapeRadius"):
          shapeRadius = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("shapeHeight"):
          shapeHeight = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("shapeVolume"):
          shapeVolume = node.childNodes[0].nodeValue
          
      self.devices.append(Device(name, int(diameter), int(length), shape, int(shapeRadius), int(shapeHeight), int(shapeVolume)))

  def targetTumorFiducialsNodeSelectorChanged(self):
    print ""
  
  def entryPointFiducialsNodeSelectorChanged(self):
    self.probePlacementGroupBox.setStyleSheet("QGroupBox {} ")
  
  def targetFiducialsNodeSelectorChanged(self):
    self.probePlacementGroupBox.setStyleSheet("QGroupBox {} ")
      
  def onSelectDevicesFileButtonClicked(self):
    
    fileDialog = qt.QFileDialog()
    
    self.fileDialog = fileDialog
    
    if fileDialog.exec_() == 1:
      path = fileDialog.selectedFiles()[0]
    
    file = open(path)
    
    self.layout.addWidget(fileDialog)
    
    self.parseDevicesFile(file)
    
    self.fileNameLabel.setText(path)
  
  def onAddInsertionRadiusButtonClicked(self):
    
    self.insertionSphere = InsertionSphere(self.targetTumorFiducialsNodeSelector.currentNode(), self.insertionRadius)
  
  def onDeleteInsertionRadiusButtonClicked(self):
    scene = slicer.mrmlScene
    self.insertionSphere.insertionRadiusModelDisplay.VisibilityOff()
    self.insertionSphere.insertionRadiusModelDisplay.SliceIntersectionVisibilityOff()
    # todo: delete models from scene
    
  def deviceSelected(self):
    self.insertionRadius = self.devices[self.devicesComboBox.currentIndex].length
      
  def onPlaceProbeButtonClicked(self):
    
    if (self.entryPointFiducialsNodeSelector.currentNode() is self.targetFiducialsNodeSelector.currentNode()):
      self.sameFiducialErrorMessage.showMessage("Target Point must be different from Entry Point.")
      self.probePlacementGroupBox.setStyleSheet("QGroupBox {border: 2px solid red;} ")
    else:
      self.probeCnt = self.probeCnt + 1
      probeText = 'Probe ' + str(self.probeCnt)
      self.probeNameLineEdit.setText(probeText)
      Probe(self.entryPointFiducialsNodeSelector.currentNode(), self.targetFiducialsNodeSelector.currentNode(), self.devices[self.devicesComboBox.currentIndex].length, self.devices[self.devicesComboBox.currentIndex].diameter, probeText, self.probeColors[self.probeCnt%5])
      self.probePlacementGroupBox.setStyleSheet("QGroupBox {} ")
    
  def onDrawAblationZoneButtonClicked(self):
    
    if (self.entryPointFiducialsNodeSelector.currentNode() is self.targetFiducialsNodeSelector.currentNode()):
      self.sameFiducialErrorMessage.showMessage("Target Point must be different from Entry Point.")
    else:
      self.ablationZones.append(AblationZone(self.entryPointFiducialsNodeSelector.currentNode(), self.targetFiducialsNodeSelector.currentNode(), self.devices[self.devicesComboBox.currentIndex].shape, self.devices[self.devicesComboBox.currentIndex].shapeRadius, self.devices[self.devicesComboBox.currentIndex].shapeHeight, self.devices[self.devicesComboBox.currentIndex].shapeVolume, self.ablationZoneColor))
      curAblationZoneCheckBox = qt.QCheckBox(self.ablationZones[-1].lesionModel.GetName())
      curAblationZoneCheckBox.setCheckState(2)
      curAblationZoneCheckBox.setStyleSheet("QCheckBox {background-color: orange;} ")
      curAblationZoneCheckBox.connect('stateChanged(int)', self.ablationZonesCheckBoxesStateChanged)
      
      self.ablationZonesLayout.addWidget(curAblationZoneCheckBox)
      self.ablationZonesCheckBoxes.append(curAblationZoneCheckBox)
      
  def ablationZonesCheckBoxesStateChanged(self):
    for i in range(len(self.ablationZonesCheckBoxes)):
     if self.ablationZonesCheckBoxes[i].checkState() == 0:
       self.ablationZones[i].setAblationZoneInvisible()
     if self.ablationZonesCheckBoxes[i].checkState() == 2:
       self.ablationZones[i].setAblationZoneVisible()  
