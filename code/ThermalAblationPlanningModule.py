from __main__ import vtk, qt, ctk, slicer

#
# ThermalAblationPlanningModule
#

class ThermalAblationPlanningModule:
  def __init__(self, parent):
    parent.title = "Thermal Ablation Planning"
    parent.category = "Thermal Ablation"
    parent.contributor = "Haichao Miao <hmiao87@gmail.com>"
    parent.helpText = """
    Slicer 4 module for planning a ablation procedure.
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
      self.parent.show()
    
  def setup(self):
    # Instantiate and connect widgets ...
    
    # Probe Placement Planning Collapsible button
    probePlacementPlanningCollapsibleButton = ctk.ctkCollapsibleButton()
    probePlacementPlanningCollapsibleButton.text = "Probe Placement Planning"
    self.layout.addWidget(probePlacementPlanningCollapsibleButton)
    

    formLayout = qt.QFormLayout(probePlacementPlanningCollapsibleButton)
    

    # Apply button
    applyButton = qt.QPushButton("Apply")
    applyButton.toolTip = "Execute the placement of the probe"
    formLayout.addWidget(applyButton)
    applyButton.connect('clicked(bool)', self.onApplyButtonClicked)
    
    
    
    # Set local var as instance attribute
    self.applyButton = applyButton
    
    # Default Button
    defaultButton = qt.QPushButton("Default")
    defaultButton.toolTip = "Reset the parameters to default"
    formLayout.addWidget(defaultButton)
    defaultButton.connect('clicked(bool)', self.onDefaultButtonClicked)
    
    self.defaultButton = defaultButton
    
    
  def onApplyButtonClicked(self):
    print "Apply Button clicked!"
    
  def onDefaultButtonClicked(self):
    print "Default Button clicked!"

