import sys, ifcopenshell, ifcopenshell.util.element

def create_ifc(file_path='output/model.ifc'):
    # Create a new IFC file with basic structure
    ifc = ifcopenshell.file(schema='IFC4')
    # Project
    project = ifc.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), Name='Data Hall Project')
    site = ifc.create_entity('IfcSite', GlobalId=ifcopenshell.guid.new(), Name='Site')
    building = ifc.create_entity('IfcBuilding', GlobalId=ifcopenshell.guid.new(), Name='Data Hall')
    storey = ifc.create_entity('IfcBuildingStorey', GlobalId=ifcopenshell.guid.new(), Name='Ground Floor', Elevation=0.0)
    # Relate hierarchy
    ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=project, RelatedObjects=[site])
    ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=site, RelatedObjects=[building])
    ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=building, RelatedObjects=[storey])
    # Simple placeholder rack
    rack = ifc.create_entity('IfcFurniture', GlobalId=ifcopenshell.guid.new(), Name='Rack 1', ObjectType='Rack')
    # Placement at origin
    placement = ifc.create_entity('IfcLocalPlacement', PlacementRelTo=None,
                                  RelativePlacement=ifc.create_entity('IfcAxis2Placement3D',
                                    Location=ifc.create_entity('IfcCartesianPoint', (0.0,0.0,0.0)),
                                    Axis=ifc.create_entity('IfcDirection', (0.0,0.0,1.0)),
                                    RefDirection=ifc.create_entity('IfcDirection', (1.0,0.0,0.0))))
    rack.ObjectPlacement = placement
    # Add to storey
    ifc.create_entity('IfcRelContainedInSpatialStructure', GlobalId=ifcopenshell.guid.new(),
                      RelatingStructure=storey, RelatedElements=[rack])
    # Write file
    ifc.write(file_path)

if __name__ == '__main__':
    out_path = sys.argv[1] if len(sys.argv) > 1 else 'output/model.ifc'
    create_ifc(out_path)
