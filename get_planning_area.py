import requests, sqlite3
import numpy as np

write_into_database = False
token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOjQwODIsInVzZXJfaWQiOjQwODIsImVtYWlsIjoiY2hlbmdndWFuLnRlb0BnbWFpbC5jb20iLCJmb3JldmVyIjpmYWxzZSwiaXNzIjoiaHR0cDpcL1wvb20yLmRmZS5vbmVtYXAuc2dcL2FwaVwvdjJcL3VzZXJcL3Nlc3Npb24iLCJpYXQiOjE1OTA4MzQxMTIsImV4cCI6MTU5MTI2NjExMiwibmJmIjoxNTkwODM0MTEyLCJqdGkiOiI2MTEwNmVlZDFjZmQ4NWQxYjc4MTY0ZDMwNTgwYWFjNiJ9.g_SJC6pXONfl2F2LVAZK3QMVIOuVYuOBNK0uDmvYiZg'

planning_year   = '2019'

if write_into_database:
    db_file_name    = 'master-plan.db'
    table_name      = 'planning-area-2019'

input_kml       = "./G_MP19_LAND_USE_PL.kml"
kml_file_name   = f'output_planning_area_{planning_year}.kml'

kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<!-- Copyright 2020 (C) by Teo Cheng Guan -->
<kml xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:atom="http://www.w3.org/2005/Atom" xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>G_MP19_LAND_USE_PL</name>
<visibility>1</visibility>
<Schema name="G_MP19_LAND_USE_PL" id="kml_schema_ft_G_MP19_LAND_USE_PL">
\t<SimpleField type="xsd:string" name="LU_DESC">
\t\t<displayName>LU_DESC</displayName>
\t</SimpleField>
\t<SimpleField type="xsd:string" name="NumOfPolygons">
\t\t<displayName>NumOfPolygons</displayName>
\t</SimpleField>
</Schema>
<Folder id="kml_ft_G_MP19_LAND_USE_PL">
<name>G_MP19_LAND_USE_PL</name>\n"""

kml_footer = """</Folder>
</Document></kml>"""

url = f'https://developers.onemap.sg/privateapi/popapi/getAllPlanningarea?token={token}&year={planning_year}'
resp = requests.get(url).json()

# Open output KML file
kml_file = open(kml_file_name, "w+")
kml_file.write(kml_header)

planning_polygons = []
Num_planning_area_counted = 0
max_polygon_in_planning_area = 0

if write_into_database:
    conn = sqlite3.connect(db_file_name)

for each in resp:
    if each['geojson'] != None:
        planning_area = each['pln_area_n']
        coordinates = eval(each['geojson'])['coordinates']

        #polygon = coordinates[0][0]
        polygons = []
        num_polygons_in_planning_area = len(coordinates)
        print(f'{planning_area}: {num_polygons_in_planning_area}')

        for each_cor in coordinates:
            dim = np.array(each_cor).ndim  
            print(f'  Dim: {dim}')              
            if dim == 3:
                polygons.append(each_cor[0])
                print(f'    polygons -> {len(polygons)}')

            elif dim == 1:
                for each_sub_cor in each_cor:
                    sub_dim = np.array(each_sub_cor).ndim
                    print(f'    sub_dim {sub_dim}') 
                    print(f'    len = {len(each_sub_cor)}')
                    if sub_dim == 2:
                        polygons.append(each_sub_cor)
                        print(f'      > polygons -> {len(polygons)}')
                    else:
                        print(f'      ONION DETECTED -> len of each_sub_cor {len(each_sub_cor)}')
            else:
                print(f'      ONION DETECTED -> dim = {dim}')
            #print(f'    polygons -> {len(polygons)}')
            #if planning_area == 'DOWNTOWN CORE':


        if num_polygons_in_planning_area > max_polygon_in_planning_area:
            max_polygon_in_planning_area = num_polygons_in_planning_area

        #print(eval(each['geojson'])['coordinates'][0][0])

        polygon_id = 0
        for each_polygon in polygons:
            polygon_str = ''
            for each_point in each_polygon:
                polygon_str += f'{each_point[0]},{each_point[1]},0.0 '
            #print(each_polygon)
            #break

            # Print the polygon in [lat, lon] format to be stored in the db
            db_polygon = []
            for each_coordinate in each_polygon:
                db_polygon.append([each_coordinate[1], each_coordinate[0]])

            if write_into_database:
                c = conn.cursor()
                sql_exp = f'INSERT into "{table_name}" (area_id, planning_area, Polygon) VALUES ("{planning_area}_{polygon_id}", "{planning_area}", "{db_polygon}") ;'
                c.execute(sql_exp)
                conn.commit()

            Num_planning_area_counted += 1
            kml_file.write(f'<Placemark id="{planning_area}_{polygon_id}">\n')
            kml_file.write(f'\t<name>{planning_area}_{polygon_id}</name>\n')

            kml_file.write('\t<ExtendedData>\n\t<SchemaData schemaUrl="#kml_schema_ft_G_MP19_LAND_USE_PL">\n')
            kml_file.write(f'\t\t<SimpleData name="LU_DESC">{planning_area}</SimpleData>\n')
            kml_file.write(f'\t\t<SimpleData name="NumOfPolygons">{num_polygons_in_planning_area}</SimpleData>\n')            
            kml_file.write('\t</SchemaData>\n\t</ExtendedData>\n')

            kml_file.write('\t<Polygon><outerBoundaryIs><LinearRing><coordinates>')
            kml_file.write(polygon_str)
            kml_file.write('</coordinates></LinearRing></outerBoundaryIs></Polygon>\n')     
            kml_file.write('</Placemark>\n')
            polygon_id += 1



print(Num_planning_area_counted) 
print(f'max_polygon_in_planning_area = {max_polygon_in_planning_area}')

kml_file.write(kml_footer)
kml_file.close()

if write_into_database:
    conn.close()



"""
{'id': 26, 'pln_area_n': 'SIMPANG'}, 
{'id': 27, 'pln_area_n': 'SOUTHERN ISLANDS'}, 
{'id': 28, 'pln_area_n': 'SUNGEI KADUT'}, 
{'id': 33, 'pln_area_n': 'TUAS'}, 
{'id': 34, 'pln_area_n': 'WESTERN ISLANDS'}, 
{'id': 35, 'pln_area_n': 'WESTERN WATER CATCHMENT'}, 
{'id': 38, 'pln_area_n': 'DOWNTOWN CORE'}, 
{'id': 42, 'pln_area_n': 'NEWTON'}, 
{'id': 43, 'pln_area_n': 'ORCHARD'}, 
{'id': 45, 'pln_area_n': 'KALLANG'}, 
{'id': 46, 'pln_area_n': 'LIM CHU KANG'}, 
{'id': 49, 'pln_area_n': 'NORTH-EASTERN ISLANDS'}, 
{'id': 51, 'pln_area_n': 'PASIR RIS'}, 
{'id': 56, 'pln_area_n': 'STRAITS VIEW'}, 
{'id': 39, 'pln_area_n': 'MARINA EAST'}, 
{'id': 40, 'pln_area_n': 'MARINA SOUTH'}, 
{'id': 31, 'pln_area_n': 'TENGAH'}, 
{'id': 25, 'pln_area_n': 'SERANGOON'}, 
{'id': 57, 'pln_area_n': 'OTHERS'}, 
{'id': 5, 'pln_area_n': 'BOON LAY'}, 
{'id': 3, 'pln_area_n': 'BEDOK'}, 
{'id': 7, 'pln_area_n': 'BUKIT MERAH'}, 
{'id': 8, 'pln_area_n': 'BUKIT PANJANG'}, 
{'id': 9, 'pln_area_n': 'JURONG EAST'}, 
{'id': 11, 'pln_area_n': 'BUKIT TIMAH'}, 
{'id': 12, 'pln_area_n': 'CENTRAL WATER CATCHMENT'}, 
{'id': 13, 'pln_area_n': 'CHANGI'}, 
{'id': 15, 'pln_area_n': 'CHOA CHU KANG'}, 
{'id': 21, 'pln_area_n': 'QUEENSTOWN'}, 
{'id': 22, 'pln_area_n': 'SELETAR'}, 
{'id': 47, 'pln_area_n': 'MANDAI'}, 
{'id': 2, 'pln_area_n': 'ANG MO KIO'}, 
{'id': 4, 'pln_area_n': 'BISHAN'}, 
{'id': 6, 'pln_area_n': 'BUKIT BATOK'}, 
{'id': 14, 'pln_area_n': 'CHANGI BAY'}, 
{'id': 10, 'pln_area_n': 'JURONG WEST'}, 
{'id': 16, 'pln_area_n': 'CLEMENTI'}, 
{'id': 17, 'pln_area_n': 'GEYLANG'}, 
{'id': 18, 'pln_area_n': 'HOUGANG'}, 
{'id': 19, 'pln_area_n': 'PIONEER'}, 
{'id': 20, 'pln_area_n': 'PUNGGOL'}, 
{'id': 23, 'pln_area_n': 'SEMBAWANG'}, 
{'id': 24, 'pln_area_n': 'SENGKANG'}, 
{'id': 29, 'pln_area_n': 'TAMPINES'}, 
{'id': 30, 'pln_area_n': 'TANGLIN'}, 
{'id': 32, 'pln_area_n': 'TOA PAYOH'}, 
{'id': 36, 'pln_area_n': 'WOODLANDS'}, 
{'id': 37, 'pln_area_n': 'YISHUN'}, 
{'id': 41, 'pln_area_n': 'MUSEUM'}, 
{'id': 44, 'pln_area_n': 'OUTRAM'}, 
{'id': 48, 'pln_area_n': 'MARINE PARADE'}, 
{'id': 50, 'pln_area_n': 'NOVENA'}, 
{'id': 52, 'pln_area_n': 'PAYA LEBAR'}, 
{'id': 53, 'pln_area_n': 'RIVER VALLEY'}, 
{'id': 54, 'pln_area_n': 'ROCHOR'}, 
{'id': 55, 'pln_area_n': 'SINGAPORE RIVER'}    
"""
