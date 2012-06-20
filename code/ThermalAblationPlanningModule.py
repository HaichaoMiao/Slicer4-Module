from __main__ import vtk, qt, ctk, slicer
import xml.dom.minidom
import random
import string
from math import sqrt, pow


# todo: shapes of the ablation zone

# ThermalAblationPlanningModule
#

standardDevicesXml = """
<devices>
    <device>
        <name>Galil ICE Seed</name>
        <diameter>5</diameter>
        <length>150</length>
        <ablationzone>
            <shape>sphere</shape>
            <shapeRadius>15</shapeRadius>
        </ablationzone>
    </device>
    <device>
        <name>Galil ICE Rod</name>
        <diameter>8</diameter>
        <length>120</length>
        <ablationzone>
            <shape>cylinder</shape>
            <shapeRadius>20</shapeRadius>
            <shapeHeight>40</shapeHeight>
        </ablationzone>
    </device>
    <device>
        <name>TestEllipsoid</name>
        <diameter>4</diameter>
        <length>190</length>
        <ablationzone>
            <shape>sphere</shape>
            <shapeHeight>40</shapeHeight>
            <shapeVolume>240</shapeVolume>
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
    
    '''
    # Ablation Zones (checkableNodeComboBox)
    # checkedNodes() doesn't work in python
    
    ablationZonesGroupBox = qt.QGroupBox()
    ablationZonesGroupBox.setTitle("Ablation Zones")
    self.ablationZonesGroupBox = ablationZonesGroupBox
    formLayout.addWidget(ablationZonesGroupBox)

    ablationZonesLayout = qt.QFormLayout(ablationZonesGroupBox)
    
    self.ablationZonesLayout = ablationZonesLayout
    
    modelNodesComboBox = slicer.qMRMLCheckableNodeComboBox()
    modelNodesComboBox.objectName = "displayNodeSelector"
    modelNodesComboBox.nodeTypes = ['vtkMRMLModelNode']
    modelNodesComboBox.baseName = "Display Nodes"
    modelNodesComboBox.noneEnabled = False
    modelNodesComboBox.addEnabled = False
    modelNodesComboBox.removeEnabled = False
    self.modelNodesComboBox = modelNodesComboBox
    
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.modelNodesComboBox, 'setMRMLScene(vtkMRMLScene*)')  
    
    
    self.ablationZonesLayout.addRow("Display Nodes:", self.modelNodesComboBox)
    
    setModelsVisibleButton = qt.QPushButton("Set Models Visible")
    setModelsVisibleButton.toolTip = "set selected models visible"
    setModelsVisibleButton.connect('clicked(bool)', self.onSetModelsVisibleButtonClicked)
    self.setModelsVisibleButton = setModelsVisibleButton
    
    setModelsInvisibleButton = qt.QPushButton("Set Models Invisible")
    setModelsInvisibleButton.toolTip = "set selected models invisible"
    setModelsInvisibleButton.connect('clicked(bool)', self.onSetModelsInvisibleButtonClicked)
    self.setModelsInvisibleButton = setModelsInvisibleButton
    
    
    self.ablationZonesLayout.addWidget(self.setModelsVisibleButton)
    self.ablationZonesLayout.addWidget(self.setModelsInvisibleButton)
    
    '''
    '''
    ablationZonesView = slicer.qMRMLTreeView()
    ablationZonesView.setSceneModelType('vtkMRMLModelHierarchyNode')
    
    
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        ablationZonesView, 'setMRMLScene(vtkMRMLScene*)')  
    
    self.ablationZonesLayout.addRow("Display Nodes:", ablationZonesView) 
    '''
    
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
    print "targetTumorFiducialsNodeSelectorChanged"
  
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
      drawProbe(self.entryPointFiducialsNodeSelector.currentNode(), self.targetFiducialsNodeSelector.currentNode(), self.devices[self.devicesComboBox.currentIndex].length, self.devices[self.devicesComboBox.currentIndex].diameter, probeText, self.probeColors[self.probeCnt%5])
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
        
class drawProbe:
    
  def __init__(self, entryPointFiducialListNode, targetFiducialListNode, length, diameter, probeText, probeColor):
    
    entryPointFid = entryPointFiducialListNode
    targetFid = targetFiducialListNode
    scene = slicer.mrmlScene
    
    #Create an probe.
    probe = vtk.vtkCylinderSource()
    probe.SetHeight(length)
    probe.SetRadius(diameter / 2)
    
    pos = [0 for i in range(3)]
    
    # get coordinates from current entry point fiducial
    currentEntryPointFiducialCoordinatesRAS = [0, 0, 0]
    
    entryPointFid.GetFiducialCoordinates(currentEntryPointFiducialCoordinatesRAS)
    
    currentTargetFiducialCoordinatesRAS = [0, 0, 0]
    
    targetFid.GetFiducialCoordinates(currentTargetFiducialCoordinatesRAS)
    
    # pos is the vector that describes the distance between the target and the entry point
    for i in range(3):
      pos[i] = currentTargetFiducialCoordinatesRAS[i] - currentEntryPointFiducialCoordinatesRAS[i]
      
    pointsDistance = sqrt(pow(pos[0], 2) + pow(pos[1], 2) + pow(pos[2], 2))
    
    # len is the vector that describes the length of the probe
    len = [0 for i in range(3)]
    for i in range(3):
      len[i] = length / pointsDistance * pos[i]
      
    translationTarget = [currentTargetFiducialCoordinatesRAS[0] - len[0] / 2, currentTargetFiducialCoordinatesRAS[1] - len[1] / 2, currentTargetFiducialCoordinatesRAS[2] - len[2] / 2]

    # Generate a random start and end point
    random.seed(8775070)
    startPoint = [0 for i in range(3)]
    startPoint[0] = currentEntryPointFiducialCoordinatesRAS[0]
    startPoint[1] = currentEntryPointFiducialCoordinatesRAS[1]
    startPoint[2] = currentEntryPointFiducialCoordinatesRAS[2]
    endPoint = [0 for i in range(3)]
    endPoint[0] = currentTargetFiducialCoordinatesRAS[0]
    endPoint[1] = currentTargetFiducialCoordinatesRAS[1]
    endPoint[2] = currentTargetFiducialCoordinatesRAS[2]
     
    # Compute a basis
    normalizedX = [0 for i in range(3)]
    normalizedY = [0 for i in range(3)]
    normalizedZ = [0 for i in range(3)]
     
    # The X axis is a vector from start to end
    math = vtk.vtkMath()
    math.Subtract(endPoint, startPoint, normalizedX)
    # length = math.Norm(normalizedX)
    math.Normalize(normalizedX)
    
    # The Z axis is an arbitrary vector cross X
    arbitrary = [0 for i in range(3)]
    arbitrary[0] = random.uniform(-10,10)
    arbitrary[1] = random.uniform(-10,10)
    arbitrary[2] = random.uniform(-10,10)
    math.Cross(normalizedX, arbitrary, normalizedZ)
    math.Normalize(normalizedZ)
    
    # The Y axis is Z cross X
    math.Cross(normalizedZ, normalizedX, normalizedY)
    matrix = vtk.vtkMatrix4x4()
     
    # Create the direction cosine matrix
    matrix.Identity()
    for i in range(3):
      matrix.SetElement(i, 0, normalizedX[i])
      matrix.SetElement(i, 1, normalizedY[i])
      matrix.SetElement(i, 2, normalizedZ[i])
     
    # Apply the transforms
    transform = vtk.vtkTransform()
    transform.Translate(translationTarget)
    transform.Concatenate(matrix)
    transform.RotateZ(90)
    
    
    # Create model node
    probeModel = slicer.vtkMRMLModelNode()
    probeModel.SetScene(scene)
    probeModel.SetName(probeText + "-%s" % targetFid.GetName())
    probeModel.SetAndObservePolyData(probe.GetOutput())

    # Create display node
    probeModelDisplay = slicer.vtkMRMLModelDisplayNode()
    
    probeModelDisplay.SetColor(probeColor)
    
    probeModelDisplay.SetOpacity(1)
    probeModelDisplay.SliceIntersectionVisibilityOn()
    
    probeModelDisplay.SetScene(scene)
    scene.AddNode(probeModelDisplay)
    probeModel.SetAndObserveDisplayNodeID(probeModelDisplay.GetID())

    # Add to scene
    probeModelDisplay.SetPolyData(probe.GetOutput())
    
    scene.AddNode(probeModel)
    
    
    # Create probeTransform node
    probeTransform = slicer.vtkMRMLLinearTransformNode()
    probeTransform.SetName(probeText + 'Transform-%s' % entryPointFid.GetName())
    
    scene.AddNode(probeTransform)
    
    probeTransform.ApplyTransformMatrix(transform.GetMatrix())
    
    probeModel.SetAndObserveTransformNodeID(probeTransform.GetID())
    
    
class AblationZone:
  
  def __init__(self, entryPointFiducialListNode, targetFiducialListNode, shape, shapeRadius, shapeHeight, shapeVolume, ablationZoneColor):
    
    entryPointFid = entryPointFiducialListNode
    targetFid = targetFiducialListNode
    
    scene = slicer.mrmlScene
    
    
    if (shape == 'sphere'):
      source = vtk.vtkSphereSource()
      source.SetRadius(shapeRadius)
      source.Update()
    elif (shape == 'cylinder'):
      source = vtk.vtkCylinderSource()
      source.SetRadius(shapeRadius)
      source.SetHeight(shapeHeight)
      source.Update()
    elif (shape == 'ellipsoid'):
      source = vtk.vtkSphereSource()
      source.SetRadius(shapeRadius)
      source.Update()
    else:
      source = vtk.vtkSphereSource()
      source.SetRadius(shapeRadius)
      source.Update()
    
    
    # get coordinates from current entry point fiducial
    currentEntryPointFiducialCoordinatesRAS = [0, 0, 0]
    
    entryPointFid.GetFiducialCoordinates(currentEntryPointFiducialCoordinatesRAS)
    
    currentTargetFiducialCoordinatesRAS = [0, 0, 0]
    
    targetFid.GetFiducialCoordinates(currentTargetFiducialCoordinatesRAS)
    
    translationTarget = [currentTargetFiducialCoordinatesRAS[0], currentTargetFiducialCoordinatesRAS[1], currentTargetFiducialCoordinatesRAS[2]]

    # Generate a random start and end point
    random.seed(8775070)
    startPoint = [0 for i in range(3)]
    startPoint[0] = currentEntryPointFiducialCoordinatesRAS[0]
    startPoint[1] = currentEntryPointFiducialCoordinatesRAS[1]
    startPoint[2] = currentEntryPointFiducialCoordinatesRAS[2]
    endPoint = [0 for i in range(3)]
    endPoint[0] = currentTargetFiducialCoordinatesRAS[0]
    endPoint[1] = currentTargetFiducialCoordinatesRAS[1]
    endPoint[2] = currentTargetFiducialCoordinatesRAS[2]
     
    # Compute a basis
    normalizedX = [0 for i in range(3)]
    normalizedY = [0 for i in range(3)]
    normalizedZ = [0 for i in range(3)]
     
    # The X axis is a vector from start to end
    math = vtk.vtkMath()
    math.Subtract(endPoint, startPoint, normalizedX)
    # length = math.Norm(normalizedX)
    math.Normalize(normalizedX)
    
    # The Z axis is an arbitrary vector cross X
    arbitrary = [0 for i in range(3)]
    arbitrary[0] = random.uniform(-10,10)
    arbitrary[1] = random.uniform(-10,10)
    arbitrary[2] = random.uniform(-10,10)
    math.Cross(normalizedX, arbitrary, normalizedZ)
    math.Normalize(normalizedZ)
    
    # The Y axis is Z cross X
    math.Cross(normalizedZ, normalizedX, normalizedY)
    matrix = vtk.vtkMatrix4x4()
     
    # Create the direction cosine matrix
    matrix.Identity()
    for i in range(3):
      matrix.SetElement(i, 0, normalizedX[i])
      matrix.SetElement(i, 1, normalizedY[i])
      matrix.SetElement(i, 2, normalizedZ[i])
      matrix.SetElement(i, 3, currentTargetFiducialCoordinatesRAS[i])
      
    # Apply the transforms
    transform = vtk.vtkTransform()
    transform.Concatenate(matrix)
    transform.RotateZ(90)
    
        
    # Create model node
    lesionModel = slicer.vtkMRMLModelNode()
    lesionModel.SetScene(scene)
    lesionModel.SetName("Ablationzone-%s" % targetFid.GetName())
    lesionModel.SetAndObservePolyData(source.GetOutput())
    self.lesionModel = lesionModel
    # Create display node
    lesionModelDisplay = slicer.vtkMRMLModelDisplayNode()
    lesionModelDisplay.SetColor(ablationZoneColor)
    lesionModelDisplay.SetOpacity(0.4)
    lesionModelDisplay.SliceIntersectionVisibilityOn()
    
    lesionModelDisplay.SetScene(scene)
    scene.AddNode(lesionModelDisplay)
    lesionModel.SetAndObserveDisplayNodeID(lesionModelDisplay.GetID())

    
    # Add to scene
    lesionModelDisplay.SetPolyData(source.GetOutput())
    self.lesionModelDisplay = lesionModelDisplay
    self.lesionModel= lesionModel
    
    scene.AddNode(lesionModel)
    
    # Create ablationZoneTransform node
    ablationZoneTransform = slicer.vtkMRMLLinearTransformNode()
    ablationZoneTransform.SetName('AblationZoneTransform-%s' % targetFid.GetName())
    
    scene.AddNode(ablationZoneTransform)
    
    ablationZoneTransform.ApplyTransformMatrix(transform.GetMatrix())
    
    lesionModel.SetAndObserveTransformNodeID(ablationZoneTransform.GetID())
    
    self.ablationZoneTransform = ablationZoneTransform
    
  def setAblationZoneInvisible(self):
    scene = slicer.mrmlScene
    self.lesionModelDisplay.VisibilityOff()
    self.lesionModelDisplay.SliceIntersectionVisibilityOff()
    
    # self.lesionModel.UpdateScene(scene)
    self.lesionModelDisplay.UpdateScene(scene)
  
  def setAblationZoneVisible(self):
    scene = slicer.mrmlScene
    self.lesionModelDisplay.VisibilityOn()
    self.lesionModelDisplay.SliceIntersectionVisibilityOn()
    
    # self.lesionModel.UpdateScene(scene)
    self.lesionModelDisplay.UpdateScene(scene)    
  
  
class InsertionSphere:
  
  def __init__(self, targetFiducialListNode, radius):
    target = targetFiducialListNode
    
    scene = slicer.mrmlScene
    
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(radius)
    sphere.SetThetaResolution(20)
    sphere.SetPhiResolution(20)
    sphere.Update()

    # Create model node
    insertionRadiusModel = slicer.vtkMRMLModelNode()
    insertionRadiusModel.SetScene(scene)
    insertionRadiusModel.SetName("InsertionSphere-%s" % target.GetName())
    insertionRadiusModel.SetAndObservePolyData(sphere.GetOutput())

    # Create display node
    insertionRadiusModelDisplay = slicer.vtkMRMLModelDisplayNode()
    insertionRadiusModelDisplay.SetColor(0.8,0.8,0.8)
    insertionRadiusModelDisplay.SetOpacity(0.3)
    insertionRadiusModelDisplay.SliceIntersectionVisibilityOn()
    
    insertionRadiusModelDisplay.SetScene(scene)
    scene.AddNode(insertionRadiusModelDisplay)
    insertionRadiusModel.SetAndObserveDisplayNodeID(insertionRadiusModelDisplay.GetID())

    # Add to scene
    insertionRadiusModelDisplay.SetPolyData(sphere.GetOutput())
    
    scene.AddNode(insertionRadiusModel)
    
    # Create insertionRadiusTransform node
    insertionRadiusTransform = slicer.vtkMRMLLinearTransformNode()
    insertionRadiusTransform.SetName('InsertionRadiusTransform-%s' % target.GetName())
    
    scene.AddNode(insertionRadiusTransform)
    
    # Translation
    transformMatrix = vtk.vtkMatrix4x4()
    
    # get coordinates from current fiducial
    currentFiducialCoordinatesRAS = [0, 0, 0]
    
    target.GetFiducialCoordinates(currentFiducialCoordinatesRAS)
    
    transformMatrix.SetElement(0, 3, currentFiducialCoordinatesRAS[0])
    transformMatrix.SetElement(1, 3, currentFiducialCoordinatesRAS[1])
    transformMatrix.SetElement(2, 3, currentFiducialCoordinatesRAS[2])
    
    insertionRadiusTransform.ApplyTransformMatrix(transformMatrix)
    
    insertionRadiusModel.SetAndObserveTransformNodeID(insertionRadiusTransform.GetID())
    
    self.sphere = sphere
    self.insertionRadiusModel = insertionRadiusModel
    self.insertionRadiusModelDisplay = insertionRadiusModelDisplay
    self.insertionRadiusTransform = insertionRadiusTransform
  
  def disableInsertionSphere(self):
    scene = slicer.mrmlScene
    self.insertionRadiusModelDisplay.VisibilityOff()
    self.insertionRadiusModelDisplay.SliceIntersectionVisibilityOff()
    
class Device:
  def __init__(self, name, diameter, length, shape, shapeRadius, shapeHeight, shapeVolume):
    self.name = name
    self.diameter = diameter
    self.length = length
    self.shape = shape
    self.shapeRadius = shapeRadius
    self.shapeHeight = shapeHeight
    self.shapeVolume = shapeVolume


    