class Probe:
    
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
    
    '''
    ps = vtk.vtkProgrammableSource()
    
    import math 
    numPts = 80
    polyLinePoints = vtk.vtkPoints() 
    polyLinePoints.SetNumberOfPoints(numPts) 
    R=1.0 
    for i in range(0,numPts):
      x = R*math.cos(i*2*math.pi/numPts) 
      y = R*math.sin(i*2*math.pi/numPts) 
      polyLinePoints.InsertPoint(i, x, y, 0)
    aPolyLine1 = vtk.vtkPolyLine() 
    aPolyLine1.GetPointIds().SetNumberOfIds(numPts+1) 
    for i in range(0,numPts):
      aPolyLine1.GetPointIds().SetId(i,i) 
    # add one more cell at the end to close the circle on itself 
    aPolyLine1.GetPointIds().SetId(numPts, 0)
    aPolyLineGrid = ps.GetOutput()
    aPolyLineGrid.Allocate(1,1)
    aPolyLineGrid.InsertNextCell(aPolyLine1.GetCellType(), aPolyLine1.GetPointIds())
    aPolyLineGrid.SetPoints(polyLinePoints)
    '''
    
    '''
    #This script generates a helix double.
    #This is intended as the script of a 'Programmable Source'
    import math
     
    ps = vtk.vtkSphereSource()
    
    
    numPts = 80 # Points along each Helix
    length = 8 # Length of each Helix
    rounds = 3 # Number of times around
    phase_shift = math.pi/1.5 # Phase shift between Helixes
     
    #Get a vtk.PolyData object for the output
    pdo = ps.GetOutput()
    print "before"
    print pdo
    
    #This will store the points for the Helix
    newPts = vtk.vtkPoints()
    for i in range(0, numPts):
       #Generate Points for first Helix
       x = i*length/numPts
       y = math.sin(i*rounds*2*math.pi/numPts)
       z = math.cos(i*rounds*2*math.pi/numPts)
       newPts.InsertPoint(i, x,y,z)
     
       #Generate Points for second Helix. Add a phase offset to y and z.
       y = math.sin(i*rounds*2*math.pi/numPts+phase_shift)
       z = math.cos(i*rounds*2*math.pi/numPts+phase_shift)
       #Offset Helix 2 pts by 'numPts' to keep separate from Helix 1 Pts
       newPts.InsertPoint(i+numPts, x,y,z)
     
    #Add the points to the vtkPolyData object
    pdo.SetPoints(newPts)
     
    #Make two vtkPolyLine objects to hold curve construction data
    aPolyLine1 = vtk.vtkPolyLine()
    aPolyLine2 = vtk.vtkPolyLine()
     
    #Indicate the number of points along the line
    aPolyLine1.GetPointIds().SetNumberOfIds(numPts)
    aPolyLine2.GetPointIds().SetNumberOfIds(numPts)
    for i in range(0,numPts):
       #First Helix - use the first set of points
       aPolyLine1.GetPointIds().SetId(i, i)
       #Second Helix - use the second set of points
       #(Offset the point reference by 'numPts').
       aPolyLine2.GetPointIds().SetId(i,i+numPts)
     
    #Allocate the number of 'cells' that will be added. 
    #Two 'cells' for the Helix curves, and one 'cell'
    #for every 3rd point along the Helixes.
    links = range(0,numPts,3)
    pdo.Allocate(2+len(links), 1)
     
    #Add the poly line 'cell' to the vtkPolyData object.
    pdo.InsertNextCell(aPolyLine1.GetCellType(), aPolyLine1.GetPointIds())
    pdo.InsertNextCell(aPolyLine2.GetCellType(), aPolyLine2.GetPointIds())
     
    for i in links:
       #Add a line connecting the two Helixes.
       aLine = vtk.vtkLine()
       aLine.GetPointIds().SetId(0, i)
       aLine.GetPointIds().SetId(1, i+numPts)
       pdo.InsertNextCell(aLine.GetCellType(), aLine.GetPointIds())
       
    print "after"
    print pdo
    '''    
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
    