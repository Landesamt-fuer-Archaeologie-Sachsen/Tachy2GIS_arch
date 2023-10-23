<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="1" styleCategories="Symbology|Labeling" version="3.4.1-Madeira">
  <renderer-v2 forceraster="0" type="RuleRenderer" symbollevels="0" enableorderby="0">
    <rules key="{022b7cfe-823d-4bf9-b076-1312c6dc9cfc}">
      <rule symbol="0" key="{a3bf9834-9266-4b43-a0cd-c0504956d53d}"/>
    </rules>
    <symbols>
      <symbol alpha="1" clip_to_extent="1" type="line" name="0">
        <layer pass="0" class="MarkerLine" enabled="1" locked="0">
          <prop k="interval" v="3"/>
          <prop k="interval_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="interval_unit" v="MM"/>
          <prop k="offset" v="0"/>
          <prop k="offset_along_line" v="3"/>
          <prop k="offset_along_line_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_along_line_unit" v="MM"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="placement" v="lastvertex"/>
          <prop k="rotate" v="0"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
          <symbol alpha="1" clip_to_extent="1" type="marker" name="@0@0">
            <layer pass="0" class="SimpleMarker" enabled="1" locked="0">
              <prop k="angle" v="180"/>
              <prop k="color" v="255,0,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="triangle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2.8"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="0"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <labeling type="rule-based">
    <rules key="{e165d695-c504-47cd-a684-ec6657e6704b}">
      <rule key="{a2c1a36c-4f1b-41b2-abee-cb1ceaa3410f}">
        <settings>
          <text-style fontFamily="MS Shell Dlg 2" fieldName="round( z(   end_point( $geometry  )  ),2 )  " fontLetterSpacing="0" fontStrikeout="0" blendMode="0" textOpacity="1" isExpression="1" previewBkgrdColor="#ffffff" fontUnderline="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontSize="7" fontWordSpacing="0" fontWeight="50" namedStyle="Standard" multilineHeight="1" fontItalic="0" useSubstitutions="0" fontCapitals="0" textColor="0,0,0,255" fontSizeUnit="Point">
            <text-buffer bufferOpacity="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferDraw="0" bufferSizeUnits="MM" bufferBlendMode="0" bufferSize="1" bufferColor="255,255,255,255" bufferNoFill="1" bufferJoinStyle="128"/>
            <background shapeSizeX="0" shapeOffsetUnit="MM" shapeRotationType="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeRotation="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeSizeY="0" shapeBorderWidthUnit="MM" shapeOpacity="1" shapeOffsetY="0" shapeType="0" shapeSizeUnit="MM" shapeBorderColor="128,128,128,255" shapeRadiiUnit="MM" shapeBlendMode="0" shapeSizeType="0" shapeFillColor="3,154,8,255" shapeOffsetX="0" shapeDraw="0" shapeRadiiY="0" shapeRadiiX="0" shapeJoinStyle="64" shapeBorderWidth="0" shapeSVGFile="" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0"/>
            <shadow shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowRadiusAlphaOnly="0" shadowBlendMode="6" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetAngle="135" shadowRadius="1.5" shadowDraw="0" shadowColor="0,0,0,255" shadowOffsetUnit="MM" shadowOffsetGlobal="1" shadowRadiusUnit="MM" shadowOpacity="0.7" shadowUnder="0" shadowOffsetDist="1" shadowScale="100"/>
            <substitutions/>
          </text-style>
          <text-format wrapChar="" multilineAlign="4294967295" rightDirectionSymbol=">" formatNumbers="1" placeDirectionSymbol="0" addDirectionSymbol="0" plussign="0" decimals="2" reverseDirectionSymbol="0" autoWrapLength="0" leftDirectionSymbol="&lt;" useMaxLineLengthForAutoWrap="1"/>
          <placement distUnits="Point" offsetUnits="MM" distMapUnitScale="3x:0,0,0,0,0,0" centroidInside="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" offsetType="0" rotationAngle="0" placementFlags="3" placement="2" centroidWhole="0" xOffset="0" dist="0" priority="5" maxCurvedCharAngleIn="25" preserveRotation="1" fitInPolygonOnly="0" maxCurvedCharAngleOut="-25" repeatDistanceUnits="MM" repeatDistance="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" yOffset="0" quadOffset="4"/>
          <rendering zIndex="0" labelPerPart="0" fontLimitPixelSize="0" obstacleFactor="1" obstacleType="0" fontMinPixelSize="3" scaleVisibility="0" fontMaxPixelSize="10000" scaleMax="0" displayAll="1" mergeLines="0" obstacle="1" limitNumLabels="0" upsidedownLabels="2" maxNumLabels="2000" drawLabels="1" scaleMin="0" minFeatureSize="0"/>
          <dd_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="PositionX">
                  <Option value="true" type="bool" name="active"/>
                  <Option value="x ( end_point(  $geometry  )  )" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
                <Option type="Map" name="PositionY">
                  <Option value="true" type="bool" name="active"/>
                  <Option value="y(  end_point(  $geometry  )  )" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </dd_properties>
        </settings>
      </rule>
    </rules>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>1</layerGeometryType>
</qgis>
