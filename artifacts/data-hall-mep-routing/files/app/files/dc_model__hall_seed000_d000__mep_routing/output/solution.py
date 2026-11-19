import sys, ifcopenshell, ifcopenshell.api

def create_ifc(output_path='output/model.ifc'):
    # Create a new IFC file with minimal required structure
    ifc = ifcopenshell.file(schema='IFC4')
    # Project
    project = ifc.create_entity('IfcProject', GlobalId=ifcopenshell.guid.new(), Name='Data Hall Project')
    ifc.add(project)
    # Units (millimetre)
    unit_assignment = ifc.create_entity('IfcUnitAssignment', Units=[
        ifc.create_entity('IfcSIUnit', UnitType='LENGTHUNIT', Name='METRE', Prefix='MILLI')
    ])
    project.UnitsInContext = unit_assignment
    # Site
    site = ifc.create_entity('IfcSite', GlobalId=ifcopenshell.guid.new(), Name='Site')
    # Building
    building = ifc.create_entity('IfcBuilding', GlobalId=ifcopenshell.guid.new(), Name='Data Hall')
    # Storey
    storey = ifc.create_entity('IfcBuildingStorey', GlobalId=ifcopenshell.guid.new(), Name='Level 0', Elevation=0.0)
    # Relate entities via aggregation relationships
    # Project contains Site
    rel_proj_site = ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=project, RelatedObjects=[site])
    # Site contains Building
    rel_site_building = ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=site, RelatedObjects=[building])
    # Building contains Storey
    rel_building_storey = ifc.create_entity('IfcRelAggregates', GlobalId=ifcopenshell.guid.new(), RelatingObject=building, RelatedObjects=[storey])
    # Write file
    ifc.write(output_path)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv)>1 else 'output/model.ifc'
    create_ifc(out)
