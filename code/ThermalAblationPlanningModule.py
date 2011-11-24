from __main__ import vtk, qt, ctk, slicer

#
# ThermalAblationPlanningModule
#

class ThermalAblationPlanningModule:

  def __init__(self, parent):
    parent.title = "Thermal Ablation Planning"
    parent.category = "Ablation"
    parent.contributor = "Haichao Miao <hmiao87@gmail.com>"
    parent.helpText = """
    Slicer 4 module for planning a ablation procedure.
    For more information, read the README file.
    """
    parent.acknowledgementText = """
    This module was created by Haichao Miao as a part of his bachelor thesis under the guidance of Wolfgang Schramm, PhD 
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

    self.inputVolumeNodeSelector = slicer.qMRMLNodeComboBox()
    self.inputVolumeNodeSelector.objectName = 'inputVolumeNodeSelector'
    self.inputVolumeNodeSelector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.inputVolumeNodeSelector.noneEnabled = False
    self.inputVolumeNodeSelector.addEnabled = False
    self.inputVolumeNodeSelector.removeEnabled = False
    self.inputVolumeNodeSelector.addAttribute("vtkMRMLScalarVolumeNode", "LabelMap", "0")    
    roiPlacementLayout.addRow("Input Volume:", self.inputVolumeNodeSelector)
    self.parent.connect('mrmlSceneChanged(vtkMRMLScene*)',
                        self.inputVolumeNodeSelector, 'setMRMLScene(vtkMRMLScene*)')
    #self.inputVolumeNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputVolumeChanged)
    #self.inputVolumeNodeSelector.connect('nodeActivated(vtkMRMLNode*)', self.onInputVolumeChanged)
    

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
    
    
  def onAddProbeButtonClicked(self):
    print "Add Probe"

  def onDrawAblationZoneButtonClicked(self):
    print "Draw Ablation Zone"
