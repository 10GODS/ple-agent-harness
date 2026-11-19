import sys, ifcopenshell, ifcopenshell.util.element

def create_ifc(filepath='output/model.ifc'):
    # Create a new IFC file with IFC4 schema
    ifc = ifcopenshell.file(schema='IFC4')
    # Project
    project = ifc.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), Name='DataHallProject')
    # Units in millimetres
    unit = ifc.create_entity('IfcUnitAssignment', Units=[
        ifc.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE', Prefix='MILLI'),
        ifc.create_entity('IfcSIUnit', UnitType='AREAUNIT', Name='SQUARE_METRE'),
        ifc.create_entity('IfcSIUnit', UnitType='VOLUMEUNIT', Name='CUBIC_METRE')
    ])
    project.UnitsInContext = unit
    # Site
    site = ifc.create_entity('IfcSite', GlobalId=ifcopenshell.guid.new(), Name='Site')
    # Building
    building = ifc.create_entity('IfcBuilding', GlobalId=ifcopenshell.guid.new(), Name='DataHall')
    # Storey
    storey = ifc.create_entity('IfcBuildingStorey', GlobalId=ifcopenshell.guid.new(), Name='Level 0')
    # Relate
    ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=project, RelatedObjects=[site])
    ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=site, RelatedObjects=[building])
    ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=building, RelatedObjects=[storey])
    # Dummy rack as IfcFurniture
    rack = ifc.create_entity('IfcFurniture', GlobalId=ifcopenshell.guid.new(), Name='Rack1', ObjectPlacement=ifc.create_entity('IfcLocalPlacement'))
    # Assign property set
    pset = ifc.create_entity('IfcPropertySet', GlobalId=ifcopenshell.guid.new(), Name='Pset_DCM_Rack')
    prop = ifc.create_entity('IfcPropertySingleValue', Name='Rows', NominalValue=ifc.create_entity('IfcInteger', 1))
    pset.HasProperties = [prop]
    ifc.create_entity('IfcRelDefinesByProperties', GlobalId=ifcopenshell.guid.new(), RelatedObjects=[rack], RelatingPropertyDefinition=pset)
    # Add rack to storey
    ifc.create_entity('IfcRelContainedInSpatialStructure', GlobalId=ifcopenshell.guid.new(), RelatedElements=[rack], RelatingStructure=storey)
    # Write file
    ifc.write(filepath)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'output/model.ifc'
    create_ifc(out)
