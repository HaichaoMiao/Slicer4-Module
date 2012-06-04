from __main__ import vtk, qt, ctk, slicer
import xml.dom.minidom
import random

# when moving the sphere, the 2d does not update
# placement of a ROI around of the tumor
# labeling of probes in the 3D View
# ablation zones are always spheres?
# label maps?

# ThermalAblationPlanningModule
#

# only test data
document = """\
<devices>
    <device>
        <name>Galil ICE Seed</name>
        <diameter>12</diameter>
        <length>130</length>
        <ablationzone_shape>
            <volume>15</volume>
        </ablationzone_shape>
    </device>
    <device>
        <name>Galil ICE Rod</name>
        <diameter>8</diameter>
        <length>120</length>
        <ablationzone_shape>
            <volume>20</volume>
        </ablationzone_shape>
    </device>
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
    
    for num, elem in enumerate(dom.getElementsByTagName("device")):
      for node in elem.getElementsByTagName("name"):
          name = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("diameter"):
          diameter = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("length"):
          length = node.childNodes[0].nodeValue
      for node in elem.getElementsByTagName("volume"):
          volume = node.childNodes[0].nodeValue
      
      self.devices.append(device(name, int(diameter), int(length), int(volume)))
  
  def onPlaceProbeButtonClicked(self):
    
    drawProbe(self.entryPointFiducialsNodeSelector.currentNode(), self.targetFiducialsNodeSelector.currentNode(), self.devices[self.devicesComboBox.currentIndex].length, self.devices[self.devicesComboBox.currentIndex].diameter)
    
    self.probeCnt = self.probeCnt + 1
      
    self.probeNameLineEdit.setText('Probe ' + str(self.probeCnt))
    
  def onDrawAblationZoneButtonClicked(self):
      
      drawAblationZoneSphere(self.targetFiducialsNodeSelector.currentNode(), self.devices[self.devicesComboBox.currentIndex].volume) 

class drawProbe:
    
  def __init__(self, entryPointFiducialListNode, targetFiducialListNode, length, diameter):
    
    entryPointFid = entryPointFiducialListNode
    targetFid = targetFiducialListNode
    scene = slicer.mrmlScene
    
    probe = vtk.vtkCylinderSource()
    probe.SetRadius(diameter / 2)
    probe.SetHeight(length)
    
    probe.Update()
    
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
    '''
    
    probeModel = slicer.vtkMRMLModelNode()
    probeModel.SetScene(scene)
    probeModel.SetName("Probe")
    probeModel.SetAndObservePolyData(probe.GetOutput())
    
    probeModelDisplay = slicer.vtkMRMLModelDisplayNode()
    probeModelDisplay.SetColor(2, 2, 2)
    probeModelDisplay.SliceIntersectionVisibilityOn()
    probeModelDisplay.SetScene(scene)
    scene.AddNode(probeModelDisplay)
    probeModel.SetAndObserveDisplayNodeID(probeModelDisplay.GetID())

    probeModelDisplay.SetPolyData(probe.GetOutput())
    
    scene.AddNode(probeModel)
    
    # Create probeTransform node
    probeTransform = slicer.vtkMRMLLinearTransformNode()
    probeTransform.SetName('Transform-%s' % entryPointFid.GetName())
    
    scene.AddNode(probeTransform)
    
    # Translation
    transformMatrix = vtk.vtkMatrix4x4()
    
    # get coordinates from current fiducial
    currentFiducialCoordinatesRAS = [0, 0, 0]
    
    entryPointFid.GetFiducialCoordinates(currentFiducialCoordinatesRAS)
    
    transformMatrix.SetElement(0, 3, currentFiducialCoordinatesRAS[0])
    transformMatrix.SetElement(1, 3, currentFiducialCoordinatesRAS[1])
    transformMatrix.SetElement(2, 3, currentFiducialCoordinatesRAS[2])
    
    probeTransform.ApplyTransformMatrix(transformMatrix)
    
    probeModel.SetAndObserveTransformNodeID(probeTransform.GetID())
    
    # test 
    
    USER_MATRIX = False
    
    #Create an arrow.
    cylinder = vtk.vtkArrowSource()
    # cylinder.SetHeight(3)
    # cylinder.SetRadius(2)
    
    # Generate a random start and end point
    random.seed(8775070)
    startPoint = [0 for i in range(3)]
    startPoint[0] = random.uniform(-10,10)
    startPoint[1] = random.uniform(-10,10)
    startPoint[2] = random.uniform(-10,10)
    endPoint = [0 for i in range(3)]
    endPoint[0] = random.uniform(-10,10)
    endPoint[1] = random.uniform(-10,10)
    endPoint[2] = random.uniform(-10,10)
     
    # Compute a basis
    normalizedX = [0 for i in range(3)]
    normalizedY = [0 for i in range(3)]
    normalizedZ = [0 for i in range(3)]
     
    # The X axis is a vector from start to end
    math = vtk.vtkMath()
    math.Subtract(endPoint, startPoint, normalizedX)
    length = math.Norm(normalizedX)
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
    transform.Translate(startPoint)
    transform.Concatenate(matrix)
    transform.Scale(length, length, length)
     
    # Transform the polydata
    transformPD = vtk.vtkTransformPolyDataFilter()
    transformPD.SetTransform(transform)
    transformPD.SetInputConnection(cylinder.GetOutputPort())
     
    #Create a mapper and actor for the arrow
    mapper = vtk.vtkPolyDataMapper()
    actor = vtk.vtkActor()
     
    if USER_MATRIX:
        mapper.SetInputConnection(cylinder.GetOutputPort())
        actor.SetUserMatrix(transform.GetMatrix())
    else:
        mapper.SetInputConnection(transformPD.GetOutputPort())
     
    actor.SetMapper(mapper)
     
    # Create spheres for start and end point
    sphereStartSource = vtk.vtkSphereSource()
    sphereStartSource.SetCenter(startPoint)
    sphereStartMapper = vtk.vtkPolyDataMapper()
    sphereStartMapper.SetInputConnection(sphereStartSource.GetOutputPort())
    sphereStart = vtk.vtkActor()
    sphereStart.SetMapper(sphereStartMapper)
    sphereStart.GetProperty().SetColor(1.0, 1.0, .3)
     
    sphereEndSource = vtk.vtkSphereSource()
    sphereEndSource.SetCenter(endPoint)
    sphereEndMapper = vtk.vtkPolyDataMapper()
    sphereEndMapper.SetInputConnection(sphereEndSource.GetOutputPort())
    sphereEnd = vtk.vtkActor()
    sphereEnd.SetMapper(sphereEndMapper)
    sphereEnd.GetProperty().SetColor(1.0, .3, .3)
    
    
    # Create model node
    model1 = slicer.vtkMRMLModelNode()
    model1.SetScene(scene)
    model1.SetName("model1-%s" % targetFid.GetName())
    model1.SetAndObservePolyData(sphereStartSource.GetOutput())

    # Create display node
    model1display = slicer.vtkMRMLModelDisplayNode()
    model1display.SetColor(0,100,0)
    model1display.SetOpacity(1)
    model1display.SliceIntersectionVisibilityOn()
    
    model1display.SetScene(scene)
    scene.AddNode(model1display)
    model1.SetAndObserveDisplayNodeID(model1display.GetID())

    # Add to scene
    model1display.SetPolyData(sphereStartSource.GetOutput())
    
    scene.AddNode(model1)
    
    model2 = slicer.vtkMRMLModelNode()
    
    # Create model node
    model2 = slicer.vtkMRMLModelNode()
    model2.SetScene(scene)
    model2.SetName("model2-%s" % targetFid.GetName())
    model2.SetAndObservePolyData(sphereEndSource.GetOutput())

    # Create display node
    model2display = slicer.vtkMRMLModelDisplayNode()
    model2display.SetColor(0,100,0)
    model2display.SetOpacity(1)
    model2display.SliceIntersectionVisibilityOn()
    
    model2display.SetScene(scene)
    scene.AddNode(model2display)
    model2.SetAndObserveDisplayNodeID(model2display.GetID())

    # Add to scene
    model2display.SetPolyData(sphereEndSource.GetOutput())
    
    scene.AddNode(model2)
    
    # Create model node
    model3 = slicer.vtkMRMLModelNode()
    model3.SetScene(scene)
    model3.SetName("model3-%s" % targetFid.GetName())
    model3.SetAndObservePolyData(cylinder.GetOutput())

    # Create display node
    model3display = slicer.vtkMRMLModelDisplayNode()
    model3display.SetColor(0,100,0)
    model3display.SetOpacity(1)
    model3display.SliceIntersectionVisibilityOn()
    
    model3display.SetScene(scene)
    scene.AddNode(model3display)
    model3.SetAndObserveDisplayNodeID(model3display.GetID())

    # Add to scene
    model3display.SetPolyData(cylinder.GetOutput())
    
    scene.AddNode(model3)
    
    
    # Create probeTransform node
    cylinderTransform = slicer.vtkMRMLLinearTransformNode()
    cylinderTransform.SetName('Cylinder-%s' % entryPointFid.GetName())
    
    scene.AddNode(cylinderTransform)
    
    cylinderTransform.ApplyTransformMatrix(transform.GetMatrix())
    
    model3.SetAndObserveTransformNodeID(cylinderTransform.GetID())
    
    '''''
    #Create a renderer, render window, and interactor
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
     
    #Add the actor to the scene
    renderer.AddActor(actor)
    renderer.AddActor(sphereStart)
    renderer.AddActor(sphereEnd)
    renderer.SetBackground(.1, .2, .3) # Background color dark blue
     
     
    #Render and interact
    renderWindow.Render()
    renderWindowInteractor.Start()
    '''
class drawAblationZoneSphere:
  
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
    lesionModelDisplay.SetColor(200,0,0)
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
    ablationZoneTransform.SetName('Transform-%s' % target.GetName())
    
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
    
    
    

class device:
  def __init__(self, name, diameter, length, volume):
    self.name = name
    self.diameter = diameter
    self.length = length
    self.volume = volume