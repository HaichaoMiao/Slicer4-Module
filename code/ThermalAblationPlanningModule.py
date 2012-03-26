from __main__ import vtk, qt, ctk, slicer
from xml.dom.minidom import parseString


# ThermalAblationPlanningModule
#

class ThermalAblationPlanningModule:

  def __init__(self, parent):
    parent.title = "Thermal Ablation Planning"
    parent.category = "Ablation"
    parent.contributor = "Haichao Miao <hmiao87@gmail.com>"
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
    
    if not parent:
      self.setup()
      self.fiducialsNodeSelector.setMRMLScene(slicer.mrmlScene)

      self.parent.show()
      
    
  def setup(self):
    

    #
    # Probe Placement Planning Collapsible button
    #
    
    probePlacementPlanningCollapsibleButton = ctk.ctkCollapsibleButton()
    probePlacementPlanningCollapsibleButton.text = "Probe Placement Planning"
    self.layout.addWidget(probePlacementPlanningCollapsibleButton)
    
    formLayout = qt.QFormLayout(probePlacementPlanningCollapsibleButton)

    # ROI Placement
    
    roiPlacementGroupBox = qt.QGroupBox()
    roiPlacementGroupBox.setTitle("1: ROI Placement")
    self.roiPlacementGroupBox = roiPlacementGroupBox
    
    formLayout.addWidget(roiPlacementGroupBox)
    
    roiPlacementLayout = qt.QFormLayout(roiPlacementGroupBox)

    self.fiducialsNodeSelector = slicer.qMRMLNodeComboBox()
    self.fiducialsNodeSelector.objectName = "fiducialsNodeSelector"
    self.nodeTypes = ['vtkMRMLAnnotationHierarchyNode']
    self.fiducialsNodeSelector.baseName = "Target"
    self.fiducialsNodeSelector.noneEnabled = False
    self.fiducialsNodeSelector.addEnabled = False
    self.fiducialsNodeSelector.removeEnabled = False
    
    roiPlacementLayout.addRow("Target Point:", self.fiducialsNodeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.fiducialsNodeSelector, 'setMRMLScene(vtkMRMLScene*)')     
     
    
    
    # todo: value -> instance variable
    roiPlacementLineEdit = qt.QLineEdit()
    roiPlacementLineEdit.text = "100"
    self.roiPlacementLineEdit = roiPlacementLineEdit
    
    addInsertionRadiusButton = qt.QPushButton("Add Insertion Radius")
    addInsertionRadiusButton.toolTip = "Add Insertion Radius"
    
    addInsertionRadiusButton.connect('clicked(bool)', self.onAddInsertionRadiusButtonClicked)
    
    roiPlacementLayout.addRow(roiPlacementLineEdit, addInsertionRadiusButton)
    
    self.addInsertionRadiusButton = addInsertionRadiusButton
    
    # 2a: Point Selection

    pointSelectionGroupBox = qt.QGroupBox()
    pointSelectionGroupBox.setTitle("2a: Point Selection")
    self.pointSelectionGroupBox = pointSelectionGroupBox
    
    formLayout.addWidget(pointSelectionGroupBox)
    
    pointSelectionLayout = qt.QFormLayout(pointSelectionGroupBox)
    
    pointOneComboBox = slicer.qMRMLNodeComboBox()
    
    
    
    pointTwoComboBox = qt.QComboBox()
    
    # todo: fill with point selection
    self.pointOneComboBox = pointOneComboBox
    self.pointTwoComboBox = pointTwoComboBox
    
    pointSelectionLayout.addRow(pointOneComboBox, pointTwoComboBox)
    
    # 2b: Probe Placement
    
    probePlacementGroupBox = qt.QGroupBox()
    probePlacementGroupBox.setTitle("2b: Probe Placement")
    self.probePlacementGroupBox = probePlacementGroupBox
    
    formLayout.addWidget(probePlacementGroupBox)
    
    probePlacementLayout = qt.QFormLayout(probePlacementGroupBox)
    
    addProbeButton = qt.QPushButton("Add Probe")
    addProbeButton.toolTip = "Add Probe"
    self.addProbeButton = addProbeButton
    
    addProbeButton.connect('clicked(bool)', self.onAddProbeButtonClicked)
   
    probeLineEdit = qt.QLineEdit()
    # todo: value -> instance variable
    probeLineEdit.text = "Probe 1"
    
    self.probeLineEdit = probeLineEdit
    
    probePlacementLayout.addRow(addProbeButton, probeLineEdit)
    
    # 3: Ablation Zone Estimation
    
    ablationZoneEstimationGroupBox = qt.QGroupBox()
    ablationZoneEstimationGroupBox.setTitle("3: Ablation Zone Estimation")
    self.ablationZoneEstimationGroupBox = ablationZoneEstimationGroupBox
    
    formLayout.addWidget(ablationZoneEstimationGroupBox)
    
    ablationZoneEstimationLayout = qt.QFormLayout(ablationZoneEstimationGroupBox)
    
    
    
    devicesComboBox = qt.QComboBox()

    self.devices = ["Galil ICE Sphere", "Galil ICE Rod", "Galil ICE Seed", "Rita Stardust XL", "Radionics CoolTip", "Radionics Cluster Probe"]
    
    for device in self.devices:
      devicesComboBox.addItem(device)
    
    self.devicesComboBox = devicesComboBox
    
    drawAblationZoneButton = qt.QPushButton("Draw Ablation Zone")
    drawAblationZoneButton.toolTip = "Draw Ablation Zone"
    self.drawAblationZoneButton = drawAblationZoneButton
    
    drawAblationZoneButton.connect('clicked(bool)', self.onDrawAblationZoneButtonClicked)
    
    ablationZoneEstimationLayout.addRow("Select Device: ", devicesComboBox)
    ablationZoneEstimationLayout.addRow(drawAblationZoneButton)
    
  def onAddInsertionRadiusButtonClicked(self):
    currentValumeNode = self.inputVolumeNodeSelector.currentNode()
    currentTargetNode = self.fiducialsNodeSelector.currentNode()
    
    newModelNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelNode")
    newModelNode.SetScene(slicer.mrmlScene)
    newModelNode.SetName(slicer.mrmlScene.GetUniqueNameByString(self.outputModelNodeSelector.baseName))        
    slicer.mrmlScene.AddNode(newModelNode)
    currentModelNode = newModelNode
    self.outputModelNodeSelector.setCurrentNode(currentModelNode)        
    
  
  def onAddInsertionRadiusButtonClicked(self):
    print "Add Insertion Radius"
    
    file = open('/Users/haichao/git/Slicer4-Module/code/devices.xml', 'r')
    
    data = file.read()
    
    dom = parseString(data)
    
    xmlTag = dom.getElementsByTagName('devices')[0].toxml()
    
    xmlData = xmlTag.replace('<devices>','').replace('</devices>','')
    
    print xmlData
    
    model = TestSphere(self.fiducialsNodeSelector.currentNode())
    
  def onAddProbeButtonClicked(self):
    print "Add Probe"

  def onDrawAblationZoneButtonClicked(self):
    print "Draw Ablation Zone"

class TestSphere:
  
  def __init__(self, fiducialListNode):
    fids = fiducialListNode
    scene = slicer.mrmlScene

    # Create model node
    model = slicer.vtkMRMLModelNode()
    model.SetScene(scene)
    model.SetName("Path-%s" % fids.GetName())
    

    # Create display node
    modelDisplay = slicer.vtkMRMLModelDisplayNode()
    #modelDisplay.SetColor(1,1,0) # yellow
    modelDisplay.SetScene(scene)
    scene.AddNodeNoNotify(modelDisplay)
    model.SetAndObserveDisplayNodeID(modelDisplay.GetID())

    # Add to scene
    modelDisplay.SetPolyData(model.GetPolyData())
    scene.AddNode(model)

    # Camera cursor
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(100)
    sphere.Update()


    # Create model node
    cursor = slicer.vtkMRMLModelNode()
    cursor.SetScene(scene)
    cursor.SetName("Cursor-%s" % fids.GetName())
    cursor.SetAndObservePolyData(sphere.GetOutput())

    # Create display node
    cursorModelDisplay = slicer.vtkMRMLModelDisplayNode()
    cursorModelDisplay.SetColor(1,1,0) # red
    cursorModelDisplay.SetScene(scene)
    scene.AddNodeNoNotify(cursorModelDisplay)
    cursor.SetAndObserveDisplayNodeID(cursorModelDisplay.GetID())

    # Add to scene
    cursorModelDisplay.SetPolyData(sphere.GetOutput())
    scene.AddNode(cursor)

    # Create transform node
    transform = slicer.vtkMRMLLinearTransformNode()
    transform.SetName('Transform-%s' % fids.GetName())
    
    scene.AddNode(transform)
    cursor.SetAndObserveTransformNodeID(transform.GetID())
    
    # Translation
    transformMatrix = vtk.vtkMatrix4x4()
    transformMatrix.SetElement(0,3, 100)
    transformMatrix.SetElement(1,3, 100)
    
    transform.ApplyTransformMatrix(transformMatrix)
    
    self.transform = transform
    