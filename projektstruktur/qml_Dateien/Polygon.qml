<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis simplifyAlgorithm="0" simplifyLocal="1" minScale="1e+08" version="3.4.1-Madeira" labelsEnabled="0" readOnly="0" hasScaleBasedVisibilityFlag="0" simplifyDrawingTol="1" simplifyDrawingHints="1" maxScale="0" simplifyMaxScale="1" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <renderer-v2 forceraster="0" symbollevels="0" enableorderby="0" type="singleSymbol">
    <symbols>
      <symbol alpha="1" clip_to_extent="1" type="fill" name="0">
        <layer enabled="1" class="SimpleFill" locked="0" pass="0">
          <prop v="3x:0,0,0,0,0,0" k="border_width_map_unit_scale"/>
          <prop v="150,150,150,255" k="color"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="150,150,150,255" k="outline_color"/>
          <prop v="dash" k="outline_style"/>
          <prop v="0.3" k="outline_width"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="no" k="style"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <customproperties>
    <property value="id" key="dualview/previewExpressions"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property key="variableNames"/>
    <property key="variableValues"/>
  </customproperties>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerOpacity>1</layerOpacity>
  <SingleCategoryDiagramRenderer attributeLegend="1" diagramType="Histogram">
    <DiagramCategory penAlpha="255" scaleBasedVisibility="0" height="15" minimumSize="0" opacity="1" backgroundAlpha="255" penColor="#000000" lineSizeScale="3x:0,0,0,0,0,0" sizeScale="3x:0,0,0,0,0,0" enabled="0" minScaleDenominator="0" scaleDependency="Area" lineSizeType="MM" maxScaleDenominator="1e+08" labelPlacementMethod="XHeight" rotationOffset="270" penWidth="0" diagramOrientation="Up" width="15" backgroundColor="#ffffff" sizeType="MM" barWidth="5">
      <fontProperties style="" description="MS Shell Dlg 2,7.8,-1,5,50,0,0,0,0,0"/>
      <attribute field="" color="#000000" label=""/>
    </DiagramCategory>
  </SingleCategoryDiagramRenderer>
  <DiagramLayerSettings priority="0" dist="0" placement="1" obstacle="0" showAll="1" linePlacementFlags="18" zIndex="0">
    <properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </properties>
  </DiagramLayerSettings>
  <geometryOptions removeDuplicateNodes="0" geometryPrecision="0">
    <activeChecks/>
    <checkConfiguration/>
  </geometryOptions>
  <fieldConfiguration>
    <field name="id">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="messdatum">
      <editWidget type="DateTime">
        <config>
          <Option type="Map">
            <Option value="true" type="bool" name="allow_null"/>
            <Option value="false" type="bool" name="calendar_popup"/>
            <Option value="yyyy-MM-dd" type="QString" name="display_format"/>
            <Option value="yyyy-MM-dd" type="QString" name="field_format"/>
            <Option value="false" type="bool" name="field_iso_format"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="aktcode">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="obj_type">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="AllowMulti"/>
            <Option value="true" type="bool" name="AllowNull"/>
            <Option value=" &quot;Field4&quot;  = 1" type="QString" name="FilterExpression"/>
            <Option value="Field2" type="QString" name="Key"/>
            <Option value="Auswahllisten_2_Objekttype_li_c2d201cc_63de_4806_9146_f13426828304" type="QString" name="Layer"/>
            <Option value="1" type="int" name="NofColumns"/>
            <Option value="true" type="bool" name="OrderByValue"/>
            <Option value="false" type="bool" name="UseCompleter"/>
            <Option value="Field2" type="QString" name="Value"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="obj_art">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="AllowMulti"/>
            <Option value="true" type="bool" name="AllowNull"/>
            <Option value="regexp_match(  &quot;Field5&quot; , current_value( 'obj_type' )) > 0 and&#xa;    (&quot;Field4&quot;  =  1)" type="QString" name="FilterExpression"/>
            <Option value="Field3" type="QString" name="Key"/>
            <Option value="Auswahllisten_2_1_Objektart_li_cfb3b472_5fbc_4d07_bbbd_1f6aca779ea9" type="QString" name="Layer"/>
            <Option value="1" type="int" name="NofColumns"/>
            <Option value="true" type="bool" name="OrderByValue"/>
            <Option value="false" type="bool" name="UseCompleter"/>
            <Option value="Field3" type="QString" name="Value"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="schnitt_nr">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="planum">
      <editWidget type="TextEdit">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="IsMultiline"/>
            <Option value="false" type="bool" name="UseHtml"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="material">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="AllowMulti"/>
            <Option value="true" type="bool" name="AllowNull"/>
            <Option value=" &quot;Field3&quot;  =  current_value( 'obj_type')" type="QString" name="FilterExpression"/>
            <Option value="Field1" type="QString" name="Key"/>
            <Option value="Auswahllisten_3_Material_2a99b026_6dd9_470d_bc5d_412210e3b553" type="QString" name="Layer"/>
            <Option value="1" type="int" name="NofColumns"/>
            <Option value="false" type="bool" name="OrderByValue"/>
            <Option value="false" type="bool" name="UseCompleter"/>
            <Option value="Field1" type="QString" name="Value"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bemerkung">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
    <field name="geo_arch">
      <editWidget type="ValueRelation">
        <config>
          <Option type="Map">
            <Option value="false" type="bool" name="AllowMulti"/>
            <Option value="true" type="bool" name="AllowNull"/>
            <Option value="" type="QString" name="FilterExpression"/>
            <Option value="Field1" type="QString" name="Key"/>
            <Option value="Auswahllisten_4_geo_arch_35826565_69d8_441e_87c6_5d1f5db6ab86" type="QString" name="Layer"/>
            <Option value="1" type="int" name="NofColumns"/>
            <Option value="false" type="bool" name="OrderByValue"/>
            <Option value="false" type="bool" name="UseCompleter"/>
            <Option value="Field2" type="QString" name="Value"/>
          </Option>
        </config>
      </editWidget>
    </field>
    <field name="bef_nr">
      <editWidget type="TextEdit">
        <config>
          <Option/>
        </config>
      </editWidget>
    </field>
  </fieldConfiguration>
  <aliases>
    <alias field="id" index="0" name=""/>
    <alias field="messdatum" index="1" name="Aufnamedatum"/>
    <alias field="aktcode" index="2" name="Grabung"/>
    <alias field="obj_type" index="3" name="Objekttyp"/>
    <alias field="obj_art" index="4" name="Objektart"/>
    <alias field="schnitt_nr" index="5" name="Schnitt Nr"/>
    <alias field="planum" index="6" name="Planum"/>
    <alias field="material" index="7" name="Material"/>
    <alias field="bemerkung" index="8" name=""/>
    <alias field="geo_arch" index="9" name="Geologie/Archäologie"/>
    <alias field="bef_nr" index="10" name=""/>
  </aliases>
  <excludeAttributesWMS/>
  <excludeAttributesWFS/>
  <defaults>
    <default field="id" applyOnUpdate="0" expression=" if (count( &quot;id&quot; )= 0 , 0, maximum( &quot;id&quot;)+1)"/>
    <default field="messdatum" applyOnUpdate="0" expression=" now( )"/>
    <default field="aktcode" applyOnUpdate="0" expression=" @aktcode "/>
    <default field="obj_type" applyOnUpdate="0" expression=""/>
    <default field="obj_art" applyOnUpdate="0" expression=""/>
    <default field="schnitt_nr" applyOnUpdate="0" expression=""/>
    <default field="planum" applyOnUpdate="0" expression=""/>
    <default field="material" applyOnUpdate="0" expression=""/>
    <default field="bemerkung" applyOnUpdate="0" expression=""/>
    <default field="geo_arch" applyOnUpdate="0" expression=" @arch_geo "/>
    <default field="bef_nr" applyOnUpdate="0" expression=""/>
  </defaults>
  <constraints>
    <constraint field="id" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="messdatum" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="aktcode" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="obj_type" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="obj_art" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="schnitt_nr" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="planum" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="material" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="bemerkung" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="geo_arch" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
    <constraint field="bef_nr" unique_strength="0" exp_strength="0" notnull_strength="0" constraints="0"/>
  </constraints>
  <constraintExpressions>
    <constraint exp="" field="id" desc=""/>
    <constraint exp="" field="messdatum" desc=""/>
    <constraint exp="" field="aktcode" desc=""/>
    <constraint exp="" field="obj_type" desc=""/>
    <constraint exp="" field="obj_art" desc=""/>
    <constraint exp="" field="schnitt_nr" desc=""/>
    <constraint exp="" field="planum" desc=""/>
    <constraint exp="" field="material" desc=""/>
    <constraint exp="" field="bemerkung" desc=""/>
    <constraint exp="" field="geo_arch" desc=""/>
    <constraint exp="" field="bef_nr" desc=""/>
  </constraintExpressions>
  <expressionfields/>
  <attributeactions>
    <defaultAction value="{00000000-0000-0000-0000-000000000000}" key="Canvas"/>
  </attributeactions>
  <attributetableconfig actionWidgetStyle="dropDown" sortOrder="0" sortExpression="">
    <columns>
      <column width="-1" hidden="0" type="field" name="id"/>
      <column width="-1" hidden="0" type="field" name="messdatum"/>
      <column width="-1" hidden="0" type="field" name="aktcode"/>
      <column width="-1" hidden="1" type="actions"/>
      <column width="-1" hidden="0" type="field" name="obj_type"/>
      <column width="-1" hidden="0" type="field" name="schnitt_nr"/>
      <column width="-1" hidden="0" type="field" name="planum"/>
      <column width="-1" hidden="0" type="field" name="material"/>
      <column width="-1" hidden="0" type="field" name="bemerkung"/>
      <column width="-1" hidden="0" type="field" name="bef_nr"/>
      <column width="-1" hidden="0" type="field" name="obj_art"/>
      <column width="-1" hidden="0" type="field" name="geo_arch"/>
    </columns>
  </attributetableconfig>
  <conditionalstyles>
    <rowstyles/>
    <fieldstyles/>
  </conditionalstyles>
  <editform tolerant="1"></editform>
  <editforminit/>
  <editforminitcodesource>0</editforminitcodesource>
  <editforminitfilepath></editforminitfilepath>
  <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from qgis.PyQt.QtWidgets import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
  <featformsuppress>0</featformsuppress>
  <editorlayout>generatedlayout</editorlayout>
  <editable>
    <field editable="1" name="aktcode"/>
    <field editable="1" name="bef_nr"/>
    <field editable="1" name="bemerkung"/>
    <field editable="1" name="fund_nr"/>
    <field editable="1" name="geo-arch"/>
    <field editable="1" name="geo_arch"/>
    <field editable="0" name="id"/>
    <field editable="1" name="material"/>
    <field editable="1" name="messdatum"/>
    <field editable="1" name="obj_art"/>
    <field editable="1" name="obj_type"/>
    <field editable="1" name="opj_art"/>
    <field editable="1" name="planum"/>
    <field editable="1" name="schnitt_nr"/>
  </editable>
  <labelOnTop>
    <field labelOnTop="0" name="aktcode"/>
    <field labelOnTop="0" name="bef_nr"/>
    <field labelOnTop="0" name="bemerkung"/>
    <field labelOnTop="0" name="fund_nr"/>
    <field labelOnTop="0" name="geo-arch"/>
    <field labelOnTop="0" name="geo_arch"/>
    <field labelOnTop="0" name="id"/>
    <field labelOnTop="0" name="material"/>
    <field labelOnTop="0" name="messdatum"/>
    <field labelOnTop="0" name="obj_art"/>
    <field labelOnTop="0" name="obj_type"/>
    <field labelOnTop="0" name="opj_art"/>
    <field labelOnTop="0" name="planum"/>
    <field labelOnTop="0" name="schnitt_nr"/>
  </labelOnTop>
  <widgets/>
  <previewExpression>id</previewExpression>
  <mapTip></mapTip>
  <layerGeometryType>2</layerGeometryType>
</qgis>
