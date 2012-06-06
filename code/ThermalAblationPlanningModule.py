from __main__ import vtk, qt, ctk, slicer
import xml.dom.minidom
import random
from math import sqrt, pow, asin, sin, acos, cos

# placement of a ROI around of the tumor
# labeling of probes in the 3D View
# ablation zones are always spheres?
# label maps?
# relative paths depends on the slicer app, not the module

# ThermalAblationPlanningModule
#

# only test data
document = """\
<devices>
    <Device>
        <name>Galil ICE Seed</name>
        <diameter>5</diameter>
        <length>150</length>
        <ablationzone_shape>
            <volume>15</volume>
        </ablationzone_shape>
    </Device>
    <Device>
        <name>Galil ICE Rod</name>
        <diameter>8</diameter>
        <length>120</length>
        <ablationzone_shape>
            <volume>20</volume>
        </ablationzone_shape>
    </Device>
</devices>
"""

class ThermalAblationPlanningModule:

  def __init__(self, parent):
      
    parent.title = "Thermal Ablation Planning"
    parent.categories = ["Ablation"]
    parent.dependencies = []
    parent.contributors = ["Haichao Miao <hmiao87@gmail.com>"]
    parent.helpText = """
    Slicer 4 module for planning a thermal ablation procedure.
    For more information, read the README file.
    """
    parent.acknowledgementText = """
    This module was created by Haichao Miao as a part of his bachelor thesis under the guidance of Dr. Wolfgang Schramm 
    at the Vienna University of Technology.
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
    self.transform = None
    
    if not parent:
      self.setup()
      self.entryPointFiducialsNodeSelector.setMRMLScene(slicer.mrmlScene)

      self.parent.show()
      
    
  def setup(self):
    

    #
    # Probe Placement Planning Collapsible button
    #
    
    probePlacementPlanningCollapsibleButton = ctk.ctkCollapsibleButton()
    probePlacementPlanningCollapsibleButton.text = "Probe Placement Planning"
    self.layout.addWidget(probePlacementPlanningCollapsibleButton)
    
    formLayout = qt.QFormLayout(probePlacementPlanningCollapsibleButton)


    # 0: Insertion Radius
    
    insertionRadiusGroupBox = qt.QGroupBox()
    insertionRadiusGroupBox.setTitle("0: Placement of ROI")
    self.insertionRadiusGroupBox = insertionRadiusGroupBox
    
    formLayout.addWidget(insertionRadiusGroupBox)
    
    insertionRadiusLayout = qt.QGridLayout(insertionRadiusGroupBox)
    
    radiusHorizontalSlider = qt.QSlider()
    radiusHorizontalSlider.setOrientation(1)
    radiusHorizontalSlider.setMaximum(300)
    radiusHorizontalSlider.setValue(100)
    radiusHorizontalSlider.setPageStep(1)
    
    self.radiusHorizontalSlider = radiusHorizontalSlider
    
    
    self.radiusHorizontalSlider.connect('valueChanged(int)', self.sliderValueChanged)
    insertionRadiusLabel = qt.QLabel()
    insertionRadiusLabel.setText(radiusHorizontalSlider.value)
    
    self.insertionRadiusLabel = insertionRadiusLabel
    
    self.targetTumorFiducialsNodeSelector = slicer.qMRMLNodeComboBox()
    self.targetTumorFiducialsNodeSelector.objectName = "targetTumorFiducialsNodeSelector"
    self.targetTumorFiducialsNodeSelector.nodeTypes = ['vtkMRMLAnnotationFiducialNode']
    self.targetTumorFiducialsNodeSelector.baseName = "Target Tumor"
    self.targetTumorFiducialsNodeSelector.noneEnabled = False
    self.targetTumorFiducialsNodeSelector.addEnabled = False
    self.targetTumorFiducialsNodeSelector.removeEnabled = False
    
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.targetTumorFiducialsNodeSelector, 'setMRMLScene(vtkMRMLScene*)')  
    
    addInsertionRadiusButton = qt.QPushButton("Add Insertion Radius")
    addInsertionRadiusButton.toolTip = "Add Insertion Radius"
    self.addInsertionRadiusButton = addInsertionRadiusButton
    
    insertionRadiusLayout.addWidget(radiusHorizontalSlider, 1, 1)
    insertionRadiusLayout.addWidget(insertionRadiusLabel, 1, 2)
    insertionRadiusLayout.addWidget(self.targetTumorFiducialsNodeSelector, 1, 3)
    insertionRadiusLayout.addWidget(addInsertionRadiusButton, 1, 4)

    addInsertionRadiusButton.connect('clicked(bool)', self.onAddInsertionRadiusButtonClicked)
    
    
    
    # 1: Device Selection
    
    deviceSelectionGroupBox = qt.QGroupBox()
    deviceSelectionGroupBox.setTitle("1: Device Selection")
    self.deviceSelectionGroupBox = deviceSelectionGroupBox
    
    formLayout.addWidget(deviceSelectionGroupBox)
    
    deviceSelectionLayout = qt.QFormLayout(deviceSelectionGroupBox)
    
    devicesComboBox = qt.QComboBox()

    self.parseDevices()
    
    for device in self.devices:
      devicesComboBox.addItem(device.name)
      
      
    self.devicesComboBox = devicesComboBox
    
    deviceSelectionLayout.addRow("Select Device: ", devicesComboBox)
    
    # self.devicesComboBox.connect('currentIndexChanged(int)', self.onDeviceComboBoxChanged)
    
    # Probe Placement
    
    probePlacementGroupBox = qt.QGroupBox()
    probePlacementGroupBox.setTitle("2: Probe Placement")
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
    
    placeProbeButton = qt.QPushButton("Place Probe")
    placeProbeButton.toolTip = "Place Probe"
    self.placeProbeButton = placeProbeButton
    
    placeProbeButton.connect('clicked(bool)', self.onPlaceProbeButtonClicked)
    
    self.probeNameLineEdit = qt.QLineEdit()
    
    self.probeCnt = 1
    
    self.probeNameLineEdit.text = 'Probe ' + str(self.probeCnt)
    
    probePlacementLayout.addRow(self.probeNameLineEdit, placeProbeButton)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.probeNameLineEdit, 'setMRMLScene(vtkMRMLScene*)')  
    
    
    # 3: Draw Ablation Zone

    drawAblationZoneGroupBox = qt.QGroupBox()
    drawAblationZoneGroupBox.setTitle("3: Draw Ablation Zone")
    self.drawAblationZoneGroupBox = drawAblationZoneGroupBox
    
    formLayout.addWidget(drawAblationZoneGroupBox)
    
    drawAblationZoneLayout = qt.QFormLayout(drawAblationZoneGroupBox)
    
    drawAblationZoneButton = qt.QPushButton("Draw Ablation Zone")
    drawAblationZoneButton.toolTip = "Draw Ablation Zone"
    self.drawAblationZoneButton = drawAblationZoneButton
    
    drawAblationZoneButton.connect('clicked(bool)', self.onDrawAblationZoneButtonClicked)
    
    drawAblationZoneLayout.addRow(drawAblationZoneButton)
    
  def parseDevices(self):
    
    dom = xml.dom.minidom.parseString(document)
    
    self.devices = []
    
    for num, elem in enumerate(dom.getElementsByTagName("Device")):
      for node in elem.getElementsByTagName("name"):
          name = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("diameter"):
          diameter = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("length"):
          length = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("volume"):
          volume = node.childNodes[0].nodeValue
      
      self.devices.append(Device(name, int(diameter), int(length), int(volume)))
  
  
  def onAddInsertionRadiusButtonClicked(self):
    
    self.insertionSphere = InsertionSphere(self.targetTumorFiducialsNodeSelector.currentNode(), self.radiusHorizontalSlider.value)
    
    
  def sliderValueChanged(self):
    scene = slicer.mrmlScene
    self.insertionRadiusLabel.setText(self.radiusHorizontalSlider.value)
    self.insertionSphere.sphere.SetRadius(self.radiusHorizontalSlider.value)
    self.insertionSphere.sphere.Update
    self.insertionSphere.insertionRadiusModel.UpdateScene(scene)
    self.insertionSphere.insertionRadiusModelDisplay.UpdateScene(scene)
    
    
    
  def onPlaceProbeButtonClicked(self):
    
    
    self.probeCnt = self.probeCnt + 1
    
    # alternating colors for the probes
    self.probeColor = [[50, 50, 0], [50, 0, 50], [0, 50, 50], [0, 0, 50], [0, 50, 0]]
    
    probeText = 'Probe ' + str(self.probeCnt)
      
    self.probeNameLineEdit.setText(probeText)
    
    drawProbe(self.entryPointFiducialsNodeSelector.currentNode(), self.targetFiducialsNodeSelector.currentNode(), self.devices[self.devicesComboBox.currentIndex].length, self.devices[self.devicesComboBox.currentIndex].diameter, probeText, self.probeColor[self.probeCnt%5])
    
    self.insertionSphere.deleteInsertionSphere()
    
  def onDrawAblationZoneButtonClicked(self):
      
      AblationZoneSphere(self.targetFiducialsNodeSelector.currentNode(), self.devices[self.devicesComboBox.currentIndex].volume) 

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
    
    
    '''
    # Create the axes and the associated mapper and actor.   
    axes = vtk.vtkAxes()   
    axes.SetOrigin(0, 0, 0)   
    axesMapper = vtk.vtkPolyDataMapper()   
    axesMapper.SetInputConnection(axes.GetOutputPort())   
    axesActor = vtk.vtkActor()   
    axesActor.SetMapper(axesMapper)   
       
    # Create the 3D text and the associated mapper and follower (a type of   
    # actor).  Position the text so it is displayed over the origin of the   
    # axes.   
    atext = vtk.vtkVectorText()   
    atext.SetText("Origin")   
    textMapper = vtk.vtkPolyDataMapper()   
    textMapper.SetInputConnection(atext.GetOutputPort())   
    textActor = vtk.vtkFollower()   
    textActor.SetMapper(textMapper)   
    textActor.SetScale(0.2, 0.2, 0.2)   
    textActor.AddPosition(0, -0.1, 0)   
       
    
    # Create the Renderer, RenderWindow, and RenderWindowInteractor.   
    ren = vtk.vtkRenderer()   
    renWin = vtk.vtkRenderWindow()   
    renWin.AddRenderer(ren)   
    iren = vtk.vtkRenderWindowInteractor()   
    iren.SetRenderWindow(renWin)   
       
    # Add the actors to the renderer.   
    ren.AddActor(axesActor)   
    ren.AddActor(textActor)   
       
    # Zoom in closer.   
    ren.ResetCamera()   
    ren.GetActiveCamera().Zoom(1.6)   
       
    # Reset the clipping range of the camera; set the camera of the   
    # follower; render.   
    ren.ResetCameraClippingRange()   
    textActor.SetCamera(ren.GetActiveCamera())   
       
    iren.Initialize()   
    renWin.Render()   
    iren.Start() 
    
    
    # Labeling the Probe
    
    probeLabelModel = slicer.vtkMRMLModelNode()
    probeLabelModel.SetScene(scene)
    probeLabelModel.SetName(probeText + 'Label')
    probeLabelModel.SetAndObservePolyData(atext.GetOutput())
    
    probeLabelModelDisplay = slicer.vtkMRMLModelDisplayNode()
    probeLabelModelDisplay.SetScene(scene)
    
    scene.AddNode(probeLabelModelDisplay)
    
    probeLabelModel.SetAndObserveDisplayNodeID(probeLabelModelDisplay.GetID())
    
    probeLabelModelDisplay.SetPolyData(atext.GetOutput())
    
    scene.AddNode(probeLabelModel)
    
    '''
    
class AblationZoneSphere:
  
  def __init__(self, targetFiducialListNode, volume):
    target = targetFiducialListNode
    
    scene = slicer.mrmlScene
    
    # Camera lesionModel
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(volume)
    sphere.Update()

    # Create model node
    lesionModel = slicer.vtkMRMLModelNode()
    lesionModel.SetScene(scene)
    lesionModel.SetName("Ablationzone-%s" % target.GetName())
    lesionModel.SetAndObservePolyData(sphere.GetOutput())

    # Create display node
    lesionModelDisplay = slicer.vtkMRMLModelDisplayNode()
    lesionModelDisplay.SetColor(100,0,0)
    lesionModelDisplay.SetOpacity(0.4)
    lesionModelDisplay.SliceIntersectionVisibilityOn()
    
    lesionModelDisplay.SetScene(scene)
    scene.AddNode(lesionModelDisplay)
    lesionModel.SetAndObserveDisplayNodeID(lesionModelDisplay.GetID())

    # Add to scene
    lesionModelDisplay.SetPolyData(sphere.GetOutput())
    
    scene.AddNode(lesionModel)
    
    # Create ablationZoneTransform node
    ablationZoneTransform = slicer.vtkMRMLLinearTransformNode()
    ablationZoneTransform.SetName('AblationZoneTransform-%s' % target.GetName())
    
    scene.AddNode(ablationZoneTransform)
    
    # Translation
    transformMatrix = vtk.vtkMatrix4x4()
    
    # get coordinates from current fiducial
    currentFiducialCoordinatesRAS = [0, 0, 0]
    
    target.GetFiducialCoordinates(currentFiducialCoordinatesRAS)
    
    transformMatrix.SetElement(0, 3, currentFiducialCoordinatesRAS[0])
    transformMatrix.SetElement(1, 3, currentFiducialCoordinatesRAS[1])
    transformMatrix.SetElement(2, 3, currentFiducialCoordinatesRAS[2])
    
    ablationZoneTransform.ApplyTransformMatrix(transformMatrix)
    
    lesionModel.SetAndObserveTransformNodeID(ablationZoneTransform.GetID())
    
    self.ablationZoneTransform = ablationZoneTransform
    

class InsertionSphere:
  
  def __init__(self, targetFiducialListNode, radius):
    target = targetFiducialListNode
    
    scene = slicer.mrmlScene
    
    # Camera lesionModel
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(radius)
    sphere.Update()

    # Create model node
    insertionRadiusModel = slicer.vtkMRMLModelNode()
    insertionRadiusModel.SetScene(scene)
    insertionRadiusModel.SetName("Ablationzone-%s" % target.GetName())
    insertionRadiusModel.SetAndObservePolyData(sphere.GetOutput())

    # Create display node
    insertionRadiusModelDisplay = slicer.vtkMRMLModelDisplayNode()
    insertionRadiusModelDisplay.SetColor(10,10,10)
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
  
  def deleteInsertionSphere(self):
    self.insertionRadiusModelDisplay.VisibilityOff()
    self.insertionRadiusModelDisplay.SliceIntersectionVisibilityOff()
    
    
class Device:
  def __init__(self, name, diameter, length, volume):
    self.name = name
    self.diameter = diameter
    self.length = length
    self.volume = volume